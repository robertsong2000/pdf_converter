import argparse
import os
from pathlib import Path
from markdownify import markdownify as md

def html_to_md(html_content):
    """
    Converts HTML content to Markdown content with custom options.
    """
    return md(html_content, 
              strip=['script', 'style'], 
              autolinks=True, 
              strong_em_symbol='**', 
              heading_style='ATX')

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