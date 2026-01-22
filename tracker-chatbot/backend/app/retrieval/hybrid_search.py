from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
import re
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class HybridSearcher:
    def __init__(self, vector_store, embedder, alpha: float = 0.5, rrf_k: int = 60):
        """
        Hybrid searcher combines:
        - Dense search (Chroma vector similarity)
        - Sparse search (BM25)
        """
        self.vector_store = vector_store
        self.embedder = embedder
        self.alpha = alpha
        self.rrf_k = rrf_k

        self.bm25_index = None
        self.documents = []         # BM25 docs
        self.doc_id_to_index = {}   # doc_id -> index

        logger.info(f"Initialized hybrid searcher with alpha={alpha}, rrf_k={rrf_k}")

    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        IMPORTANT:
        This should ONLY build BM25 index.
        It must NOT call vector_store.add_documents() because upload pipeline already does it,
        and calling it again causes duplicate docs in Chroma.
        """
        if not documents:
            return True

        try:
            self.documents = []
            self.doc_id_to_index = {}

            tokenized_docs = []

            for i, doc in enumerate(documents):
                content = doc.get("content", "") or ""
                metadata = doc.get("metadata", {}) or {}

                # Create a stable local id for BM25 indexing
                doc_id = doc.get("id") or metadata.get("document_id") or f"bm25_{i}"

                tokens = self._tokenize_text(content)
                tokenized_docs.append(tokens)

                self.documents.append({
                    "id": doc_id,
                    "content": content,
                    "metadata": metadata,
                    "tokens": tokens
                })
                self.doc_id_to_index[doc_id] = len(self.documents) - 1

            if tokenized_docs:
                self.bm25_index = BM25Okapi(tokenized_docs)
                logger.info(f"BM25 indexed {len(self.documents)} documents")

            return True

        except Exception as e:
            logger.error(f"Error indexing documents for BM25: {str(e)}", exc_info=True)
            return False

    def search(self, query: str, top_k: int = 8, threshold: float = None) -> List[Dict[str, Any]]:
        """
        Hybrid search (RRF fusion).
        NOTE: threshold must be small because RRF scores are small (~0.01).
        """
        # Use config threshold if not provided
        if threshold is None:
            from ..config import settings
            threshold = settings.retrieval.threshold
            
        logger.info(f"Using threshold: {threshold}")
        
        if not query or not self.documents:
            logger.warning(f"Empty query or no documents. Query: '{query}', Docs count: {len(self.documents)}")
            return []

        try:
            dense_results = self._dense_search(query, top_k * 2)
            sparse_results = self._sparse_search(query, top_k * 2)
            
            logger.info(f"Dense results: {len(dense_results)}, Sparse results: {len(sparse_results)}")

            fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results)
            logger.info(f"Fused results: {len(fused_results)}")

            # Debug: Show scores before filtering
            for i, r in enumerate(fused_results[:5]):
                logger.info(f"Result {i}: score={r.get('combined_score', 0.0):.6f}")

            filtered = [r for r in fused_results if r.get("combined_score", 0.0) >= threshold]
            logger.info(f"After threshold filtering ({threshold}): {len(filtered)} results")
            
            final_results = filtered[:top_k]
            logger.info(f"Final results (top_k={top_k}): {len(final_results)}")
            
            return final_results

        except Exception as e:
            logger.error(f"Error in hybrid search: {str(e)}", exc_info=True)
            return []

    def _dense_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Dense vector similarity search using Chroma."""
        try:
            # FIX: your Embedder does not have embed_query()
            query_embedding = self.embedder.embed_query(query)

            if query_embedding is None or len(query_embedding) == 0:
                return []

            results = self.vector_store.query(query_embedding, top_k)

            for rank, r in enumerate(results):
                r["dense_rank"] = rank + 1
                r["dense_score"] = r.get("score", 0.0)

            return results

        except Exception as e:
            logger.error(f"Error in dense search: {str(e)}", exc_info=True)
            return []

    def _sparse_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Sparse BM25 search."""
        if not self.bm25_index:
            return []

        try:
            query_tokens = self._tokenize_text(query)
            bm25_scores = self.bm25_index.get_scores(query_tokens)

            results = []
            for idx, score in enumerate(bm25_scores):
                if score > 0:
                    doc = self.documents[idx]
                    results.append({
                        "id": doc["id"],
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "sparse_score": float(score),
                        "sparse_rank": None
                    })

            results.sort(key=lambda x: x["sparse_score"], reverse=True)

            for rank, r in enumerate(results[:top_k]):
                r["sparse_rank"] = rank + 1

            return results[:top_k]

        except Exception as e:
            logger.error(f"Error in sparse search: {str(e)}", exc_info=True)
            return []

    def _reciprocal_rank_fusion(self, dense_results: List[Dict[str, Any]],
                                sparse_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """RRF fusion of dense + sparse results."""
        doc_scores = defaultdict(float)
        doc_data = {}

        for r in dense_results:
            doc_id = r["id"]
            rank = r.get("dense_rank", 999999)
            score = 1.0 / (self.rrf_k + rank)
            doc_scores[doc_id] += self.alpha * score
            doc_data[doc_id] = r

        for r in sparse_results:
            doc_id = r["id"]
            rank = r.get("sparse_rank", None)
            if rank is not None:
                score = 1.0 / (self.rrf_k + rank)
                doc_scores[doc_id] += (1.0 - self.alpha) * score
                doc_data[doc_id] = r

        final = []
        for doc_id, combined_score in doc_scores.items():
            base = doc_data[doc_id].copy()
            base["combined_score"] = float(combined_score)
            final.append(base)

        final.sort(key=lambda x: x["combined_score"], reverse=True)
        return final

    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text for BM25."""
        if not text:
            return []
        text = text.lower()
        tokens = re.findall(r"\b\w+\b", text)
        return [t for t in tokens if len(t) >= 2]

    def get_search_stats(self) -> Dict[str, Any]:
        return {
            "indexed_documents": len(self.documents),
            "bm25_index_created": self.bm25_index is not None,
            "alpha": self.alpha,
            "rrf_k": self.rrf_k,
            "vector_store_stats": self.vector_store.get_stats()
        }

    def clear_index(self):
        self.documents = []
        self.doc_id_to_index = {}
        self.bm25_index = None
        self.vector_store.clear_collection()
        logger.info("Cleared hybrid search index")
