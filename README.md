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

## Markdown Test Case Parser

The `md_testcase_parser.py` script parses test cases from Markdown files and saves them as individual files.

### Usage
```
python md_testcase_parser.py input.md [--output output_dir]
```

### Features
- Extracts test cases marked with "Test case :"
- Cleans up document headers and footers
- Saves each test case as a separate Markdown file
- Supports various document types

### Output
Creates numbered test case files (testcase_1.md, testcase_2.md, etc.) in the specified output directory.

## Batch Test Case Parser

The `parse_md_testcases.sh` script provides batch processing functionality for multiple DVM markdown files.

### Usage
```bash
./parse_md_testcases.sh
```

### Features
- Automatically processes all `*DVM*.md` files in the current directory
- Creates separate output directories for each file (prefixed with `testcases_`)
- Copies the original markdown file to the output directory
- Automatically creates ZIP archives for each processed directory
- Uses strict error handling (`set -Eeuo pipefail`)

### Output Structure
For each input file (e.g., `UDS_SWDL_DVM.md`):
1. Creates directory: `testcases_UDS_SWDL_DVM/`
2. Extracts test cases into individual files within the directory
3. Copies the original file to the directory
4. Creates a ZIP archive: `testcases_UDS_SWDL_DVM.zip`

### Requirements
- Bash shell
- Python 3.x (for the underlying `md_testcase_parser.py`)
- `zip` utility for archive creation