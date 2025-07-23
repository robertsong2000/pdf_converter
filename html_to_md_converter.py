import argparse
import os
import re
from pathlib import Path
from markdownify import markdownify as md
from bs4 import BeautifulSoup

def clean_html_content(html_content):
    """
    使用 BeautifulSoup 预处理 HTML，移除 CSS 和 JavaScript 内容
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 移除所有 script 标签
    for script in soup.find_all('script'):
        script.decompose()
    
    # 移除所有 style 标签
    for style in soup.find_all('style'):
        style.decompose()
    
    # 移除所有 link 标签（通常用于外部 CSS）
    for link in soup.find_all('link'):
        link.decompose()
    
    # 移除所有 meta 标签
    for meta in soup.find_all('meta'):
        meta.decompose()
    
    # 移除所有 noscript 标签
    for noscript in soup.find_all('noscript'):
        noscript.decompose()
    
    # 移除所有元素的 style 属性
    for element in soup.find_all():
        if element.has_attr('style'):
            del element['style']
        # 移除其他可能包含 CSS 的属性
        for attr in ['class', 'id', 'onclick', 'onload', 'onmouseover', 'onmouseout']:
            if element.has_attr(attr):
                del element[attr]
    
    return str(soup)

def remove_css_from_text(text):
    """
    从文本中移除 CSS 规则和 JavaScript 代码
    """
    # 移除 CSS 规则（包括 @media 查询）
    text = re.sub(r'@media[^{]*\{[^{}]*\{[^{}]*\}[^{}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'@media[^{]*\{[^{}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'[^{}]*\{[^{}]*\}', '', text, flags=re.DOTALL)
    
    # 移除 JavaScript 函数和变量声明
    text = re.sub(r'var\s+\w+\s*=.*?;', '', text, flags=re.DOTALL)
    text = re.sub(r'function\s+\w+\s*\([^)]*\)\s*\{.*?\}', '', text, flags=re.DOTALL)
    
    # 移除多余的空行
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    text = re.sub(r'^\s*\n', '', text, flags=re.MULTILINE)
    
    return text.strip()

def html_to_md(html_content):
    """
    Converts HTML content to Markdown content with custom options.
    先清理 HTML 内容，移除 CSS 和 JavaScript，然后转换为 Markdown。
    """
    # 预处理 HTML，移除不需要的内容
    cleaned_html = clean_html_content(html_content)
    
    # 转换为 Markdown
    markdown_content = md(cleaned_html, 
                         convert=['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                                 'ul', 'ol', 'li', 'a', 'strong', 'em', 'b', 'i', 
                                 'table', 'tr', 'td', 'th', 'thead', 'tbody',
                                 'blockquote', 'pre', 'code', 'br', 'hr', 'span'],
                         autolinks=True, 
                         strong_em_symbol='**', 
                         heading_style='ATX',
                         escape_misc=False)
    
    # 后处理：移除可能残留的 CSS 和 JavaScript 内容
    markdown_content = remove_css_from_text(markdown_content)
    
    return markdown_content

def convert_file(input_filepath, output_filepath):
    """
    Reads HTML content from input_filepath, converts it to Markdown,
    and writes the Markdown content to output_filepath.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        markdown_content = html_to_md(html_content)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_filepath)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Successfully converted '{input_filepath}' to '{output_filepath}'")
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_default_output_path(input_filepath):
    """
    Generate default output path by changing the extension to .md
    """
    input_path = Path(input_filepath)
    return str(input_path.with_suffix('.md'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert an HTML file to a Markdown file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python html_to_md_converter.py input.html
  python html_to_md_converter.py input.html output.md
  python html_to_md_converter.py input.html --output custom_name.md
        """
    )
    parser.add_argument('input_file', type=str, help='Path to the input HTML file.')
    parser.add_argument('output_file', type=str, nargs='?', help='Path to the output Markdown file (optional).')
    parser.add_argument('--output', '-o', type=str, help='Path to the output Markdown file (alternative way).')
    
    args = parser.parse_args()
    
    # 确定输出文件路径
    if args.output:
        output_file = args.output
    elif args.output_file:
        output_file = args.output_file
    else:
        output_file = generate_default_output_path(args.input_file)
    
    convert_file(args.input_file, output_file)