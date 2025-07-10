import requests
from dotenv import load_dotenv
import os
import argparse

load_dotenv()

# 本地Stirling PDF服务地址（默认端口8083）
BASE_URL = os.getenv("STIRLING_PDF_BASE_URL", "http://localhost:8083")
# 目标接口路径
API_ENDPOINT = "/api/v1/convert/pdf/markdown"
# 完整请求URL
url = f"{BASE_URL}{API_ENDPOINT}"

# 1. 准备请求参数
parser = argparse.ArgumentParser(description="Convert PDF to Markdown using Stirling PDF API.")
parser.add_argument("pdf_file_path", type=str, help="Path to the input PDF file.")
parser.add_argument("--output", dest="output_markdown_path", type=str, default="output.md",
                    help="Path to save the output Markdown file. Defaults to 'output.md'.")
args = parser.parse_args()

pdf_file_path = args.pdf_file_path
output_markdown_path = args.output_markdown_path

# 2. 构建请求数据（multipart/form-data格式，用于上传文件）
files = {
    "fileInput": (os.path.basename(pdf_file_path), open(pdf_file_path, "rb"), "application/pdf")  # 上传PDF文件
}

# 3. 发送POST请求
try:
    response = requests.post(url, files=files)
    # 4. 处理响应
    if response.status_code == 200:
        # 接口返回Markdown内容
        markdown_content = response.text
        with open(output_markdown_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        print(f"PDF已成功转换为Markdown并保存到：{output_markdown_path}")
    else:
        print(f"请求失败，状态码：{response.status_code}，响应内容：{response.text}")
except Exception as e:
    print(f"调用接口出错：{str(e)}")