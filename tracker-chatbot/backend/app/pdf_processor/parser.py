import fitz  # PyMuPDF
import pdfplumber
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PDFContent:
    text: str
    pages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    tables: List[Dict[str, Any]]
    toc: List[Dict[str, Any]]


class PDFParser:
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def parse_pdf(self, file_path: str) -> PDFContent:
        """Parse PDF file and extract text, tables, and metadata."""
        doc = None
        try:
            # Extract with PyMuPDF for text and metadata
            doc = fitz.open(file_path)
            
            # Get document metadata safely
            metadata = self._extract_metadata(doc)
            
            # Extract text and page info
            pages = []
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()
                
                # Clean text artifacts
                cleaned_text = self._clean_text(page_text)
                
                page_info = {
                    'page_number': page_num + 1,
                    'text': cleaned_text,
                    'char_count': len(cleaned_text),
                    'bbox': page.rect,
                }
                
                pages.append(page_info)
                full_text += cleaned_text + "\n"
            
            # Extract tables with pdfplumber (streaming for memory efficiency)
            tables = self._extract_tables(file_path)
            
            # Extract table of contents with better error handling
            toc = self._extract_toc(doc)
            
            return PDFContent(
                text=full_text,
                pages=pages,
                metadata=metadata,
                tables=tables,
                toc=toc
            )
            
        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {str(e)}")
            raise
        finally:
            # Ensure document is always closed to prevent resource leaks
            if doc is not None:
                doc.close()
    
    def _extract_metadata(self, doc) -> Dict[str, Any]:
        """Extract PDF metadata safely."""
        try:
            metadata = doc.metadata or {}  # Handle None metadata
            return {
                'title': metadata.get('title', '') or '',
                'author': metadata.get('author', '') or '',
                'subject': metadata.get('subject', '') or '',
                'creator': metadata.get('creator', '') or '',
                'producer': metadata.get('producer', '') or '',
                'creation_date': metadata.get('creationDate', '') or '',
                'modification_date': metadata.get('modDate', '') or '',
                'page_count': len(doc),
            }
        except Exception as e:
            logger.warning(f"Error extracting metadata: {str(e)}")
            return {
                'title': '',
                'author': '',
                'subject': '',
                'creator': '',
                'producer': '',
                'creation_date': '',
                'modification_date': '',
                'page_count': len(doc) if doc else 0,
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean text artifacts from PDF extraction."""
        if not text:
            return ""
        
        # Handle character encoding issues
        try:
            # Try to fix common encoding issues
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
        except UnicodeError:
            logger.warning("Text encoding issue, using original text")
        
        # Remove excessive whitespace but preserve structure
        text = re.sub(r'\s+', ' ', text)
        
        # Less aggressive character cleaning - preserve technical characters
        # Keep: letters, numbers, spaces, punctuation, technical symbols
        # Remove: control characters and random artifacts
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Fix common OCR/extraction issues but preserve technical terms
        # List of common technical acronyms to preserve
        technical_terms = {
            'WiFi', 'IoT', 'USB', 'API', 'HTTP', 'HTTPS', 'URL', 'JSON', 'XML', 'HTML',
            'CSS', 'SQL', 'NoSQL', 'CPU', 'GPU', 'RAM', 'ROM', 'BIOS', 'UEFI', 'PDF',
            'LTE', '5G', '4G', '3G', '2G', 'GPS', 'GPRS', 'EDGE', 'HSPA', 'WCDMA',
            'CDMA', 'TDMA', 'FDMA', 'VoIP', 'SIP', 'RTP', 'TCP', 'UDP', 'IP', 'IPv4',
            'IPv6', 'DNS', 'DHCP', 'NAT', 'VPN', 'SSH', 'SSL', 'TLS', 'FTP', 'SMTP',
            'POP3', 'IMAP', 'LDAP', 'Kerberos', 'OAuth', 'JWT', 'REST', 'SOAP',
            'XML', 'XSLT', 'XPATH', 'XQuery', 'DOM', 'SAX', 'AJAX', 'XHR', 'WSDL',
            'UML', 'ERD', 'BPMN', 'IDE', 'SDK', 'API', 'CLI', 'GUI', 'UI', 'UX',
            'AI', 'ML', 'DL', 'NLP', 'CV', 'OCR', 'RPA', 'BI', 'CRM', 'ERP', 'SCM'
        }
        
        # Create pattern to preserve technical terms
        term_pattern = '|'.join(re.escape(term) for term in technical_terms)
        
        # Protect technical terms from camelCase splitting
        for term in technical_terms:
            text = text.replace(term, f'__PROTECTED_{term}__')
        
        # Fix camelCase but be more conservative
        text = re.sub(r'([a-z])([A-Z])([a-z])', r'\1 \2\3', text)  # Only split if followed by lowercase
        
        # Restore protected terms
        for term in technical_terms:
            text = text.replace(f'__PROTECTED_{term}__', term)
        
        # Fix spacing around punctuation
        text = re.sub(r'\s*([.,;:!?])\s*', r'\1 ', text)
        text = re.sub(r'\s*([()\[\]{}])\s*', r' \1 ', text)
        
        # Remove line breaks within sentences but preserve list structure
        # Don't merge lines that start with list markers or numbers
        text = re.sub(r'(?<=[.!?])\s*\n\s*', ' ', text)
        text = re.sub(r'(?<=[a-z])\s*\n\s*(?=[a-z])', ' ', text)
        # Preserve line breaks that start list items
        text = re.sub(r'\n(?=\s*[-•*]\s|\s*\d+\.\s)', '\n', text)
        
        # Clean up extra spaces but preserve single spaces
        text = re.sub(r' {2,}', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Preserve paragraph breaks
        
        return text.strip()
    
    def _extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from PDF using pdfplumber with memory management."""
        tables = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_tables = page.extract_tables()
                        if page_tables:
                            for table_num, table in enumerate(page_tables):
                                # Clean table data and filter empty rows
                                cleaned_table = []
                                for row in table:
                                    if row:  # Skip None rows
                                        cleaned_row = []
                                        for cell in row:
                                            if cell is not None:
                                                cleaned_cell = str(cell).strip()
                                                cleaned_row.append(cleaned_cell)
                                            else:
                                                cleaned_row.append("")
                                        if any(cleaned_row):  # Only add non-empty rows
                                            cleaned_table.append(cleaned_row)
                                
                                if cleaned_table:
                                    tables.append({
                                        'page_number': page_num + 1,
                                        'table_number': table_num + 1,
                                        'data': cleaned_table,
                                        'rows': len(cleaned_table),
                                        'columns': len(cleaned_table[0]) if cleaned_table else 0
                                    })
                        
                        # Clear page from memory to prevent memory leaks
                        page.close()
                        
                    except Exception as e:
                        logger.warning(f"Error extracting tables from page {page_num + 1}: {str(e)}")
                        continue
        
        except Exception as e:
            logger.warning(f"Error extracting tables: {str(e)}")
        
        return tables
    
    def _extract_toc(self, doc) -> List[Dict[str, Any]]:
        """Extract table of contents from PDF with multiple format support."""
        toc = []
        
        try:
            # Try standard TOC extraction first
            toc_data = doc.get_toc()
            if toc_data:
                for item in toc_data:
                    if len(item) >= 3:
                        level, title, page_num = item[:3]
                        if title and title.strip():  # Only add non-empty titles
                            toc.append({
                                'level': level,
                                'title': title.strip(),
                                'page_number': page_num
                            })
            
            # If no TOC found, try to extract from outlines (bookmarks)
            if not toc:
                try:
                    outlines = doc.get_outline()
                    if outlines:
                        self._extract_from_outlines(outlines, toc, 0)
                except:
                    logger.debug("No outlines found in PDF")
            
            # If still no TOC, try to find it in the first few pages
            if not toc:
                toc = self._extract_toc_from_text(doc)
            
            logger.info(f"Extracted {len(toc)} TOC entries")
            
        except Exception as e:
            logger.warning(f"Error extracting TOC: {str(e)}")
        
        return toc
    
    def _extract_from_outlines(self, outlines, toc_list, level):
        """Recursively extract TOC from PDF outlines."""
        for outline in outlines:
            try:
                if isinstance(outline, dict):
                    title = outline.get('title', '').strip()
                    page = outline.get('page', 0)
                    if title:
                        toc_list.append({
                            'level': level,
                            'title': title,
                            'page_number': page + 1  # Convert to 1-based indexing
                        })
                    
                    # Recursively process nested outlines
                    if 'kids' in outline:
                        self._extract_from_outlines(outline['kids'], toc_list, level + 1)
                        
            except Exception as e:
                logger.debug(f"Error processing outline item: {str(e)}")
                continue
    
    def _extract_toc_from_text(self, doc) -> List[Dict[str, Any]]:
        """Extract TOC by searching for patterns in first few pages."""
        toc = []
        
        # Only check first 5 pages for TOC
        max_pages = min(5, len(doc))
        
        toc_patterns = [
            r'^(\d+)\.\s+(.+?)\s+(\d+)$',  # "1. Chapter Title 123"
            r'^([A-Za-z]+)\s+(\d+)$',       # "Contents 123"
            r'^(\.{3,})\s+(\d+)$',          # "......... 123"
        ]
        
        for page_num in range(max_pages):
            try:
                page = doc[page_num]
                text = page.get_text()
                lines = text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Try to match TOC patterns
                    for pattern in toc_patterns:
                        match = re.match(pattern, line)
                        if match:
                            groups = match.groups()
                            if len(groups) >= 2:
                                title = groups[0] if len(groups) == 2 else groups[1]
                                page_num_toc = int(groups[-1])
                                
                                if len(title) > 3:  # Filter out very short titles
                                    toc.append({
                                        'level': 1,
                                        'title': title,
                                        'page_number': page_num_toc
                                    })
                                    break
                
            except Exception as e:
                logger.debug(f"Error extracting TOC from page {page_num + 1}: {str(e)}")
                continue
        
        return toc
    
    def validate_file(self, file_path: str) -> bool:
        """Validate if file is a supported PDF."""
        try:
            doc = fitz.open(file_path)
            is_valid = len(doc) > 0
            doc.close()
            return is_valid
        except:
            return False
    
    def get_page_count(self, file_path: str) -> int:
        """Get page count of PDF."""
        try:
            doc = fitz.open(file_path)
            count = len(doc)
            doc.close()
            return count
        except:
            return 0
