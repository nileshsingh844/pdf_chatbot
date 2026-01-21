from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Any, Optional
import re
from dataclasses import dataclass
import logging
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    content: str
    page_number: int
    chunk_id: str
    metadata: Dict[str, Any]
    category: str = "general"


class SemanticChunker:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 150, min_size: int = 50):
        # Parameter validation
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if min_size < 0:
            raise ValueError("min_size must be non-negative")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
            
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_size = min_size
        
        # Initialize LangChain text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Triple newlines (major sections)
                "\n\n",    # Double newlines (sections)
                "\n",      # Single newlines (paragraphs)
                ". ",      # Sentence followed by space
                "? ",      # Question followed by space
                "! ",      # Exclamation followed by space
                "; ",      # Semicolon followed by space
                ", ",      # Comma followed by space
                " ",       # Space (words)
                ""         # Character level
            ]
        )
        
        # Category keywords for semantic classification
        self.category_keywords = {
            "hardware": [
                "voltage", "current", "power", "watt", "amp", "ohm", "resistance",
                "circuit", "board", "chip", "processor", "memory", "storage",
                "sensor", "actuator", "motor", "battery", "connector", "cable",
                "pin", "gpio", "uart", "spi", "i2c", "pcb", "solder", "wiring"
            ],
            "communication": [
                "gps", "wifi", "bluetooth", "lora", "radio", "antenna", "signal",
                "transmission", "reception", "protocol", "network", "ethernet",
                "tcp", "udp", "http", "mqtt", "modbus", "can", "rs485", "serial"
            ],
            "power": [
                "battery", "solar", "charging", "consumption", "efficiency",
                "regulator", "converter", "inverter", "ups", "backup", "supply"
            ],
            "software": [
                "firmware", "algorithm", "code", "programming", "software",
                "application", "driver", "library", "api", "function", "variable",
                "class", "method", "debug", "compile", "install", "configure"
            ],
            "commands": [
                "command", "instruction", "syntax", "parameter", "argument",
                "option", "flag", "execute", "run", "start", "stop", "restart",
                "configure", "setup", "install", "update", "upgrade"
            ]
        }
    
    def chunk_document(self, pdf_content) -> List[DocumentChunk]:
        """Chunk PDF content into semantic segments."""
        chunks = []
        
        # Validate input
        if not pdf_content:
            logger.error("pdf_content is None or empty")
            return chunks
            
        # Safe attribute access with validation
        if not hasattr(pdf_content, 'pages') or not pdf_content.pages:
            logger.error("pdf_content.pages is missing or empty")
            return chunks
            
        # Generate unique document ID for chunk ID uniqueness
        doc_id = hashlib.md5(str(id(pdf_content)).encode()).hexdigest()[:8]
        logger.info(f"Processing document {doc_id} with {len(pdf_content.pages)} pages")
        
        try:
            # Process each page separately to maintain page context
            for page_info in pdf_content.pages:
                if not isinstance(page_info, dict):
                    logger.warning(f"Skipping invalid page_info: {type(page_info)}")
                    continue
                    
                # Safe page text extraction
                page_text = page_info.get('text', '').strip()
                page_number = page_info.get('page_number', 0)
                
                if not page_text:
                    logger.debug(f"Skipping empty page {page_number}")
                    continue
                
                # Split page text into chunks
                page_chunks = self.text_splitter.split_text(page_text)
                logger.debug(f"Page {page_number}: split into {len(page_chunks)} chunks")
                
                for i, chunk_text in enumerate(page_chunks):
                    if not chunk_text.strip():
                        continue
                    
                    # Ensure minimum chunk size
                    if len(chunk_text.strip()) < self.min_size:
                        continue
                    
                    # Create unique chunk ID with document identifier
                    chunk_id = f"{doc_id}_page_{page_number}_chunk_{i+1}"
                    
                    # Categorize chunk (can return multiple categories)
                    categories = self._categorize_chunk(chunk_text)
                    primary_category = categories[0] if categories else "general"
                    
                    # Safe metadata extraction
                    metadata = {
                        'page_number': page_number,
                        'chunk_index': i + 1,
                        'total_chunks_on_page': len(page_chunks),
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split()),
                        'category': primary_category,
                        'all_categories': ', '.join(categories) if categories else '',  # Convert list to string
                        'document_id': doc_id
                    }
                    
                    # Add source metadata safely
                    if hasattr(pdf_content, 'metadata') and pdf_content.metadata:
                        metadata.update({
                            'source': getattr(pdf_content.metadata, 'get', lambda x, y: y)('title', 'Unknown'),
                            'author': getattr(pdf_content.metadata, 'get', lambda x, y: y)('author', 'Unknown')
                        })
                    else:
                        metadata.update({
                            'source': 'Unknown',
                            'author': 'Unknown'
                        })
                    
                    # Create document chunk
                    chunk = DocumentChunk(
                        content=chunk_text.strip(),
                        page_number=page_number,
                        chunk_id=chunk_id,
                        metadata=metadata,
                        category=primary_category
                    )
                    
                    chunks.append(chunk)
            
            # Apply small chunk merging if needed
            if len(chunks) > 1000:  # Memory protection for large documents
                logger.warning(f"Large document detected ({len(chunks)} chunks), applying merging")
                chunks = self.merge_small_chunks(chunks)
            
            logger.info(f"Created {len(chunks)} chunks from document")
            return chunks
            
        except Exception as e:
            logger.error(f"Error chunking document: {str(e)}")
            return chunks
    
    def _categorize_chunk(self, text: str) -> List[str]:
        """Categorize chunk based on keyword matching. Returns sorted list of categories."""
        text_lower = text.lower()
        category_scores = {}
        
        # Score each category based on keyword matches
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            category_scores[category] = score
        
        # Sort categories by score (highest first) and filter out zero scores
        sorted_categories = [
            cat for cat, score in sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
            if score > 0
        ]
        
        # Return all categories with scores, or just "general" if none found
        return sorted_categories if sorted_categories else ["general"]
    
    def get_chunk_stats(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Get statistics about the chunks."""
        if not chunks:
            return {}
        
        stats = {
            'total_chunks': len(chunks),
            'total_characters': sum(len(chunk.content) for chunk in chunks),
            'total_words': sum(len(chunk.content.split()) for chunk in chunks),
            'avg_chunk_size': sum(len(chunk.content) for chunk in chunks) / len(chunks),
            'categories': {},
            'page_distribution': {}
        }
        
        # Category distribution
        for chunk in chunks:
            category = chunk.category
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
        
        # Page distribution
        for chunk in chunks:
            page = chunk.page_number
            stats['page_distribution'][page] = stats['page_distribution'].get(page, 0) + 1
        
        return stats
    
    def merge_small_chunks(self, chunks: List[DocumentChunk], min_size: int = 200) -> List[DocumentChunk]:
        """Merge chunks that are too small with adjacent chunks on the same page."""
        if not chunks:
            return chunks
        
        merged_chunks = []
        current_chunk = None
        
        for chunk in chunks:
            if len(chunk.content) < min_size:
                # Small chunk, try to merge with previous if same page
                if current_chunk is None:
                    current_chunk = chunk
                elif current_chunk.page_number == chunk.page_number:
                    # Merge with current chunk (same page only)
                    current_chunk.content += " " + chunk.content
                    
                    # Update metadata properly
                    current_chunk.metadata['merged_chunks'] = current_chunk.metadata.get('merged_chunks', 0) + 1
                    current_chunk.metadata['char_count'] = len(current_chunk.content)
                    current_chunk.metadata['word_count'] = len(current_chunk.content.split())
                    current_chunk.metadata['chunk_index'] = current_chunk.metadata.get('chunk_index', 1)
                    
                    # Update chunk ID to reflect merge
                    current_chunk.chunk_id += f"_merged_{chunk.chunk_id}"
                    
                    # Merge categories
                    if hasattr(chunk, 'all_categories') and chunk.all_categories:
                        current_categories_str = current_chunk.metadata.get('all_categories', current_chunk.category)
                        # Convert to list for merging, then back to string
                        current_categories_list = current_categories_str.split(', ') if isinstance(current_categories_str, str) else [current_categories_str]
                        
                        chunk_categories_str = chunk.metadata.get('all_categories', chunk.category)
                        chunk_categories_list = chunk_categories_str.split(', ') if isinstance(chunk_categories_str, str) else [chunk_categories_str]
                        
                        for cat in chunk_categories_list:
                            if cat not in current_categories_list:
                                current_categories_list.append(cat)
                        
                        # Convert back to string
                        current_chunk.metadata['all_categories'] = ', '.join(current_categories_list)
                        current_chunk.category = current_categories_list[0]  # Update primary category
                else:
                    # Different page, finalize current chunk and start new
                    if current_chunk:
                        merged_chunks.append(current_chunk)
                    current_chunk = chunk
            else:
                # Normal sized chunk
                if current_chunk:
                    merged_chunks.append(current_chunk)
                    current_chunk = None
                merged_chunks.append(chunk)
        
        # Don't forget the last chunk
        if current_chunk:
            merged_chunks.append(current_chunk)
        
        logger.info(f"Merged {len(chunks)} chunks into {len(merged_chunks)} chunks")
        return merged_chunks
    
    def filter_empty_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Filter out empty or whitespace-only chunks."""
        return [chunk for chunk in chunks if chunk.content.strip()]
