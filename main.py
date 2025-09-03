

import json
import re
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import sys

try:
    import pdfplumber
    import camelot
    import pandas as pd
    from PIL import Image
    import pytesseract
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages using: pip install -r requirements.txt")
    sys.exit(1)


class PDFParser:
    
    def __init__(self, pdf_path: str):
 
        self.pdf_path = Path(pdf_path)
        self.sections_pattern = re.compile(
            r'^(?:\d+\.?\s*)?([A-Z][A-Za-z\s]+?)(?:\n|\r\n?)',
            re.MULTILINE
        )
        self.subsections_pattern = re.compile(
            r'^(?:\d+\.\d+\.?\s*)?([A-Z][A-Za-z\s]+?)(?:\n|\r\n?)',
            re.MULTILINE
        )
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extract_sections_and_subsections(self, text: str) -> Tuple[str, str]:
   
        # Look for common section patterns
        section_patterns = [
            r'^\s*(\d+\.?\s*[A-Z][A-Za-z\s]+)',
            r'^\s*([A-Z][A-Z\s]+)\s*$',
            r'^\s*([A-Z][a-z][A-Za-z\s]+)\s*$'
        ]
        
        subsection_patterns = [
            r'^\s*(\d+\.\d+\.?\s*[A-Za-z][A-Za-z\s]+)',
            r'^\s*([a-z]\.\s*[A-Za-z][A-Za-z\s]+)',
            r'^\s*([A-Z][a-z][A-Za-z\s]+)\s*$'
        ]
        
        section = None
        sub_section = None
        
        lines = text.split('\n')
        for line in lines[:5]:  # Check first few lines
            line = line.strip()
            if not line:
                continue
                
            # Check for section
            for pattern in section_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match and not section:
                    section = match.group(1).strip()
                    break
            
            # Check for subsection
            for pattern in subsection_patterns:
                match = re.match(pattern, line, re.MULTILINE)
                if match and not sub_section and section:
                    sub_section = match.group(1).strip()
                    break
        
        return section, sub_section
    
    def clean_text(self, text: str) -> str:

        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove page numbers and headers/footers patterns
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        text = re.sub(r'\n\s*Page \d+ of \d+\s*\n', '\n', text, re.IGNORECASE)
        
        return text.strip()
    
    def extract_tables_from_page(self, page_num: int) -> List[Dict[str, Any]]:
        """
        Extract tables from a specific page using camelot.
        
        Args:
            page_num (int): Page number (1-indexed)
            
        Returns:
            List[Dict[str, Any]]: List of table dictionaries
        """
        tables = []
        try:
            # Use camelot to extract tables
            camelot_tables = camelot.read_pdf(
                str(self.pdf_path),
                pages=str(page_num),
                flavor='lattice'  # Use lattice for better table detection
            )
            
            for i, table in enumerate(camelot_tables):
                if table.df.empty:
                    continue
                
                # Convert DataFrame to list of lists
                table_data = []
                for _, row in table.df.iterrows():
                    table_data.append(row.tolist())
                
                # Remove empty rows
                table_data = [row for row in table_data if any(str(cell).strip() for cell in row)]
                
                if table_data:
                    tables.append({
                        "type": "table",
                        "section": None,  # Will be filled by context analysis
                        "sub_section": None,
                        "description": f"Table {i+1} from page {page_num}",
                        "table_data": table_data
                    })
        
        except Exception as e:
            self.logger.warning(f"Could not extract tables from page {page_num}: {e}")
            
        return tables
    
    def detect_charts_in_page(self, page) -> List[Dict[str, Any]]:
        charts = []
        
        try:
            # Look for images that might be charts
            images = page.images
            
            for i, image in enumerate(images):
                # Check if the image might be a chart based on size and position
                width = image.get('width', 0)
                height = image.get('height', 0)
                
               
                if width > 100 and height > 100:
                    # Try to extract any nearby text that might describe the chart
                    x0, y0 = image.get('x0', 0), image.get('y0', 0)
                    x1, y1 = image.get('x1', width), image.get('y1', height)
                    
                    # Look for text near the chart
                    nearby_text = ""
                    for text_obj in page.chars:
                        text_y = text_obj.get('y0', 0)
                        if abs(text_y - y1) < 50:  # Text within 50 points of chart
                            nearby_text += text_obj.get('text', '')
                    
                    charts.append({
                        "type": "chart",
                        "section": None,  # Will be filled by context analysis
                        "sub_section": None,
                        "description": f"Chart/Image {i+1} - {nearby_text[:100]}..." if nearby_text else f"Chart/Image {i+1}",
                        "table_data": [],  # Could be populated with extracted data
                        "dimensions": {"width": width, "height": height}
                    })
        
        except Exception as e:
            self.logger.warning(f"Could not detect charts: {e}")
        
        return charts
    
    def analyze_content_blocks(self, page) -> List[Dict[str, Any]]:
     
        content_blocks = []
        
        # Extract text with positioning information
        text_objects = page.chars
        if not text_objects:
            return content_blocks
        
        # Group text by approximate lines
        lines = {}
        for char in text_objects:
            y = round(char['y0'], 1)
            if y not in lines:
                lines[y] = []
            lines[y].append(char)
        
        # Sort lines by y-coordinate (top to bottom)
        sorted_lines = sorted(lines.items(), key=lambda x: -x[0])  # Negative for top-to-bottom
        
        current_paragraph = []
        current_y_group = None
        
        for y, chars in sorted_lines:
            line_text = ''.join([char['text'] for char in chars]).strip()
            
            if not line_text:
                continue
            if current_y_group is not None and abs(y - current_y_group) > 20:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    if len(paragraph_text.strip()) > 10:  # Minimum paragraph length
                        section, sub_section = self.extract_sections_and_subsections(paragraph_text)
                        
                        content_blocks.append({
                            "type": "paragraph",
                            "section": section,
                            "sub_section": sub_section,
                            "text": self.clean_text(paragraph_text)
                        })
                    
                    current_paragraph = []
            
            current_paragraph.append(line_text)
            current_y_group = y
        
        # Add the last paragraph
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            if len(paragraph_text.strip()) > 10:
                section, sub_section = self.extract_sections_and_subsections(paragraph_text)
                
                content_blocks.append({
                    "type": "paragraph",
                    "section": section,
                    "sub_section": sub_section,
                    "text": self.clean_text(paragraph_text)
                })
        
        return content_blocks
    
    def parse_pdf(self) -> Dict[str, Any]:
       
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        
        self.logger.info(f"Parsing PDF: {self.pdf_path}")
        
        result = {"pages": []}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                self.logger.info(f"Processing page {page_num}")
                
                page_content = []
                
                # Extract text content as paragraphs
                text_blocks = self.analyze_content_blocks(page)
                page_content.extend(text_blocks)
                
                # Extract tables
                tables = self.extract_tables_from_page(page_num)
                
                # Try to assign context to tables based on nearby text
                for table in tables:
                    # Find the most recent paragraph with a section
                    for block in reversed(text_blocks):
                        if block.get("section"):
                            table["section"] = block["section"]
                            table["sub_section"] = block.get("sub_section")
                            break
                
                page_content.extend(tables)
                
                # Detect charts/images
                charts = self.detect_charts_in_page(page)
                
                # Try to assign context to charts
                for chart in charts:
                    for block in reversed(text_blocks):
                        if block.get("section"):
                            chart["section"] = block["section"]
                            chart["sub_section"] = block.get("sub_section")
                            break
                
                page_content.extend(charts)
                
                result["pages"].append({
                    "page_number": page_num,
                    "content": page_content
                })
        
        self.logger.info(f"Successfully parsed {len(result['pages'])} pages")
        return result
    
    def save_json(self, data: Dict[str, Any], output_path: str):
      
        output_path = Path(output_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"JSON output saved to: {output_path}")


def main():
   
    parser = argparse.ArgumentParser(description="Parse PDF and extract structured JSON")
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument("-o", "--output", default="output.json", help="Output JSON file path")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        pdf_parser = PDFParser(args.input_pdf)
        extracted_data = pdf_parser.parse_pdf()
        pdf_parser.save_json(extracted_data, args.output)
        
        print(f"Successfully parsed {args.input_pdf}")
        print(f"Output saved to {args.output}")
        
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        sys.exit(1)


if __name__ == "__main__":

    main()
