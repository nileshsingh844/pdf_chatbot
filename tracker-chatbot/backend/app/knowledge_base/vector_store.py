import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions
import uuid
from typing import List, Dict, Any, Optional, Tuple
import logging
import json
import time

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_db", 
                 collection_name: str = "pdf_documents"):
        """
        Initialize ChromaDB vector store.
        
        Args:
            persist_directory: Directory to persist the database
            collection_name: Name of the collection to use
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        self.client = None
        self.collection = None
        
        logger.info(f"Initializing vector store with persist directory: {persist_directory}")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client and get/create collection."""
        try:
            # Create persistent client
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Connected to existing collection: {self.collection_name}")
            except Exception:
                # Collection doesn't exist, create it
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "PDF document chunks"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
        
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of documents with 'content', 'embedding', and 'metadata'
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        try:
            # Prepare data for ChromaDB
            ids = []
            embeddings = []
            documents_text = []
            metadatas = []
            
            for doc in documents:
                # Generate unique ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
                
                # Get embedding
                embedding = doc.get('embedding', [])
                if not embedding:
                    logger.warning(f"Document {doc_id} has no embedding, skipping")
                    continue
                embeddings.append(embedding)
                
                # Get content
                content = doc.get('content', '')
                documents_text.append(content)
                
                # Get metadata
                metadata = doc.get('metadata', {})
                # Ensure metadata is serializable
                serializable_metadata = self._make_serializable(metadata)
                metadatas.append(serializable_metadata)
            
            if not embeddings:
                logger.warning("No valid documents to add")
                return []
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents_text,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(ids)} documents to vector store")
            return ids
        
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise
    
    def query(self, query_embedding: List[float], 
              top_k: int = 8, 
              where: Optional[Dict[str, Any]] = None,
              where_document: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_embedding: Embedding of the query
            top_k: Number of results to return
            where: Metadata filter conditions
            where_document: Document content filter conditions
            
        Returns:
            List of search results with scores and metadata
        """
        if not query_embedding:
            return []
        
        try:
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where,
                where_document=where_document,
                include=['metadatas', 'documents', 'distances', 'uris']
            )
            
            # Format results
            formatted_results = []
            if results['ids'] and results['ids'][0]:
                for i in range(len(results['ids'][0])):
                    result = {
                        'id': results['ids'][0][i],
                        'content': results['documents'][0][i] if results['documents'] else '',
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'score': 1 - results['distances'][0][i] if results['distances'] else 0.0,  # Convert distance to similarity
                        'uri': results['uris'][0][i] if results['uris'] else None
                    }
                    formatted_results.append(result)
            
            logger.info(f"Query returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {str(e)}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document data or None if not found
        """
        try:
            results = self.collection.get(
                ids=[doc_id],
                include=['metadatas', 'documents']
            )
            
            if results['ids'] and results['ids'][0]:
                return {
                    'id': results['ids'][0],
                    'content': results['documents'][0] if results['documents'] else '',
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {str(e)}")
            return None
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents from the vector store.
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not doc_ids:
            return True
        
        try:
            self.collection.delete(ids=doc_ids)
            logger.info(f"Successfully deleted {len(doc_ids)} documents")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "PDF document chunks"}
            )
            logger.info("Successfully cleared collection")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            
            return {
                'collection_name': self.collection_name,
                'document_count': count,
                'persist_directory': self.persist_directory,
                'client_type': 'persistent',
                'last_updated': time.time()
            }
            
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {}
    
    def list_collections(self) -> List[str]:
        """
        List all available collections.
        
        Returns:
            List of collection names
        """
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
            
        except Exception as e:
            logger.error(f"Error listing collections: {str(e)}")
            return []
    
    def _make_serializable(self, obj: Any) -> Any:
        """
        Convert object to JSON-serializable format.
        
        Args:
            obj: Object to serialize
            
        Returns:
            JSON-serializable object
        """
        if isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {key: self._make_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, tuple):
            return tuple(self._make_serializable(item) for item in obj)
        else:
            # Convert other types to string
            return str(obj)
    
    def is_healthy(self) -> bool:
        """
        Check if the vector store is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get collection count
            self.collection.count()
            return True
        except Exception:
            return False
    
    def backup_collection(self, backup_path: str) -> bool:
        """
        Backup the collection to a specified path.
        
        Args:
            backup_path: Path to backup the collection
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This is a simplified backup - in production you might want more sophisticated backup
            import shutil
            shutil.copytree(self.persist_directory, backup_path, dirs_exist_ok=True)
            logger.info(f"Successfully backed up collection to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up collection: {str(e)}")
            return False
