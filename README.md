# PDF to Markdown Converter

A Python script that converts PDF files to Markdown format using Stirling PDF API.

## Requirements
- Python 3.x
- `python-dotenv`
- `requests`

## Installation
1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
```
python pdf_converter.py input.pdf [--output output.md]
```

## Configuration
Create a `.env` file with:
```
STIRLING_PDF_BASE_URL=http://localhost:8083
```