import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

def extract_test_script_from_html(html_content, page_number):
    """
    从HTML内容中提取测试脚本步骤
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    test_script = []
    
    # 查找所有段落
    all_paragraphs = soup.find_all('p')
    
    # 查找步骤开始的标记
    step_start_index = None
    for i, p in enumerate(all_paragraphs):
        text = p.get_text().strip()
        style = p.get('style', '')
        left_match = re.search(r'left:(\d+)px', style)
        left_pos = int(left_match.group(1)) if left_match else 0
        
        # 查找"Step Action"或"Step"作为开始标记
        if 'Step Action' in text or ('Step' in text and left_pos < 200):
            step_start_index = i
            break
        # 或者查找数字开头的步骤
        elif re.match(r'\d+', text) and left_pos < 200:
            step_start_index = i
            break
    
    if step_start_index is None:
        # 如果没有找到明确的开始标记，尝试从包含步骤格式的段落开始
        for i, p in enumerate(all_paragraphs):
            text = p.get_text().strip()
            if re.match(r'\d+\s+Read DID', text):
                step_start_index = i
                break
    
    if step_start_index is None:
        return test_script
    
    # 从步骤开始处处理
    paragraphs_to_process = all_paragraphs[step_start_index:]
    
    # 处理步骤
    current_step = None
    for p in paragraphs_to_process:
        text = p.get_text().strip()
        if not text:
            continue
        
        style = p.get('style', '')
        left_match = re.search(r'left:(\d+)px', style)
        left_pos = int(left_match.group(1)) if left_match else 0
        top_match = re.search(r'top:(\d+)px', style)
        top_pos = int(top_match.group(1)) if top_match else 0
        
        # 查找步骤数字
        step_match = re.match(r'(\d+)', text)
        if step_match and left_pos < 200:
            # 保存前一个步骤
            if current_step and (current_step["action"] or current_step["expected_result"]):
                test_script.append(current_step)
            
            # 创建新步骤
            current_step = {
                "step": step_match.group(1),
                "action": text[len(step_match.group(1)):].strip(),
                "expected_result": ""
            }
        elif current_step:
            # 收集动作和预期结果
            if left_pos < 300:  # 动作区域
                if current_step["action"]:
                    current_step["action"] += " " + text
                else:
                    current_step["action"] = text
            else:  # 预期结果区域
                if current_step["expected_result"]:
                    current_step["expected_result"] += " " + text
                else:
                    current_step["expected_result"] = text
    
    # 添加最后一个步骤
    if current_step and (current_step["action"] or current_step["expected_result"]):
        test_script.append(current_step)
    
    return test_script

def has_test_script_only(html_content):
    """
    检查页面是否只包含测试脚本（没有测试用例标题）
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    # 检查是否有测试用例标题 - 严格匹配格式
    has_test_case = bool(re.search(r'\d+(\.\d+)*\s+Test case\s*[:\s].*\(Ver:\s*\d+\)', text))
    
    # 检查是否有测试脚本 - 查找步骤格式
    has_script = bool(re.search(r'Step\s+Action', text, re.IGNORECASE)) or \
                   bool(re.search(r'\d+\s+Read DID', text, re.IGNORECASE)) or \
                   bool(re.search(r'\d+\s+[A-Z][a-z]', text))
    
    return has_script and not has_test_case

def extract_test_cases_from_html(html_content, page_number, include_requirements=False):
    """
    从HTML内容中提取测试用例信息
    
    参数:
        html_content: HTML内容
        page_number: 页码
        include_requirements: 是否包含requirements字段，默认为False
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有包含"Test case"的标题
    test_case_headers = []
    
    # 查找所有可能包含测试用例的标题
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            text = heading.get_text().strip()
            # 只匹配真正的测试用例标题格式：数字+Test case+版本号
            if re.match(r'\d+(\.\d+)*\s+Test case\s*[:\s].*\(Ver:\s*\d+\)', text):
                test_case_headers.append(heading)
    
    # 在HTML中查找包含"Test case"的段落作为标题
    for p in soup.find_all('p'):
        text = p.get_text().strip()
        # 严格匹配测试用例标题格式：数字+Test case+描述+(Ver: 数字)
        if re.match(r'\d+(\.\d+)*\s+Test case\s*[:\s].*\(Ver:\s*\d+\)', text):
            test_case_headers.append(p)
    
    test_cases = []
    
    for header in test_case_headers:
        test_case = {
            "page_number": page_number,
            "title": header.get_text().strip(),
            "test_case_id": "",
            "legacy_id": "",
            "purpose": "",
            "precondition": "",
            "description": "",
            "requirements": [],
            "test_script": []
        }
        
        # 查找测试用例ID
        # 查找所有段落，寻找测试用例相关信息
        all_paragraphs = soup.find_all('p')
        for i, p in enumerate(all_paragraphs):
            text = p.get_text().strip()
            
            # 查找测试用例ID
            if 'Test Case ID:' in text:
                id_match = re.search(r'Test Case ID:\s*(\d+)', text)
                if id_match:
                    test_case["test_case_id"] = id_match.group(1)
                else:
                    # 如果没有在当前段落找到ID，检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        id_match = re.search(r'(\d+)', next_text)
                        if id_match:
                            test_case["test_case_id"] = id_match.group(1)
            
            # 查找Legacy ID
            if 'Legacy ID:' in text:
                # Legacy ID可能在下一行
                legacy_match = re.search(r'Legacy ID:\s*(\S+)', text)
                if not legacy_match:
                    # 检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        if next_text and not next_text.startswith(('Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script')):
                            test_case["legacy_id"] = next_text
                else:
                    test_case["legacy_id"] = legacy_match.group(1)
            
            # 查找Purpose
            if 'Purpose:' in text:
                purpose_match = re.search(r'Purpose:\s*(.*)', text, re.DOTALL)
                if purpose_match and purpose_match.group(1).strip():
                    test_case["purpose"] = purpose_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到Purpose，检查后续段落直到遇到其他标记
                    j = i + 1
                    purpose_lines = []
                    while j < len(all_paragraphs):
                        next_text = all_paragraphs[j].get_text().strip()
                        if not next_text:
                            j += 1
                            continue
                            
                        # 检查是否遇到其他标记，但允许以·开头的文本
                        is_other_marker = False
                        for marker in ['Test', 'PreCondition', 'Description', 'Requirements', 'Test Script', 'PostCondition']:
                            if next_text.startswith(marker) and not next_text.startswith('·'):
                                is_other_marker = True
                                break
                        
                        if is_other_marker:
                            break
                            
                        # 收集Purpose文本，包括以·开头的
                        purpose_lines.append(next_text)
                        j += 1
                    
                    if purpose_lines:
                        # 清理Purpose文本，移除开头的·和多余的空格
                        cleaned_lines = []
                        for line in purpose_lines:
                            line = line.strip()
                            if line.startswith('·'):
                                line = line[1:].strip()
                            if line:
                                cleaned_lines.append(line)
                        test_case["purpose"] = " ".join(cleaned_lines)
            
            # 查找PreCondition
            if 'PreCondition:' in text:
                precondition_match = re.search(r'PreCondition:\s*(.*)', text, re.DOTALL)
                if precondition_match and precondition_match.group(1).strip():
                    test_case["precondition"] = precondition_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到PreCondition，检查后续段落直到遇到其他标记
                    j = i + 1
                    precondition_lines = []
                    while j < len(all_paragraphs):
                        next_text = all_paragraphs[j].get_text().strip()
                        if not next_text:
                            j += 1
                            continue
                            
                        # 检查是否遇到其他标记，但允许以·开头的文本
                        is_other_marker = False
                        for marker in ['Test', 'Purpose', 'Description', 'Requirements', 'Test Script', 'PostCondition']:
                            if next_text.startswith(marker) and not next_text.startswith('·'):
                                is_other_marker = True
                                break
                        
                        if is_other_marker:
                            break
                            
                        # 收集PreCondition文本，包括以·开头的
                        precondition_lines.append(next_text)
                        j += 1
                    
                    if precondition_lines:
                        # 清理PreCondition文本，移除开头的·和多余的空格
                        cleaned_lines = []
                        for line in precondition_lines:
                            line = line.strip()
                            if line.startswith('·'):
                                line = line[1:].strip()
                            if line:
                                cleaned_lines.append(line)
                        test_case["precondition"] = " ".join(cleaned_lines)
            
            # 查找PostCondition
            if 'PostCondition:' in text:
                postcondition_match = re.search(r'PostCondition:\s*(.*)', text, re.DOTALL)
                if postcondition_match and postcondition_match.group(1).strip():
                    test_case["postcondition"] = postcondition_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到PostCondition，检查后续段落直到遇到其他标记
                    j = i + 1
                    postcondition_lines = []
                    while j < len(all_paragraphs):
                        next_text = all_paragraphs[j].get_text().strip()
                        if not next_text:
                            j += 1
                            continue
                            
                        # 检查是否遇到其他标记，但允许以·开头的文本
                        is_other_marker = False
                        for marker in ['Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script']:
                            if next_text.startswith(marker) and not next_text.startswith('·'):
                                is_other_marker = True
                                break
                        
                        if is_other_marker:
                            break
                            
                        # 收集PostCondition文本，包括以·开头的
                        postcondition_lines.append(next_text)
                        j += 1
                    
                    if postcondition_lines:
                        # 清理PostCondition文本，移除开头的·和多余的空格
                        cleaned_lines = []
                        for line in postcondition_lines:
                            line = line.strip()
                            if line.startswith('·'):
                                line = line[1:].strip()
                            if line:
                                cleaned_lines.append(line)
                        test_case["postcondition"] = " ".join(cleaned_lines)
            
            # 查找Description
            if 'Description:' in text or 'Test case Description:' in text:
                description_match = re.search(r'(Test case )?Description:\s*(.*)', text, re.DOTALL)
                if description_match and description_match.group(2).strip():
                    test_case["description"] = description_match.group(2).strip()
                else:
                    # 如果没有在当前段落找到Description，检查后续段落直到遇到其他标记
                    j = i + 1
                    description_lines = []
                    while j < len(all_paragraphs):
                        next_text = all_paragraphs[j].get_text().strip()
                        if not next_text:
                            j += 1
                            continue
                            
                        # 检查是否遇到其他标记，但允许以·开头的描述文本
                        is_other_marker = False
                        for marker in ['Test', 'Purpose', 'PreCondition', 'Requirements', 'Test Script', 'PostCondition']:
                            if next_text.startswith(marker) and not next_text.startswith('·'):
                                is_other_marker = True
                                break
                        
                        if is_other_marker:
                            break
                            
                        # 收集描述文本，包括以·开头的
                        description_lines.append(next_text)
                        j += 1
                    
                    if description_lines:
                        # 清理描述文本，移除开头的·和多余的空格
                        cleaned_lines = []
                        for line in description_lines:
                            line = line.strip()
                            if line.startswith('·'):
                                line = line[1:].strip()
                            if line:
                                cleaned_lines.append(line)
                        test_case["description"] = " ".join(cleaned_lines)
            
            # 查找需求表格 - 仅在include_requirements为True时处理
            if 'Requirements:' in text and include_requirements:
                # 需求信息在后续段落中
                next_elements = all_paragraphs[i+1:]
                # 查找需求信息的结束标记
                end_markers = ['Test Script Description', 'Test Script', 'Step Action']
                
                # 收集所有段落，按top值排序来模拟表格行
                requirement_data = []
                
                # 首先收集所有带有样式的段落
                for j, next_p in enumerate(next_elements):
                    next_text = next_p.get_text().strip()
                    if not next_text:
                        continue
                    
                    # 检查是否到达结束标记
                    if any(marker in next_text for marker in end_markers):
                        break
                    
                    # 获取元素的样式属性用于定位
                    style = next_p.get('style', '')
                    top_match = re.search(r'top:(\d+)px', style)
                    left_match = re.search(r'left:(\d+)px', style)
                    
                    if top_match and left_match:
                        top = int(top_match.group(1))
                        left = int(left_match.group(1))
                        
                        # 排除表头行
                        if 'Requirement' in next_text and 'Req ID' in next_text:
                            continue
                        
                        # 收集所有非空的文本
                        if next_text and next_text != 'Requirement':
                            requirement_data.append({
                                'text': next_text,
                                'top': top,
                                'left': left
                            })
                
                # 按top值分组，同一行的元素top值相近
                if requirement_data:
                    rows = {}
                    for item in requirement_data:
                        # 找到相近的top值组（允许15px误差）
                        row_key = None
                        for key in rows.keys():
                            if abs(key - item['top']) <= 15:
                                row_key = key
                                break
                        
                        if row_key is None:
                            row_key = item['top']
                            rows[row_key] = []
                        
                        rows[row_key].append(item)
                    
                    # 处理每一行数据
                    for top_value in sorted(rows.keys()):
                        row_items = rows[top_value]
                        # 按left值排序来识别列
                        row_items.sort(key=lambda x: x['left'])
                        
                        # 提取列数据
                        columns = [item['text'] for item in row_items]
                        
                        # 跳过表头行（包含"Requirement"和"Req ID"的行）
                        is_header = False
                        for col in columns:
                            if 'Requirement' in col and 'Req ID' in col:
                                is_header = True
                                break
                            elif 'Req ID' in col and 'Ver' in col:
                                is_header = True
                                break
                        
                        if is_header:
                            continue
                        
                        # 跳过完全匹配表头文本的行
                        if len(columns) >= 2 and columns[0] == "Requirement" and columns[1] == "Req ID":
                            continue
                        
                        # 根据列数和位置判断数据结构
                        if len(columns) >= 4:
                            # 标准的4列数据：Requirement, Req ID, Ver, Status
                            requirement = {
                                "requirement": columns[0],
                                "req_id": columns[1],
                                "ver": columns[2] if len(columns) > 2 else "",
                                "status": columns[3] if len(columns) > 3 else ""
                            }
                            test_case["requirements"].append(requirement)
                        elif len(columns) == 3:
                            # 3列数据：Requirement, Req ID, Ver
                            requirement = {
                                "requirement": columns[0],
                                "req_id": columns[1],
                                "ver": columns[2],
                                "status": ""
                            }
                            test_case["requirements"].append(requirement)
                        elif len(columns) == 2:
                            # 2列数据：Requirement, Req ID
                            requirement = {
                                "requirement": columns[0],
                                "req_id": columns[1],
                                "ver": "",
                                "status": ""
                            }
                            test_case["requirements"].append(requirement)
                        elif len(columns) == 1 and columns[0] and not columns[0].startswith('Test'):
                            # 单列数据：只有Requirement
                            requirement = {
                                "requirement": columns[0],
                                "req_id": "",
                                "ver": "",
                                "status": ""
                            }
                            test_case["requirements"].append(requirement)
            
            # 查找测试脚本描述
            if 'Test Script Description' in text:
                # 测试脚本信息在后续段落中
                next_elements = all_paragraphs[i+1:]
                # 查找测试脚本信息的结束标记
                end_markers = ['Test Case ID:', 'PreCondition:', 'Purpose:', 'Description:', 'Requirements:']
                
                # 用于存储测试步骤的临时列表
                step_elements = []
                
                # 收集测试步骤元素
                for next_p in next_elements:
                    next_text = next_p.get_text().strip()
                    
                    # 检查是否到达结束标记
                    if any(marker in next_text for marker in end_markers):
                        break
                    
                    # 跳过表头行
                    if 'Step' in next_text and 'Action' in next_text and 'Expected Result' in next_text:
                        continue
                    
                    # 跳过空文本
                    if not next_text:
                        continue
                    
                    # 获取元素的top和left样式属性
                    style = next_p.get('style', '')
                    top_match = re.search(r'top:(\d+)px', style)
                    left_match = re.search(r'left:(\d+)px', style)
                    top = int(top_match.group(1)) if top_match else 0
                    left = int(left_match.group(1)) if left_match else 0
                    
                    step_elements.append({
                        'text': next_text,
                        'top': top,
                        'left': left,
                        'element': next_p
                    })
                
                # 按top值分组，同一行的元素top值相近
                step_groups = {}
                for element in step_elements:
                    # 找到相近的top值组
                    group_key = None
                    for key in step_groups.keys():
                        if abs(key - element['top']) <= 15:  # 允许15px的误差
                            group_key = key
                            break
                    
                    if group_key is None:
                        group_key = element['top']
                        step_groups[group_key] = []
                    
                    step_groups[group_key].append(element)
                
                # 处理每个组，构建测试步骤
                for top_value in sorted(step_groups.keys()):
                    group = step_groups[top_value]
                    # 按left值排序
                    group.sort(key=lambda x: x['left'])
                    
                    # 识别步骤号、动作和预期结果
                    if len(group) >= 1:
                        # 检查第一个元素是否是步骤号
                        first_element = group[0]
                        step_number_match = re.match(r'^\d+\s*$', first_element['text'])
                        
                        if step_number_match:
                            # 确实是步骤号
                            step_number = first_element['text'].strip()
                            step = {
                                "step": step_number,
                                "action": "",
                                "expected_result": ""
                            }
                            
                            # 处理动作和预期结果
                            action_parts = []
                            expected_result_parts = []
                            
                            for element in group[1:]:
                                if element['left'] < 250:  # 动作区域 (left < 250)
                                    action_parts.append(element['text'])
                                else:  # 预期结果区域 (left >= 250)
                                    expected_result_parts.append(element['text'])
                            
                            step["action"] = " ".join(action_parts)
                            step["expected_result"] = " ".join(expected_result_parts)
                            
                            test_case["test_script"].append(step)
                        else:
                            # 不是步骤号，可能是跨行的动作或预期结果描述
                            # 检查这些文本应该属于动作还是预期结果区域
                            for element in group:
                                if element['left'] < 250:  # 动作区域
                                    if test_case["test_script"]:
                                        # 添加到上一个步骤的动作中
                                        test_case["test_script"][-1]["action"] += " " + element['text']
                                else:  # 预期结果区域
                                    if test_case["test_script"]:
                                        # 添加到上一个步骤的预期结果中
                                        test_case["test_script"][-1]["expected_result"] += " " + element['text']
        
        # 只有当测试用例有ID时才添加到结果中
        if test_case["test_case_id"]:
            test_cases.append(test_case)
        else:
            # 添加调试信息
            print(f"Test case without ID found on page {page_number}: {test_case['title']}")
            # 如果标题包含"Test case"，但没有ID，也添加到结果中
            if "Test case" in test_case["title"]:
                # 处理累积的动作文本（即使没有ID）
                if '_pending_action_parts' in test_case and test_case['_pending_action_parts']:
                    if test_case["test_script"]:
                        # 将累积的文本添加到上一个步骤的动作中
                        test_case["test_script"][-1]["action"] += " " + " ".join(test_case['_pending_action_parts']).strip()
                    # 清除暂存的文本
                    del test_case['_pending_action_parts']
                test_cases.append(test_case)
    
    return test_cases

def process_html_files(input_dir, output_dir):
    """
    处理目录中的所有HTML文件，提取测试用例并保存为JSON文件
    支持跨页的测试用例分析
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取所有HTML文件并按编号排序
    html_files = list(Path(input_dir).glob("*.html"))
    html_files.sort(key=lambda x: int(re.search(r'CC_DVM-(\d+)\.html', x.name).group(1)) if re.search(r'CC_DVM-(\d+)\.html', x.name) else 0)
    
    all_test_cases = []
    
    # 用于跟踪跨页的测试用例
    pending_test_cases = {}
    pending_test_scripts = {}  # 用于存储测试脚本，按test_case_id索引
    
    for html_file in html_files:
        print(f"Processing {html_file.name}...")
        
        # 提取页码
        page_match = re.search(r'CC_DVM-(\d+)\.html', html_file.name)
        if page_match:
            page_number = int(page_match.group(1))
        else:
            page_number = 0
        
        # 读取HTML文件
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 提取测试用例（默认不包含requirements字段）
        test_cases = extract_test_cases_from_html(html_content, page_number)
        
        # 处理跨页的测试用例
        for test_case in test_cases:
            test_case_id = test_case.get("test_case_id", "")
            
            if test_case_id in pending_test_cases:
                # 合并跨页的测试脚本
                existing_case = pending_test_cases[test_case_id]
                existing_case["test_script"].extend(test_case.get("test_script", []))
                
                # 如果当前页面有完整的测试用例信息，更新其他字段
                if test_case.get("purpose"):
                    existing_case["purpose"] = test_case["purpose"]
                if test_case.get("precondition"):
                    existing_case["precondition"] = test_case["precondition"]
                if test_case.get("description"):
                    existing_case["description"] = test_case["description"]
                if test_case.get("requirements"):
                    existing_case["requirements"] = test_case["requirements"]
                
                # 如果当前页面有测试脚本，说明跨页结束，添加到最终结果
                if test_case.get("test_script"):
                    all_test_cases.append(existing_case)
                    del pending_test_cases[test_case_id]
            else:
                # 如果是新测试用例，检查是否有测试脚本
                if test_case.get("test_script"):
                    # 有测试脚本，检查是否应该与之前的测试用例合并
                    # 查找是否有相同标题的待处理测试用例
                    matching_pending_case = None
                    for pending_id, pending_case in pending_test_cases.items():
                        if pending_case.get("title") == test_case.get("title") and not pending_case.get("test_script"):
                            matching_pending_case = pending_case
                            break
                    
                    if matching_pending_case:
                        # 合并测试脚本到待处理测试用例
                        matching_pending_case["test_script"] = test_case["test_script"]
                        # 更新其他字段
                        if test_case.get("purpose"):
                            matching_pending_case["purpose"] = test_case["purpose"]
                        if test_case.get("precondition"):
                            matching_pending_case["precondition"] = test_case["precondition"]
                        if test_case.get("description"):
                            matching_pending_case["description"] = test_case["description"]
                        if test_case.get("requirements"):
                            matching_pending_case["requirements"] = test_case["requirements"]
                    else:
                        # 没有匹配的待处理测试用例，直接添加到结果
                        all_test_cases.append(test_case)
                else:
                    # 没有测试脚本，可能是跨页的开始，暂存起来
                    pending_test_cases[test_case_id] = test_case
        
        # 特殊处理：如果当前页面只有测试脚本没有测试用例信息（如第14页）
        # 查找上一页的待处理测试用例并尝试合并测试脚本
        if page_number > 1:
            # 检查当前页面是否只有测试脚本，没有测试用例信息
            has_only_test_scripts = False
            for test_case in test_cases:
                if test_case.get("test_script") and not test_case.get("test_case_id") and not test_case.get("title").startswith("Test case"):
                    has_only_test_scripts = True
                    break
            
            # 或者检查当前页面是否有测试脚本，但页面编号是连续的（如13->14）
            if any(tc.get("test_script") for tc in test_cases):
                prev_page = page_number - 1
                # 查找上一页是否有待处理的测试用例
                for pending_id, pending_case in list(pending_test_cases.items()):
                    if pending_case.get("page_number") == prev_page and not pending_case.get("test_script"):
                        # 将当前页面的测试脚本合并到上一页的测试用例中
                        for test_case in test_cases:
                            if test_case.get("test_script"):
                                pending_case["test_script"] = test_case["test_script"]
                                # 标记为已处理
                                test_case["_processed"] = True
                                print(f"Merged test script from page {page_number} to test case from page {prev_page}: {pending_case.get('title')}")
                                
                                # 如果找到了匹配的测试用例，将其从待处理列表中移除并添加到最终结果
                                if pending_case.get("test_case_id"):
                                    all_test_cases.append(pending_case)
                                    del pending_test_cases[pending_id]
                                break
        
        # 处理跨页测试脚本合并
        next_page_num = page_number + 1
        next_page_file = Path(input_dir) / f"CC_DVM-{next_page_num}.html"
        
        if next_page_file.exists():
            with open(next_page_file, 'r', encoding='utf-8') as f:
                next_html_content = f.read()
            
            if has_test_script_only(next_html_content):
                test_script = extract_test_script_from_html(next_html_content, next_page_num)
                
                if test_script:
                    for test_case in test_cases:
                        if not test_case.get("test_script") and test_case.get("test_case_id"):
                            test_case["test_script"] = test_script
                            break
        
        # 保存单个页面的测试用例
        if test_cases:
            # 使用测试用例ID作为文件名的一部分
            if test_cases and len(test_cases) > 0 and test_cases[0].get('test_case_id'):
                test_case_id = test_cases[0]['test_case_id']
                output_file = Path(output_dir) / f"test_cases_id_{test_case_id}_page_{page_number}.json"
            else:
                output_file = Path(output_dir) / f"test_cases_page_{page_number}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_cases, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(test_cases)} test cases to {output_file}")

    # 保存当前页面的测试用例
    if test_cases:
        # 使用测试用例ID作为文件名的一部分
        if test_cases and len(test_cases) > 0 and test_cases[0].get('test_case_id'):
            test_case_id = test_cases[0]['test_case_id']
            output_file = Path(output_dir) / f"test_cases_id_{test_case_id}_page_{page_number}.json"
        else:
            output_file = Path(output_dir) / f"test_cases_page_{page_number}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(test_cases, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(test_cases)} test cases to {output_file}")
    
    # 处理剩余的跨页测试用例（没有找到后续页面的）
    # 最后检查是否有测试用例缺少测试脚本，尝试从下一页获取
    for test_case_id, test_case in list(pending_test_cases.items()):
        # 如果这个测试用例没有测试脚本，但页面编号小于最大页面
        if not test_case.get("test_script") and test_case.get("page_number", 0) < len(html_files):
            next_page = test_case.get("page_number") + 1
            # 检查下一页文件是否存在
            next_file = None
            for f in html_files:
                if f"CC_DVM-{next_page}.html" in str(f):
                    next_file = f
                    break
            
            if next_file and next_file.exists():
                print(f"Checking next page {next_page} for test script for test case: {test_case.get('title')}")
                # 读取下一页的内容
                with open(next_file, 'r', encoding='utf-8') as f:
                    next_html_content = f.read()
                
                # 检查下一页是否只有测试脚本
                if has_test_script_only(next_html_content):
                    # 提取测试脚本
                    next_test_script = extract_test_script_from_html(next_html_content, next_page)
                    if next_test_script and len(next_test_script) > 0:
                        test_case["test_script"] = next_test_script
                        print(f"Found and merged test script from page {next_page} for test case: {test_case.get('title')}")
        
        # 无论是否找到测试脚本，都将测试用例添加到最终结果
        all_test_cases.append(test_case)
        
    # 清理已处理的待处理测试用例
    pending_test_cases.clear()
    
    # 保存所有测试用例到一个文件
    all_output_file = Path(output_dir) / "all_test_cases.json"
    with open(all_output_file, 'w', encoding='utf-8') as f:
        json.dump(all_test_cases, f, ensure_ascii=False, indent=2)
    print(f"Saved all {len(all_test_cases)} test cases to {all_output_file}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract test cases from HTML files.')
    parser.add_argument('input_dir', nargs='?', default='./CC_DVMToHtml', 
                        help='Input directory containing HTML files (default: ./CC_DVMToHtml)')
    parser.add_argument('output_dir', nargs='?', default='./extracted_test_cases', 
                        help='Output directory for JSON files (default: ./extracted_test_cases)')
    
    args = parser.parse_args()
    
    process_html_files(args.input_dir, args.output_dir)