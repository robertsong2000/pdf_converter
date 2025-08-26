import argparse
import json
import re
import os
from pathlib import Path
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
    
    return soup

def html_to_json(html_content):
    """
    将HTML内容转换为JSON格式
    """
    soup = clean_html_content(html_content)
    
    # 构建JSON结构
    result = {
        "title": "",
        "headings": [],
        "paragraphs": [],
        "links": [],
        "images": [],
        "lists": [],
        "tables": [],
        "code_blocks": []
    }
    
    # 提取标题
    title_tag = soup.find('title')
    if title_tag:
        result["title"] = title_tag.get_text().strip()
    
    # 提取各级标题
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            result["headings"].append({
                "level": i,
                "text": heading.get_text().strip()
            })
    
    # 提取段落
    for paragraph in soup.find_all('p'):
        text = paragraph.get_text().strip()
        if text:
            result["paragraphs"].append(text)
    
    # 提取链接
    for link in soup.find_all('a', href=True):
        result["links"].append({
            "text": link.get_text().strip(),
            "url": link['href']
        })
    
    # 提取图片
    for img in soup.find_all('img', src=True):
        result["images"].append({
            "alt": img.get('alt', ''),
            "src": img['src']
        })
    
    # 提取列表
    for ul in soup.find_all('ul'):
        list_items = []
        for li in ul.find_all('li'):
            list_items.append(li.get_text().strip())
        if list_items:
            result["lists"].append({
                "type": "unordered",
                "items": list_items
            })
    
    for ol in soup.find_all('ol'):
        list_items = []
        for li in ol.find_all('li'):
            list_items.append(li.get_text().strip())
        if list_items:
            result["lists"].append({
                "type": "ordered",
                "items": list_items
            })
    
    # 提取表格
    for table in soup.find_all('table'):
        table_data = []
        headers = []
        
        # 提取表头
        thead = table.find('thead')
        if thead:
            for th in thead.find_all('th'):
                headers.append(th.get_text().strip())
        
        # 提取表体
        tbody = table.find('tbody')
        if tbody:
            for tr in tbody.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text().strip())
                if row:
                    table_data.append(row)
        elif not thead:  # 如果没有明确的thead和tbody
            for tr in table.find_all('tr'):
                row = []
                for td in tr.find_all(['td', 'th']):
                    row.append(td.get_text().strip())
                if row:
                    table_data.append(row)
        
        if table_data or headers:
            result["tables"].append({
                "headers": headers,
                "rows": table_data
            })
    
    # 提取代码块
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            continue
        code_text = code.get_text().strip()
        if code_text:
            result["code_blocks"].append(code_text)
    
    return result

def parse_test_report(html_content, output_dir):
    """
    解析测试报告HTML文件，提取测试用例并保存为单独的JSON文件
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有测试用例标题（包含"Test Case Silk ID"的<a>标签）
    test_case_links = []
    all_headings = soup.find_all('big', class_='Heading3')
    
    for heading in all_headings:
        # 查找heading中的<a>标签
        link = heading.find('a')
        if link:
            link_text = link.get_text().strip()
            # 只选择包含"Test Case Silk ID"的链接作为测试用例
            if 'Test Case Silk ID' in link_text:
                test_case_links.append(link)
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 解析每个测试用例
    for i, test_case_link in enumerate(test_case_links):
        # 获取测试用例名称
        test_case_text = test_case_link.get_text().strip()
        # 提取测试用例ID和名称
        # 格式: "序号 Test Case Silk ID:ID: 名称: 结果"
        if 'Test Case Silk ID:' in test_case_text:
            # 使用正则表达式提取ID和名称
            # 格式: "序号 Test Case Silk ID:ID: 名称: 结果"
            # 先尝试匹配完整的格式
            match = re.search(r'Test Case Silk ID:(\d+):\s*(.*?):\s*(Passed|Failed)', test_case_text)
            if match:
                test_case_id = match.group(1)
                test_case_name = match.group(2).strip()
            else:
                # 尝试另一种格式，其中结果在最后
                match = re.search(r'Test Case Silk ID:(\d+):\s*(.*?)\s*:\s*(Passed|Failed)$', test_case_text)
                if match:
                    test_case_id = match.group(1)
                    test_case_name = match.group(2).strip()
                else:
                    # 再尝试匹配没有结果的格式
                    match = re.search(r'Test Case Silk ID:(\d+):\s*(.*?)(?:\s*:)?$', test_case_text)
                    if match:
                        test_case_id = match.group(1)
                        test_case_name = match.group(2).strip()
                    else:
                        # 如果正则表达式不匹配，尝试使用旧方法
                        parts = test_case_text.split(':')
                        if len(parts) >= 4:
                            test_case_id = parts[2].strip()  # ID在第三个冒号后
                            # 名称在第四个冒号后，结果在最后
                            test_case_name = parts[3].strip()
                            # 如果还有更多部分，可能是结果信息
                            if len(parts) > 4:
                                test_case_name += '_' + '_'.join(parts[4:]).strip()
                        else:
                            test_case_id = str(i)
                            test_case_name = test_case_text
        else:
            test_case_id = str(i)
            test_case_name = test_case_text
        
        # 清理测试用例名称，用作文件名
        # 保留ID和结果信息在文件名中
        clean_name = re.sub(r'[^a-zA-Z0-9_\-: ]', '', test_case_name)
        filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', clean_name.replace(' ', '_'))
        # 确保文件名不为空
        if not filename:
            filename = f"test_case_{test_case_id}"
        # 确保文件名不会过长
        if len(filename) > 100:
            filename = filename[:100]
        
        # 查找测试用例的详细信息
        # 测试用例的详细信息在父级table的下一个兄弟元素中
        parent_table = test_case_link.find_parent('table')
        if parent_table:
            details = parent_table.find_next_sibling()
        else:
            details = None
        
        # 初始化测试用例数据
        test_case_data = {
            "id": test_case_id,
            "name": test_case_name,
            "steps": []
        }
        
        # 查找测试步骤表格
        if details:
            step_table = details.find('table', class_='ResultTable')
            if step_table:
                # 解析测试步骤
                rows = step_table.find_all('tr')
                for row in rows[1:]:  # 跳过表头
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        timestamp = cells[0].get_text().strip()
                        test_step = cells[1].get_text().strip()
                        description = cells[2].get_text().strip()
                        result = cells[3].get_text().strip()
                        
                        # 添加到测试步骤列表
                        test_case_data["steps"].append({
                            "timestamp": timestamp,
                            "test_step": test_step,
                            "description": description,
                            "result": result
                        })
        
        # 保存为JSON文件
        output_file = os.path.join(output_dir, f"{filename}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_case_data, f, ensure_ascii=False, indent=2)
        
        print(f"已保存测试用例 '{test_case_name}' 到 '{output_file}'")

def convert_file(input_filepath, output_filepath, parse_test_cases=False, test_cases_output_dir=None):
    """
    读取HTML文件内容，将其转换为JSON格式，并写入输出文件
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        if parse_test_cases and test_cases_output_dir:
            # 解析测试用例
            parse_test_report(html_content, test_cases_output_dir)
            print(f"测试用例已保存到目录 '{test_cases_output_dir}'")
        else:
            # 常规HTML到JSON转换
            json_content = html_to_json(html_content)
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_filepath)
            if output_dir:
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(json_content, f, ensure_ascii=False, indent=2)
            print(f"Successfully converted '{input_filepath}' to '{output_filepath}'")
    except FileNotFoundError:
        print(f"Error: Input file '{input_filepath}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_default_output_path(input_filepath):
    """
    通过更改扩展名生成默认输出路径
    """
    input_path = Path(input_filepath)
    return str(input_path.with_suffix('.json'))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="将HTML文件转换为JSON格式文件。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\示例:
  python html_to_json_converter.py input.html
  python html_to_json_converter.py input.html output.json
  python html_to_json_converter.py input.html --output custom_name.json
  python html_to_json_converter.py input.html --parse-test-cases --test-cases-output-dir ./test_cases
        """
    )
    parser.add_argument('input_file', type=str, help='输入HTML文件的路径。')
    parser.add_argument('output_file', type=str, nargs='?', help='输出JSON文件的路径（可选）。')
    parser.add_argument('--output', '-o', type=str, help='输出JSON文件的路径（替代方式）。')
    parser.add_argument('--parse-test-cases', action='store_true', help='解析测试用例并保存为单独的JSON文件')
    parser.add_argument('--test-cases-output-dir', type=str, help='测试用例输出目录')
    
    args = parser.parse_args()
    
    # 确定输出文件路径
    if args.output:
        output_file = args.output
    elif args.output_file:
        output_file = args.output_file
    else:
        output_file = generate_default_output_path(args.input_file)
    
    convert_file(args.input_file, output_file, args.parse_test_cases, args.test_cases_output_dir)