This PDF parser intelligently extracts and categorizes content from PDF documents, maintaining the original document structure while organizing information into three main content types:

Paragraphs: Text content with section and sub-section identification
Tables: Tabular data with proper formatting preservation
Charts/Images: Visual content with contextual descriptions

The parser maintains page-level hierarchy and provides clean, readable output suitable for further processing or analysis.
Features

Hierarchical Content Extraction: Preserves document structure with sections and sub-sections
Multi-Content Type Support: Handles text, tables, and visual content
Intelligent Section Detection: Automatically identifies document sections and sub-sections
Table Extraction: Uses advanced algorithms to detect and extract tabular data
Chart/Image Detection: Identifies visual content with contextual information
Clean Text Processing: Removes formatting artifacts and excessive whitespace
Modular Architecture: Well-structured, maintainable codebase
Command Line Interface: Easy-to-use CLI for batch processing
Comprehensive Logging: Detailed logging for debugging and monitoring
Installation

1} Clone the repository:

bashgit clone https://github.com/yourusername/pdf-parser.git
cd pdf-parser

2} Install dependencies:

bashpip install -r requirements.txt



Usage
bashpython pdf_parser.py input.pdf
With Custom Output File
bashpython pdf_parser.py input.pdf -o extracted_content.json
With Verbose Logging
bashpython pdf_parser.py input.pdf -v

Command Line Options

input_pdf: Path to the input PDF file (required)
-o, --output: Specify output JSON file path (default: output.json)
-v, --verbose: Enable detailed logging

The parser generates JSON output with the following  structure as  mentioned in the document 
 JSON Structure
The JSON :
○ Maintains page-level hierarchy.
○ Captures the type of data:
■ paragraph
■ table
■ chart
○ Includes section and sub-section names where applicable
