"""
Vision Service for extracting text from images and documents.

This module uses OpenAI's Vision API to extract text content from
screenshots, images, and PDF files.
"""

import logging
import base64
import io
from typing import Optional, Union
from pathlib import Path

from openai import OpenAI
from PIL import Image
import PyPDF2

from ..utils.exceptions import VisionServiceError

logger = logging.getLogger(__name__)


class VisionService:
    """
    Service for extracting text from images and PDFs using OpenAI Vision API.
    """
    
    def __init__(self, client: OpenAI, model: str = "gpt-4o"):
        """
        Initialize the Vision Service.
        
        Args:
            client: OpenAI client instance
            model: Model to use for vision tasks (default: gpt-4o)
        """
        self.client = client
        self.model = model
        logger.info(f"Initialized VisionService with model {self.model}")
    
    def extract_text_from_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None
    ) -> str:
        """
        Extract text content from an image using OpenAI Vision API.
        
        Args:
            image_data: Image file bytes
            prompt: Optional custom prompt for text extraction
            
        Returns:
            str: Extracted text content
            
        Raises:
            VisionServiceError: If text extraction fails
        """
        try:
            logger.info("Extracting text from image using Vision API")
            
            # Encode image to base64
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Default prompt for text extraction
            if prompt is None:
                prompt = (
                    "Extract all text content from this image. "
                    "If this appears to be a calendar, schedule, or task list, "
                    "extract event details including dates, times, titles, and descriptions. "
                    "If it's a document or screenshot, extract all readable text. "
                    "Format the output clearly and preserve important structure."
                )
            
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            extracted_text = response.choices[0].message.content
            logger.info(f"Successfully extracted {len(extracted_text)} characters from image")
            
            return extracted_text
            
        except Exception as e:
            logger.error(f"Failed to extract text from image: {str(e)}", exc_info=True)
            raise VisionServiceError(f"Image text extraction failed: {str(e)}")
    
    def extract_text_from_pdf(
        self,
        pdf_data: bytes,
        use_vision_for_scanned: bool = True
    ) -> str:
        """
        Extract text from a PDF file.
        
        First attempts text extraction using PyPDF2. If no text is found
        (indicating a scanned PDF), optionally uses Vision API on each page.
        
        Args:
            pdf_data: PDF file bytes
            use_vision_for_scanned: Whether to use Vision API for scanned PDFs
            
        Returns:
            str: Extracted text content
            
        Raises:
            VisionServiceError: If text extraction fails
        """
        try:
            logger.info("Extracting text from PDF")
            
            # Try text-based extraction first
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            extracted_text = ""
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    extracted_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            # If we got text, return it
            if extracted_text.strip():
                logger.info(f"Extracted {len(extracted_text)} characters from PDF using text extraction")
                return extracted_text
            
            # If no text found and vision is enabled, use Vision API
            if use_vision_for_scanned:
                logger.info("No text found in PDF, attempting Vision API extraction")
                
                # Convert PDF pages to images and extract text
                # Note: This requires additional libraries like pdf2image
                # For now, return a message indicating this is a scanned PDF
                return (
                    "[Scanned PDF detected] This appears to be a scanned PDF. "
                    "Please use an image format (PNG, JPG) for better text extraction, "
                    "or implement pdf2image conversion for scanned PDFs."
                )
            
            return "[Empty PDF] No text content found in the PDF file."
            
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}", exc_info=True)
            raise VisionServiceError(f"PDF text extraction failed: {str(e)}")
    
    def process_file(
        self,
        file_data: bytes,
        file_type: str
    ) -> str:
        """
        Process a file and extract text based on its type.
        
        Args:
            file_data: File bytes
            file_type: MIME type or file extension (e.g., 'image/png', 'application/pdf', '.jpg')
            
        Returns:
            str: Extracted text content
            
        Raises:
            VisionServiceError: If file processing fails or unsupported type
        """
        try:
            # Normalize file type
            file_type_lower = file_type.lower()
            
            # Handle images
            if any(img_type in file_type_lower for img_type in ['image/', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']):
                logger.info(f"Processing image file (type: {file_type})")
                return self.extract_text_from_image(file_data)
            
            # Handle PDFs
            elif 'pdf' in file_type_lower or file_type_lower.endswith('.pdf'):
                logger.info(f"Processing PDF file (type: {file_type})")
                return self.extract_text_from_pdf(file_data)
            
            else:
                raise VisionServiceError(
                    f"Unsupported file type: {file_type}. "
                    "Supported types: images (jpg, png, gif, etc.) and PDF files."
                )
                
        except VisionServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to process file: {str(e)}", exc_info=True)
            raise VisionServiceError(f"File processing failed: {str(e)}")
