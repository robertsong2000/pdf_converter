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

## HTML 到 JSON 转换器

`html_to_json_converter.py` 是一个将 HTML 文件转换为结构化 JSON 格式的工具，便于程序化处理和数据分析。

### 使用方法

```bash
# 基本用法：输出文件名自动生成（将 .html 扩展名改为 .json）
python html_to_json_converter.py input.html

# 指定输出文件名
python html_to_json_converter.py input.html output.json

# 使用 --output 参数指定输出文件名
python html_to_json_converter.py input.html --output custom_name.json
```

### 主要功能

1. **结构化数据提取**：
   - 提取页面标题
   - 提取各级标题（h1-h6）
   - 提取段落文本
   - 提取链接和图片信息
   - 提取有序和无序列表
   - 提取表格数据
   - 提取代码块

2. **智能内容清理**：
   - 使用 BeautifulSoup 预处理 HTML，完全移除 `<script>`、`<style>`、`<link>`、`<meta>` 和 `<noscript>` 标签
   - 移除所有元素的 `style`、`class`、`id` 等可能包含样式信息的属性

3. **灵活的输出文件命名**：
   - 如果不指定输出文件名，自动使用输入文件名并将扩展名改为 `.json`
   - 支持通过位置参数或 `--output`/`-o` 选项指定输出文件名

4. **自动目录创建**：
   - 如果输出文件的目录不存在，会自动创建

5. **强化的错误处理**：
   - 文件不存在时提供清晰的错误信息
   - 处理编码问题和其他异常情况

### 输出格式

生成的 JSON 文件包含以下结构：

```json
{
  "title": "页面标题",
  "headings": [
    {"level": 1, "text": "标题文本"},
    {"level": 2, "text": "子标题文本"}
  ],
  "paragraphs": ["段落文本1", "段落文本2"],
  "links": [
    {"text": "链接文本", "url": "链接地址"}
  ],
  "images": [
    {"alt": "替代文本", "src": "图片地址"}
  ],
  "lists": [
    {"type": "unordered", "items": ["项目1", "项目2"]},
    {"type": "ordered", "items": ["项目1", "项目2"]}
  ],
  "tables": [
    {
      "headers": ["列1", "列2"],
      "rows": [["行1列1", "行1列2"], ["行2列1", "行2列2"]]
    }
  ],
  "code_blocks": ["代码块文本"]
}
```

### 依赖要求

- `beautifulsoup4`：HTML 解析和清理

### 使用示例

```bash
# 转换 HTML 文件为 JSON
python html_to_json_converter.py webpage.html

# 转换并指定输出文件名
python html_to_json_converter.py webpage.html structured_data.json

# 解析测试报告中的测试用例并保存为单独的JSON文件
python html_to_json_converter.py qualification_report.html --parse-test-cases --test-cases-output-dir ./test_cases
```

### 测试用例解析功能

新增的测试用例解析功能可以从特定格式的测试报告HTML文件中提取测试用例，并将每个测试用例保存为单独的JSON文件。此功能专为自动化测试报告分析而设计，能够高效地从复杂的HTML结构中抽离出结构化的测试数据。

#### 使用方法

```bash
python html_to_json_converter.py input.html --parse-test-cases --test-cases-output-dir ./test_cases
```

#### 功能特性

1. **测试用例识别**：
   - 自动识别测试报告中的测试用例标题
   - 提取测试用例ID和名称

2. **测试步骤提取**：
   - 提取每个测试用例的详细测试步骤
   - 保留时间戳、测试步骤、描述和结果信息

3. **结构化输出**：
   - 每个测试用例保存为独立的JSON文件
   - 文件名基于测试用例名称生成

4. **灵活的输出目录**：
   - 支持自定义测试用例JSON文件的输出目录

#### 输出格式

生成的测试用例JSON文件包含以下结构：

```json
{
  "id": "测试用例ID",
  "name": "测试用例名称",
  "steps": [
    {
      "timestamp": "时间戳",
      "test_step": "测试步骤",
      "description": "描述",
      "result": "结果"
    }
  ]
}
```

#### 使用示例

```bash
# 解析测试报告并提取测试用例
python html_to_json_converter.py qualification_frontwipervariablerate_report.html --parse-test-cases --test-cases-output-dir ./extracted_test_cases
```