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

## HTML 到 Markdown 转换器

`html_to_md_converter.py` 是一个强大的 HTML 到 Markdown 转换工具，专门设计用于清理和转换包含大量 CSS 和 JavaScript 的 HTML 文件。

### 使用方法

```bash
# 基本用法：输出文件名自动生成（将 .html 扩展名改为 .md）
python html_to_md_converter.py input.html

# 指定输出文件名
python html_to_md_converter.py input.html output.md

# 使用 --output 参数指定输出文件名
python html_to_md_converter.py input.html --output custom_name.md
```

### 主要功能

1. **智能 CSS 和 JavaScript 过滤**：
   - 使用 BeautifulSoup 预处理 HTML，完全移除 `<script>`、`<style>`、`<link>`、`<meta>` 和 `<noscript>` 标签
   - 移除所有元素的 `style`、`class`、`id` 等可能包含样式信息的属性
   - 使用正则表达式后处理，移除残留的 CSS 规则（包括 `@media` 查询）和 JavaScript 代码

2. **灵活的输出文件命名**：
   - 如果不指定输出文件名，自动使用输入文件名并将扩展名改为 `.md`
   - 支持通过位置参数或 `--output`/`-o` 选项指定输出文件名

3. **自动目录创建**：
   - 如果输出文件的目录不存在，会自动创建

4. **强化的错误处理**：
   - 文件不存在时提供清晰的错误信息
   - 处理编码问题和其他异常情况

5. **结构化内容保留**：
   - 只转换有意义的 HTML 结构标签（标题、段落、列表、表格、链接等）
   - 保持文档的逻辑结构和格式

### 输出说明

转换后的 Markdown 文件将：
- 完全不包含 CSS 样式和 JavaScript 代码
- 保留原始 HTML 的文档结构和内容
- 使用标准的 Markdown 语法格式化
- 清理多余的空行，保持文档整洁

### 依赖要求

- `markdownify`：HTML 到 Markdown 转换
- `beautifulsoup4`：HTML 解析和清理

### 使用示例

```bash
# 转换包含大量 CSS 的 HTML 报告文件
python html_to_md_converter.py qualification_report.html

# 转换并指定输出文件名
python html_to_md_converter.py complex_page.html clean_document.md
```

这个工具特别适合处理从网页保存的 HTML 文件或包含大量内联样式的报告文件，能够有效地提取出纯净的文档内容。