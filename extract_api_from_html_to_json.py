#!/usr/bin/env python3
"""
CAPL函数API文档提取脚本
从HTML文件中提取CAPL函数的API接口说明
"""

import os
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def extract_api_from_html(html_content, page_number):
    """
    从HTML内容中提取CAPL函数API信息
    
    参数:
        html_content: HTML内容
        page_number: 页码
    
    返回:
        list: API信息列表
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    api_list = []
    
    # 首先检查是否是Availability Chart页面
    availability_chart = False
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        if 'Availability Chart' in text:
            availability_chart = True
            break
    
    if availability_chart:
        # 处理Availability Chart页面
        return extract_availability_chart(soup, page_number)
    
    # 查找函数名 - 以粗体显示在页面右侧
    function_name = None
    function_top = None
    
    # 收集所有段落信息
    all_paragraphs = []
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        style = p.get('style', '')
        
        left_match = re.search(r'left:(\d+)px', style)
        top_match = re.search(r'top:(\d+)px', style)
        
        if left_match and top_match:
            left = int(left_match.group(1))
            top = int(top_match.group(1))
            
            # 函数名通常在右侧（left > 400）且是单个单词
            if left > 400 and re.match(r'^[A-Za-z][a-zA-Z0-9]+$', text):
                function_name = text
                function_top = top
                break
    
    if not function_name:
        return api_list
    
    # 创建API信息结构
    api_info = {
        "function_name": function_name,
        "syntax": "",
        "description": "",
        "parameters": [],
        "returns": "",
        "availability": "",
        "observation": "",
        "branch_compatibility": {},
        "related_functions": []
    }
    
    # 按top位置分组，查找各个section
    sections = {}
    section_markers = {
        'Syntax': 'syntax',
        'Description': 'description',
        'Parameter': 'parameters',
        'Returns': 'returns',
        'Availability': 'availability',
        'Observation': 'observation',
        'Branch Compatibility': 'branch_compatibility',
        'Related Functions': 'related_functions'
    }
    
    # 收集所有段落并按top排序
    paragraphs = []
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        style = p.get('style', '')
        
        left_match = re.search(r'left:(\d+)px', style)
        top_match = re.search(r'top:(\d+)px', style)
        
        if left_match and top_match:
            left = int(left_match.group(1))
            top = int(top_match.group(1))
            
            # 跳过函数名本身
            if text == function_name and left > 400:
                continue
                
            paragraphs.append({
                'text': text,
                'left': left,
                'top': top,
                'element': p
            })
    
    # 按top位置排序
    paragraphs.sort(key=lambda x: x['top'])
    
    # 查找section标题和内容
    current_section = None
    section_content = []
    
    for para in paragraphs:
        text = para['text']
        left = para['left']
        top = para['top']
        
        # 检查是否是section标题
        found_section = None
        for marker, section_key in section_markers.items():
            # 更精确的匹配section标题，避免误匹配
            if (marker.lower() in text.lower() and 
                left < 200 and 
                len(text) <= len(marker) + 5):  # 允许少量额外字符
                if current_section:
                    # 保存前一个section的内容
                    content = " ".join(section_content).strip()
                    if content:
                        save_section_content(api_info, current_section, [content])
                
                current_section = section_key
                section_content = []
                found_section = True
                break
        
        if not found_section and current_section and left > 150:  # 内容通常在右侧
            section_content.append(text)
    
    # 保存最后一个section
    if current_section and section_content:
        content = " ".join(section_content).strip()
        if content:
            save_section_content(api_info, current_section, [content])
    
    api_list.append(api_info)
    return api_list

def extract_availability_chart(soup, page_number):
    """
    从Availability Chart页面提取函数列表
    
    参数:
        soup: BeautifulSoup对象
        page_number: 页码
    
    返回:
        list: 函数基本信息列表
    """
    api_list = []
    
    # 查找所有段落
    all_paragraphs = soup.find_all('p')
    
    # 按top位置排序，确保按行处理
    paragraph_data = []
    for p in all_paragraphs:
        text = p.get_text().strip()
        style = p.get('style', '')
        
        if not text or text in ['Availability Chart', '']:
            continue
            
        # 提取left和top位置
        left_match = re.search(r'left:(\d+)px', style)
        top_match = re.search(r'top:(\d+)px', style)
        
        if not left_match or not top_match:
            continue
            
        left = int(left_match.group(1))
        top = int(top_match.group(1))
        
        paragraph_data.append({
            'element': p,
            'text': text,
            'left': left,
            'top': top
        })
    
    # 按top位置分组
    lines = {}
    for data in paragraph_data:
        top = data['top']
        if top not in lines:
            lines[top] = []
        lines[top].append(data)
    
    # 处理每一行
    for top, items in lines.items():
        if top <= 100:  # 跳过标题区域
            continue
            
        # 按left位置排序
        items.sort(key=lambda x: x['left'])
        
        # 查找函数名（通常是第一个有效项，且不是"All"等）
        function_name = None
        for item in items:
            text = item['text']
            left = item['left']
            
            # 函数名通常在左侧，且符合驼峰命名
            if left < 300 and re.match(r'^[A-Za-z][a-zA-Z0-9]*$', text):
                # 排除常见的非函数名
                if text not in ['All', 'Prior', 'O', 'S', 'and', 'after']:
                    function_name = text
                    break
        
        if function_name:
            # 收集该行的其他信息作为可用性
            availability_parts = []
            for item in items:
                if item['text'] != function_name and item['left'] > 300:
                    availability_parts.append(item['text'])
            
            availability = ' '.join(availability_parts).strip()
            
            api_info = {
                "function_name": function_name,
                "syntax": f"{function_name}()",
                "description": f"CAPL函数 {function_name}",
                "parameters": [],
                "returns": "",
                "availability": availability,
                "observation": "",
                "branch_compatibility": {},
                "related_functions": []
            }
            api_list.append(api_info)
    
    return api_list

def extract_function_details(soup, function_name, function_heading):
    """
    提取特定函数的详细信息
    
    参数:
        soup: BeautifulSoup对象
        function_name: 函数名
        function_heading: 函数名的HTML元素
    
    返回:
        dict: 函数详细信息
    """
    api_info = {
        "function_name": function_name,
        "syntax": "",
        "description": "",
        "parameters": [],
        "returns": "",
        "availability": "",
        "observation": "",
        "branch_compatibility": {},
        "related_functions": []
    }
    
    # 获取函数标题的top位置
    style = function_heading.get('style', '')
    top_match = re.search(r'top:(\d+)px', style)
    if not top_match:
        return None
    
    function_top = int(top_match.group(1))
    
    # 查找所有段落
    all_paragraphs = soup.find_all('p')
    
    # 找到函数标题之后的段落
    start_index = 0
    for i, p in enumerate(all_paragraphs):
        if p == function_heading:
            start_index = i + 1
            break
    
    if start_index == 0:
        return None
    
    # 收集函数相关信息
    current_section = None
    current_text = []
    
    for i in range(start_index, len(all_paragraphs)):
        p = all_paragraphs[i]
        text = p.get_text().strip()
        if not text:
            continue
            
        style = p.get('style', '')
        top_match = re.search(r'top:(\d+)px', style)
        left_match = re.search(r'left:(\d+)px', style)
        
        if not top_match or not left_match:
            continue
            
        top = int(top_match.group(1))
        left = int(left_match.group(1))
        
        # 如果距离太远，可能是下一个函数
        if top - function_top > 800:
            break
            
        # 检查是否是新的section
        section_markers = {
            'Syntax': 'syntax',
            'Description': 'description',
            'Parameter': 'parameters',
            'Returns': 'returns',
            'Availability': 'availability',
            'Observation': 'observation',
            'Branch Compatibility': 'branch_compatibility',
            'Related Functions': 'related_functions'
        }
        
        found_section = False
        for marker, section in section_markers.items():
            if marker in text and left < 200:
                # 保存前一个section的内容
                if current_section and current_text:
                    save_section_content(api_info, current_section, current_text)
                
                current_section = section
                current_text = [text.replace(marker + ':', '').strip()]
                found_section = True
                break
        
        if not found_section and current_section:
            # 收集当前section的内容
            if left > 150:  # 内容通常比标题更靠右
                current_text.append(text)
    
    # 保存最后一个section
    if current_section and current_text:
        save_section_content(api_info, current_section, current_text)
    
    return api_info

def save_section_content(api_info, section, text_list):
    """
    保存section的内容到api_info
    """
    content = " ".join(text_list).strip()
    
    if section == 'syntax':
        # 清理语法格式
        syntax = content.replace('\n', ' ').strip()
        # 提取函数签名
        func_sig_match = re.search(r'(\w+\s+)?(\w+\s*\([^)]*\))', syntax)
        if func_sig_match:
            api_info['syntax'] = func_sig_match.group(2)
        else:
            api_info['syntax'] = syntax
            
    elif section == 'description':
        api_info['description'] = content
        
    elif section == 'parameters':
        # 解析参数
        params = parse_parameters(content)
        api_info['parameters'] = params
        
    elif section == 'returns':
        api_info['returns'] = content
        
    elif section == 'availability':
        api_info['availability'] = content
        
    elif section == 'observation':
        api_info['observation'] = content
        
    elif section == 'branch_compatibility':
        # 解析分支兼容性
        compatibility = parse_branch_compatibility(content)
        api_info['branch_compatibility'] = compatibility
        
    elif section == 'related_functions':
            # 解析相关函数，只保留真正的函数名
            lines = [line.strip() for line in content.split('\n') if line.strip() and line.strip() != 'N/A']
            valid_functions = []
            for line in lines:
                if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', line.strip()):
                    valid_functions.append(line.strip())
            api_info['related_functions'] = valid_functions

def parse_parameters(content):
    """
    解析参数字符串为结构化数据
    """
    parameters = []
    
    # 清理内容
    content = content.replace('=', ' = ')
    
    # 分割参数
    param_parts = re.split(r'[,;]\s*', content)
    
    for part in param_parts:
        if not part.strip():
            continue
            
        # 匹配参数格式：类型 名称 = 描述
        match = re.match(r'(\w+(?:\s*\[\s*\])?)\s+(\w+)\s*=\s*(.+)', part.strip())
        if match:
            param_type, param_name, param_desc = match.groups()
            parameters.append({
                "name": param_name,
                "type": param_type,
                "description": param_desc
            })
        else:
            # 尝试匹配简单格式：名称 = 描述
            match = re.match(r'(\w+)\s*=\s*(.+)', part.strip())
            if match:
                param_name, param_desc = match.groups()
                parameters.append({
                    "name": param_name,
                    "type": "unknown",
                    "description": param_desc
                })
            else:
                # 作为整体描述
                parameters.append({
                    "name": "unknown",
                    "type": "unknown",
                    "description": part.strip()
                })
    
    return parameters

def parse_branch_compatibility(content):
    """
    解析分支兼容性信息
    """
    compatibility = {}
    
    # 查找分支信息
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if '=' in line:
            parts = line.split('=')
            if len(parts) == 2:
                branch = parts[0].strip()
                status = parts[1].strip()
                compatibility[branch] = status
    
    return compatibility

def parse_related_functions(content):
    """
    解析相关函数列表
    """
    functions = []
    
    # 分割函数名
    func_names = re.split(r'[,\s]+', content)
    for name in func_names:
        name = name.strip()
        if name and name != '':
            functions.append(name)
    
    return functions

def process_html_files(input_dir, output_dir):
    """
    处理目录中的所有HTML文件
    
    参数:
        input_dir: 输入目录路径
        output_dir: 输出目录路径
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_apis = []
    
    # 获取所有HTML文件
    html_files = list(input_path.glob('*.html'))
    html_files.sort(key=lambda x: int(re.search(r'(\d+)', x.stem).group(1)) if re.search(r'(\d+)', x.stem) else 0)
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            print(f"处理文件: {html_file.name}")
            
            # 提取API信息
            apis = extract_api_from_html(html_content, html_file.stem)
            
            if apis:
                # 保存单个文件的API信息
                output_file = output_path / f"apis_{html_file.stem}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(apis, f, ensure_ascii=False, indent=2)
                
                all_apis.extend(apis)
                print(f"  提取了 {len(apis)} 个API")
            
        except Exception as e:
            print(f"处理文件 {html_file.name} 时出错: {e}")
    
    # 保存所有API信息的汇总文件
    if all_apis:
        summary_file = output_path / "all_apis.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(all_apis, f, ensure_ascii=False, indent=2)
        
        print(f"\n总计提取了 {len(all_apis)} 个API")
        print(f"所有API信息已保存到: {summary_file}")

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='从CAPL HTML文档中提取API信息')
    parser.add_argument('input_dir', help='输入HTML文件目录')
    parser.add_argument('output_dir', help='输出JSON文件目录')
    
    args = parser.parse_args()
    
    process_html_files(args.input_dir, args.output_dir)

if __name__ == "__main__":
    main()