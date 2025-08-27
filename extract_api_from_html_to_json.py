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
        # 跳过Availability Chart页面，不处理
        return []
    
    # 查找函数名 - 以粗体显示在页面右侧
    function_name = None
    function_heading = None
    
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
                function_heading = p
                break
    
    if not function_name or not function_heading:
        return api_list
    
    # 使用extract_function_details提取详细信息，支持重载函数
    function_details = extract_function_details(soup, function_name, function_heading)
    api_list.extend(function_details)
    return api_list



def extract_function_details(soup, function_name, function_heading):
    """
    提取特定函数的详细信息
    
    参数:
        soup: BeautifulSoup对象
        function_name: 函数名
        function_heading: 函数名的HTML元素
    
    返回:
        list: 函数详细信息列表（支持重载函数）
    """
    api_list = []
    
    # 获取函数标题的top位置
    style = function_heading.get('style', '')
    top_match = re.search(r'top:(\d+)px', style)
    if not top_match:
        return api_list
    
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
        return api_list
    
    # 收集函数相关信息
    current_section = None
    current_text = []
    
    # 存储所有section的内容
    sections_content = {}
    
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
                    sections_content[current_section] = current_text
                
                current_section = section
                current_text = []  # 不将标题行加入内容
                found_section = True
                break
        
        if not found_section and current_section:
            # 收集当前section的内容
            if left > 150:  # 内容通常比标题更靠右
                current_text.append(text)
    
    # 保存最后一个section
    if current_section and current_text:
        sections_content[current_section] = current_text
    
    # 处理syntax section，提取重载函数
    syntax_content = " ".join(sections_content.get('syntax', [])).strip()
    func_sig_matches = re.findall(r'\w+\s+\w+\s*\([^)]*\)', syntax_content)
    
    if not func_sig_matches:
        # 如果没有找到函数签名，创建一个默认的API条目
        api_info = {
                "function_name": function_name,
                "syntax": f"{function_name}()",
                "description": "",
                "parameters": [],
                "returns": "",
                "availability": "",
                "observation": "",
                "branch_compatibility": {}
            }
        
        # 填充其他section的内容
        for section, content_list in sections_content.items():
            if section != 'syntax':
                content = " ".join(content_list).strip()
                if section == 'parameters':
                    api_info[section] = parse_parameters(content)
                elif section == 'branch_compatibility':
                    api_info[section] = parse_branch_compatibility(content)
                elif section == 'related_functions':
                    api_info[section] = parse_related_functions(content)
                elif section == 'description':
                    # 去掉Description前缀
                    description = re.sub(r'^\s*[Dd]escription\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
                    api_info[section] = description
                elif section == 'returns':
                    # 去掉Returns前缀
                    returns = re.sub(r'^\s*[Rr]eturns?\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
                    api_info[section] = returns
                elif section == 'availability':
                    # 去掉Availability前缀
                    availability = re.sub(r'^\s*[Aa]vailability\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
                    api_info[section] = availability
                elif section == 'observation':
                    # 去掉Observation前缀
                    observation = re.sub(r'^\s*[Oo]bservation\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
                    api_info[section] = observation
                else:
                    api_info[section] = content
        
        api_list.append(api_info)
    else:
        # 为每个重载函数创建单独的API条目
            for i, signature in enumerate(func_sig_matches):
                api_info = {
                    "function_name": function_name,
                    "syntax": signature,
                    "description": "",
                    "parameters": [],
                    "returns": "",
                    "availability": "",
                    "observation": "",
                    "branch_compatibility": {}
                }
            
            # 填充其他section的内容
            for section, content_list in sections_content.items():
                if section != 'syntax' and section != 'related_functions':
                    content = " ".join(content_list).strip()
                    if section == 'parameters':
                        api_info[section] = parse_parameters(content)
                    elif section == 'branch_compatibility':
                        api_info[section] = parse_branch_compatibility(content)
                    elif section == 'description':
                        # 去掉Description前缀
                        description = content.replace('Description:', '').replace('Description', '').strip()
                        api_info[section] = description
                    else:
                        api_info[section] = content
            
            api_list.append(api_info)
    
    return api_list

def save_section_content(api_info, section, text_list):
    """
    保存section的内容到api_info
    """
    content = " ".join(text_list).strip()
    
    if section == 'syntax':
        # 清理语法格式
        syntax = content.replace('\n', ' ').strip()
        # 提取所有函数签名，支持重载函数
        # 匹配格式：返回类型 函数名(参数列表)
        func_sig_matches = re.findall(r'\w+\s+\w+\s*\([^)]*\)', syntax)
        if func_sig_matches:
            if len(func_sig_matches) == 1:
                api_info['syntax'] = func_sig_matches[0]
            else:
                # 如果有多个函数签名（重载），创建多个API条目
                api_info['syntax'] = func_sig_matches[0]
                # 保存额外的重载函数供后续处理
                api_info['overloads'] = func_sig_matches[1:]
            
    elif section == 'description':
        # 去掉Description前缀
        description = re.sub(r'^\s*[Dd]escription\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
        api_info['description'] = description
        
    elif section == 'parameters':
        # 解析参数
        params = parse_parameters(content)
        api_info['parameters'] = params
        
    elif section == 'returns':
        # 去掉Returns前缀
        returns = re.sub(r'^\s*[Rr]eturns?\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
        api_info['returns'] = returns
        
    elif section == 'availability':
        # 去掉Availability前缀
        availability = re.sub(r'^\s*[Aa]vailability\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
        api_info['availability'] = availability
        
    elif section == 'observation':
        # 去掉Observation前缀
        observation = re.sub(r'^\s*[Oo]bservation\s*[:\-]?\s*', '', content, flags=re.IGNORECASE).strip()
        api_info['observation'] = observation
        
    elif section == 'branch_compatibility':
        # 解析分支兼容性
        compatibility = parse_branch_compatibility(content)
        api_info['branch_compatibility'] = compatibility
        


def parse_parameters(content):
    """
    解析参数字符串为结构化数据
    格式：参数名称 = 参数描述
    根据HTML中的格式，参数是以<br/>分隔的，每行都是"参数名 = 描述"格式
    例如：
    section = section within file
    entry = name of variable
    def = float value to write
    file = name of file
    """
    parameters = []
    
    # 清理内容
    content = content.strip()
    if not content:
        return parameters
    
    # 移除"Parameter"或"Parameters"前缀
    content = re.sub(r'^\s*parameters?\s*[:\-]?\s*', '', content, flags=re.IGNORECASE)
    
    # 首先清理HTML标签
    content = re.sub(r'<[^>]+>', '', content)
    
    # 使用正则表达式查找所有 "参数名 = 描述" 的匹配
    # 匹配模式：参数名 = 描述（直到下一个参数开始或行尾）
    pattern = r'([a-zA-Z_]\w*)\s*=\s*([^=]*?)(?=(?:\s+[a-zA-Z_]\w*\s*=)|\n|$)'
    matches = re.findall(pattern, content, re.IGNORECASE)
    
    # 如果没有找到匹配，尝试另一种模式
    if not matches:
        # 按行分割，每行一个参数
        lines = re.split(r'\n|\r\n', content)
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 匹配参数格式：名称 = 描述
            match = re.match(r'^([^=]+)\s*=\s*(.+)$', line)
            if match:
                matches.append((match.group(1).strip(), match.group(2).strip()))
    
    # 处理找到的参数
    for param_name, param_desc in matches:
        param_name = param_name.strip()
        param_desc = param_desc.strip()
        
        # 清理参数名 - 移除前面的类型声明和修饰符
        # 例如："char section[]" -> "section"
        
        # 1. 移除类型关键字
        param_name = re.sub(r'^(?:char|long|float|int|dword|void|double|short|byte)\s+', '', param_name)
        
        # 2. 移除数组符号 [] 和指针符号 *
        param_name = re.sub(r'\[\s*\]', '', param_name)  # 移除[]
        param_name = re.sub(r'\*', '', param_name)  # 移除*
        
        # 3. 清理空格
        param_name = re.sub(r'\s+', ' ', param_name).strip()
        
        # 4. 确保参数名只包含有效字符
        param_name = re.sub(r'[^a-zA-Z0-9_]', '', param_name)
        
        # 清理参数描述
        param_desc = re.sub(r'\s+', ' ', param_desc).strip()
        
        if param_name and len(param_name) <= 30:  # 合理的参数名长度限制
            parameters.append({
                "name": param_name,
                "description": param_desc
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