"""
PDF Processing Service for HealthTwin AI
Handles PDF to image conversion for prescription scanning
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import pypdfium2 as pdfium
    PDF_SUPPORT = True
    logger.info("PDF support available via pypdfium2")
except ImportError:
    PDF_SUPPORT = False
    logger.warning("PDF support not available - pypdfium2 not installed")

try:
    import cv2
    CV2_SUPPORT = True
except ImportError:
    CV2_SUPPORT = False
    logger.warning("OpenCV not available for image processing")

try:
    from PIL import Image
    PIL_SUPPORT = True
except ImportError:
    PIL_SUPPORT = False
    logger.warning("PIL not available for image processing")


class PDFProcessor:
    """
    PDF processing service for extracting images from PDF files
    for prescription OCR processing
    """
    
    def __init__(self):
        self.max_pages = 10  # Limit to prevent abuse
        self.max_file_size = 50 * 1024 * 1024  # 50MB max for PDFs
        self.zoom_factor = 2.0  # Higher resolution for better OCR
        self.supported = PDF_SUPPORT and CV2_SUPPORT and PIL_SUPPORT
        
        if not self.supported:
            logger.warning("PDF processing not fully supported - missing dependencies")
    
    def is_pdf_supported(self) -> bool:
        """Check if PDF processing is supported"""
        return self.supported
    
    def validate_pdf_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate PDF file for processing
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Dict with validation results
        """
        try:
            # Check file size
            if len(file_content) > self.max_file_size:
                return {
                    "valid": False,
                    "error": f"PDF file too large. Maximum size is {self.max_file_size // (1024*1024)}MB"
                }
            
            # Check if it's a valid PDF
            if not self.supported:
                return {
                    "valid": False,
                    "error": "PDF processing not supported - missing dependencies"
                }
            
            # Try to open the PDF
            try:
                doc = pdfium.PdfDocument(file_content)
                page_count = len(doc)
                doc.close()
                
                if page_count == 0:
                    return {
                        "valid": False,
                        "error": "PDF file appears to be empty"
                    }
                
                if page_count > self.max_pages:
                    return {
                        "valid": False,
                        "error": f"PDF has too many pages. Maximum allowed is {self.max_pages}"
                    }
                
                return {
                    "valid": True,
                    "page_count": page_count,
                    "file_size": len(file_content)
                }
                
            except Exception as e:
                return {
                    "valid": False,
                    "error": f"Invalid PDF file: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return {
                "valid": False,
                "error": f"PDF validation error: {str(e)}"
            }
    
    def extract_images_from_pdf(self, file_content: bytes) -> List[Tuple[np.ndarray, Dict[str, Any]]]:
        """
        Extract images from PDF pages for OCR processing
        
        Args:
            file_content: PDF file content as bytes
            
        Returns:
            List of tuples containing (image_array, metadata)
        """
        if not self.supported:
            raise ValueError("PDF processing not supported")
        
        images = []
        
        try:
            doc = pdfium.PdfDocument(file_content)
            
            for page_num in range(len(doc)):
                if page_num >= self.max_pages:
                    logger.warning(f"Stopping at page {self.max_pages} (max limit)")
                    break
                
                try:
                    page = doc[page_num]
                    
                    # Render page to PIL image
                    pil_image = page.render(
                        scale=self.zoom_factor,
                        rotation=0
                    ).to_pil()
                    
                    # Convert to RGB if needed
                    if pil_image.mode != 'RGB':
                        pil_image = pil_image.convert('RGB')
                    
                    # Convert to numpy array
                    image_array = np.array(pil_image)
                    
                    # Convert RGB to BGR for OpenCV compatibility
                    if CV2_SUPPORT:
                        image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                    
                    # Create metadata
                    metadata = {
                        "page_number": page_num + 1,
                        "width": image_array.shape[1],
                        "height": image_array.shape[0],
                        "zoom_factor": self.zoom_factor,
                        "source": "pdf_page"
                    }
                    
                    images.append((image_array, metadata))
                    logger.info(f"Extracted page {page_num + 1}: {metadata['width']}x{metadata['height']}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract page {page_num + 1}: {e}")
                    continue
            
            doc.close()
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            raise ValueError(f"Failed to process PDF: {str(e)}")
        
        return images
    
    def save_images_temporarily(self, images: List[Tuple[np.ndarray, Dict[str, Any]]]) -> List[str]:
        """
        Save extracted images to temporary files for OCR processing
        
        Args:
            images: List of (image_array, metadata) tuples
            
        Returns:
            List of temporary file paths
        """
        temp_paths = []
        
        for i, (image_array, metadata) in enumerate(images):
            try:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f'_page_{metadata["page_number"]}.jpg',
                    prefix='pdf_prescription_'
                )
                temp_path = temp_file.name
                temp_file.close()
                
                # Save image
                if CV2_SUPPORT:
                    cv2.imwrite(temp_path, image_array)
                elif PIL_SUPPORT:
                    # Convert BGR back to RGB for PIL
                    if len(image_array.shape) == 3:
                        image_array = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(image_array)
                    pil_image.save(temp_path, 'JPEG', quality=95)
                else:
                    raise ValueError("No image saving library available")
                
                temp_paths.append(temp_path)
                logger.info(f"Saved page {metadata['page_number']} to {temp_path}")
                
            except Exception as e:
                logger.error(f"Failed to save image {i}: {e}")
                # Clean up any files created so far
                for path in temp_paths:
                    try:
                        os.unlink(path)
                    except:
                        pass
                raise ValueError(f"Failed to save extracted images: {str(e)}")
        
        return temp_paths
    
    def cleanup_temp_files(self, temp_paths: List[str]) -> None:
        """
        Clean up temporary files
        
        Args:
            temp_paths: List of temporary file paths to delete
        """
        for path in temp_paths:
            try:
                if os.path.exists(path):
                    os.unlink(path)
                    logger.debug(f"Cleaned up temporary file: {path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")
    
    def process_pdf_for_ocr(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline for OCR
        
        Args:
            file_content: PDF file content as bytes
            filename: Original filename
            
        Returns:
            Dict containing processing results and temporary file paths
        """
        try:
            # Validate PDF
            validation = self.validate_pdf_file(file_content, filename)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"],
                    "temp_paths": []
                }
            
            # Extract images
            images = self.extract_images_from_pdf(file_content)
            if not images:
                return {
                    "success": False,
                    "error": "No images could be extracted from PDF",
                    "temp_paths": []
                }
            
            # Save to temporary files
            temp_paths = self.save_images_temporarily(images)
            
            return {
                "success": True,
                "page_count": validation["page_count"],
                "extracted_pages": len(images),
                "temp_paths": temp_paths,
                "file_size": validation["file_size"],
                "images_metadata": [metadata for _, metadata in images]
            }
            
        except Exception as e:
            logger.error(f"PDF processing pipeline failed: {e}")
            return {
                "success": False,
                "error": f"PDF processing failed: {str(e)}",
                "temp_paths": []
            }
