from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from typing import List, Union, Optional
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 batch_size: int = 32, device: str = "cpu", normalize_embeddings: bool = True):
        """
        Initialize the embedder with sentence-transformers.
        
        Args:
            model_name: Name of the sentence-transformers model
            batch_size: Batch size for embedding multiple texts
            device: Device to run embeddings on ('cpu' or 'cuda')
            normalize_embeddings: Whether to normalize embeddings to unit length
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device if torch.cuda.is_available() and device == "cuda" else "cpu"
        self.normalize_embeddings = normalize_embeddings
        
        # Initialize model
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        logger.info(f"Initializing embedder with model: {model_name} on device: {self.device}")
        self._load_model()
    
    def _load_model(self):
        """Load the sentence-transformers model."""
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Successfully loaded model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {str(e)}")
            raise
    
    def embed_texts(self, texts: List[str], show_progress: bool = False) -> List[List[float]]:
        """
        Embed a list of texts.
        
        Args:
            texts: List of text strings to embed
            show_progress: Whether to show progress bar
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        if not valid_texts:
            return []
        
        try:
            # Embed in batches
            embeddings = self.model.encode(
                valid_texts,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )
            
            # Convert to list of lists
            embedding_list = embeddings.tolist()
            
            logger.info(f"Successfully embedded {len(valid_texts)} texts")
            return embedding_list
            
        except Exception as e:
            logger.error(f"Error embedding texts: {str(e)}")
            raise
    
    def embed_query(self, query: str) -> List[float]:
        """
        Embed a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        if not query or not query.strip():
            return []
        
        try:
            embedding = self.model.encode(
                query,
                normalize_embeddings=self.normalize_embeddings,
                convert_to_numpy=True
            )
            
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise
    
    async def embed_texts_async(self, texts: List[str]) -> List[List[float]]:
        """
        Asynchronously embed a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        loop = asyncio.get_event_loop()
        
        # Run embedding in thread pool
        embeddings = await loop.run_in_executor(
            self.executor, 
            self.embed_texts, 
            texts
        )
        
        return embeddings
    
    async def embed_query_async(self, query: str) -> List[float]:
        """
        Asynchronously embed a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            Embedding vector
        """
        loop = asyncio.get_event_loop()
        
        # Run embedding in thread pool
        embedding = await loop.run_in_executor(
            self.executor, 
            self.embed_query, 
            query
        )
        
        return embedding
    
    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        try:
            # Convert to numpy arrays
            emb1 = np.array(embedding1)
            emb2 = np.array(embedding2)
            
            # Compute cosine similarity
            similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error computing similarity: {str(e)}")
            return 0.0
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        if self.model is None:
            return 0
        
        try:
            # Get dimension by embedding a dummy text
            dummy_embedding = self.embed_query("test")
            return len(dummy_embedding)
        except:
            return 0
    
    def batch_embed_with_metadata(self, texts_with_metadata: List[tuple]) -> List[dict]:
        """
        Embed texts along with their metadata.
        
        Args:
            texts_with_metadata: List of (text, metadata) tuples
            
        Returns:
            List of dictionaries with embeddings and metadata
        """
        if not texts_with_metadata:
            return []
        
        # Extract texts
        texts = [item[0] for item in texts_with_metadata]
        
        # Embed texts
        embeddings = self.embed_texts(texts)
        
        # Combine with metadata
        results = []
        for i, (text, metadata) in enumerate(texts_with_metadata):
            result = {
                'text': text,
                'embedding': embeddings[i] if i < len(embeddings) else [],
                'metadata': metadata
            }
            results.append(result)
        
        return results
    
    def is_model_loaded(self) -> bool:
        """Check if the model is loaded and ready."""
        return self.model is not None
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        if not self.is_model_loaded():
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'model_name': self.model_name,
            'device': self.device,
            'embedding_dimension': self.get_embedding_dimension(),
            'max_seq_length': getattr(self.model, 'max_seq_length', 'unknown'),
            'normalize_embeddings': self.normalize_embeddings,
            'batch_size': self.batch_size
        }
    
    def __del__(self):
        """Cleanup when the embedder is destroyed."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
