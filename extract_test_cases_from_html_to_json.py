import os
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

def extract_test_cases_from_html(html_content, page_number):
    """
    从HTML内容中提取测试用例信息
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 查找所有包含"Test case"的标题
    test_case_headers = []
    
    # 查找所有可能包含测试用例的标题
    for i in range(1, 7):
        for heading in soup.find_all(f'h{i}'):
            if 'Test case' in heading.get_text():
                test_case_headers.append(heading)
    
    # 在HTML中查找包含"Test case"的段落作为标题
    for p in soup.find_all('p'):
        if 'Test case' in p.get_text():
            # 检查是否包含类似"5.6.2 Test case : VCP values"的文本
            text = p.get_text().strip()
            # 修改正则表达式以匹配更广泛的测试用例标题格式
            if re.match(r'\d+(\.\d+)*\s+Test case\s*[:]*', text):
                test_case_headers.append(p)
            else:
                # 添加调试信息
                print(f"Potential test case title found: {text}")
    
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
                if purpose_match:
                    test_case["purpose"] = purpose_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到Purpose，检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        if next_text and not next_text.startswith(('Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script')):
                            test_case["purpose"] = next_text
            
            # 查找PreCondition
            if 'PreCondition:' in text:
                precondition_match = re.search(r'PreCondition:\s*(.*)', text, re.DOTALL)
                if precondition_match:
                    test_case["precondition"] = precondition_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到PreCondition，检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        if next_text and not next_text.startswith(('Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script')):
                            test_case["precondition"] = next_text
            
            # 查找PostCondition
            if 'PostCondition:' in text:
                postcondition_match = re.search(r'PostCondition:\s*(.*)', text, re.DOTALL)
                if postcondition_match:
                    test_case["postcondition"] = postcondition_match.group(1).strip()
                else:
                    # 如果没有在当前段落找到PostCondition，检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        if next_text and not next_text.startswith(('Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script')):
                            test_case["postcondition"] = next_text
            
            # 查找Description
            if 'Description:' in text or 'Test case Description:' in text:
                description_match = re.search(r'(Test case )?Description:\s*(.*)', text, re.DOTALL)
                if description_match:
                    test_case["description"] = description_match.group(2).strip()
                else:
                    # 如果没有在当前段落找到Description，检查下一个段落
                    if i + 1 < len(all_paragraphs):
                        next_text = all_paragraphs[i+1].get_text().strip()
                        if next_text and not next_text.startswith(('Test', 'Purpose', 'PreCondition', 'Description', 'Requirements', 'Test Script')):
                            test_case["description"] = next_text
            
            # 查找需求表格
            if 'Requirements:' in text:
                # 需求信息在后续段落中
                next_elements = all_paragraphs[i+1:]
                # 查找需求信息的结束标记
                end_markers = ['Test Script Description', 'Test Script', 'Step Action']
                collecting = False
                headers = []
                header_found = False
                
                for next_p in next_elements:
                    next_text = next_p.get_text().strip()
                    
                    # 检查是否到达结束标记
                    if any(marker in next_text for marker in end_markers):
                        break
                    
                    # 检查是否是表头行
                    if not header_found and ('Requirement' in next_text and ('Req ID' in next_text or 'Requirement' in next_text)):
                        collecting = True
                        header_found = True
                        # 提取表头
                        headers = [cell.get_text().strip() for cell in next_p.find_all(['td', 'th'])]
                        # 如果没有找到表格单元格，尝试从文本中提取表头
                        if not headers:
                            # 分割表头文本
                            header_text = next_text.replace('Requirement', '').replace('Req ID', '').replace('Ver', '').replace('ASIL', '').replace('Status', '').strip()
                            if header_text:
                                headers = ['Requirement', 'Req ID', 'Ver', 'Status']
                        continue
                    # 如果还没有找到表头，检查当前段落是否包含表头信息
                    elif not header_found:
                        # 检查是否包含需求表头的关键字
                        if 'Requirement' in next_text and 'Req ID' in next_text:
                            collecting = True
                            header_found = True
                            # 尝试分割文本以获取表头

                    
                    # 如果正在收集需求信息
                    if collecting:
                        cells = [cell.get_text().strip() for cell in next_p.find_all(['td', 'th'])]
                        # 如果没有找到表格单元格，尝试从文本中提取单元格内容
                        if not cells:
                            # 尝试按空格分割文本，但更智能地处理
                            # 先尝试按多个空格分割
                            cells = re.split(r'\s{2,}', next_text)
                            # 如果分割后的单元格数量不够，尝试按单个空格分割
                            if len(cells) < 4:
                                cells = next_text.split()
                        
                        if len(cells) >= 4:  # 确保有足够的列
                            requirement = {
                                "requirement": cells[0] if len(headers) > 0 else "",
                                "req_id": cells[1] if len(headers) > 1 else "",
                                "ver": cells[2] if len(headers) > 2 else "",
                                "status": cells[3] if len(headers) > 3 else ""
                            }
                            test_case["requirements"].append(requirement)
                        elif len(cells) >= 2:  # 至少有需求和Req ID两列
                            requirement = {
                                "requirement": cells[0] if len(headers) > 0 else "",
                                "req_id": cells[1] if len(headers) > 1 else "",
                                "ver": cells[2] if len(headers) > 2 and len(cells) > 2 else "",
                                "status": cells[3] if len(headers) > 3 and len(cells) > 3 else ""
                            }
                            test_case["requirements"].append(requirement)
                        elif len(cells) >= 1:  # 只有一列的情况
                            requirement = {
                                "requirement": cells[0] if len(headers) > 0 else "",
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
                end_markers = ['Result', 'Evaluation', 'Analysis']
                collecting = False
                headers = []
                header_found = False
                
                for next_p in next_elements:
                    next_text = next_p.get_text().strip()
                    
                    # 检查是否到达结束标记
                    if any(marker in next_text for marker in end_markers):
                        break
                    
                    # 检查是否是表头行
                    if not header_found and ('Step' in next_text and 'Action' in next_text):
                        collecting = True
                        header_found = True
                        # 提取表头
                        headers = [cell.get_text().strip() for cell in next_p.find_all(['td', 'th'])]
                        # 如果没有找到表格单元格，尝试从文本中提取表头
                        if not headers:
                            headers = ['Step', 'Action', 'Expected Result']
                        continue
                    # 如果还没有找到表头，检查当前段落是否包含表头信息
                    elif not header_found:
                        # 检查是否包含测试脚本表头的关键字
                        if 'Step' in next_text and 'Action' in next_text:
                            collecting = True
                            header_found = True
                    
                    # 如果正在收集测试脚本信息
                    if collecting:
                        cells = [cell.get_text().strip() for cell in next_p.find_all(['td', 'th'])]
                        # 如果没有找到表格单元格，尝试从文本中提取单元格内容
                        if not cells:
                            # 尝试按空格分割文本，但更智能地处理
                            # 先尝试按多个空格分割
                            cells = re.split(r'\s{2,}', next_text)
                            # 如果分割后的单元格数量不够，尝试按单个空格分割
                            if len(cells) < 2:
                                cells = next_text.split()
                        
                        if len(cells) >= 2:  # 确保至少有步骤和动作两列
                            step = {
                                "step": cells[0] if len(headers) > 0 else "",
                                "action": cells[1] if len(headers) > 1 else ""
                            }
                            # 检查是否有预期结果列
                            if len(headers) > 2 and 'Expected Result' in headers[2]:
                                # 如果有预期结果列，尝试从下一个段落获取预期结果
                                if len(cells) > 2:
                                    step["expected_result"] = cells[2]
                                else:
                                    # 检查下一个段落是否包含预期结果
                                    next_index = all_paragraphs.index(next_p) + 1
                                    if next_index < len(all_paragraphs):
                                        next_paragraph = all_paragraphs[next_index]
                                        next_paragraph_text = next_paragraph.get_text().strip()
                                        # 简单检查是否可能是预期结果（这里可能需要更复杂的逻辑）
                                        if next_paragraph_text and not any(marker in next_paragraph_text for marker in ['Step', 'Action', 'Requirement', 'Purpose', 'PreCondition']):
                                            step["expected_result"] = next_paragraph_text
                            test_case["test_script"].append(step)
                        elif len(cells) >= 1:  # 至少有动作一列
                            step = {
                                "step": cells[0] if len(headers) > 0 and len(cells) > 0 else "",
                                "action": cells[0] if len(headers) > 1 and len(cells) > 0 else ""
                            }
                            test_case["test_script"].append(step)
                        else:  # 处理没有单元格的情况
                            # 检查段落文本是否包含步骤信息
                            if 'Step' in next_text or 'Action' in next_text:
                                # 尝试从文本中提取步骤信息
                                step_match = re.search(r'(\d+)\s+(.*)', next_text)
                                if step_match:
                                    step = {
                                        "step": step_match.group(1),
                                        "action": step_match.group(2)
                                    }
                                    test_case["test_script"].append(step)
        
        # 只有当测试用例有ID时才添加到结果中
        if test_case["test_case_id"]:
            test_cases.append(test_case)
        else:
            # 添加调试信息
            print(f"Test case without ID found on page {page_number}: {test_case['title']}")
            # 如果标题包含"Test case"，但没有ID，也添加到结果中
            if "Test case" in test_case["title"]:
                test_cases.append(test_case)
    
    return test_cases

def process_html_files(input_dir, output_dir):
    """
    处理目录中的所有HTML文件，提取测试用例并保存为JSON文件
    """
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 获取所有HTML文件并按编号排序
    html_files = list(Path(input_dir).glob("*.html"))
    html_files.sort(key=lambda x: int(re.search(r'CC_DVM-(\d+)\.html', x.name).group(1)) if re.search(r'CC_DVM-(\d+)\.html', x.name) else 0)
    
    all_test_cases = []
    
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
        
        # 提取测试用例
        test_cases = extract_test_cases_from_html(html_content, page_number)
        
        # 添加到总列表
        all_test_cases.extend(test_cases)
        
        # 保存单个文件的测试用例
        if test_cases:
            output_file = Path(output_dir) / f"test_cases_page_{page_number}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(test_cases, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(test_cases)} test cases to {output_file}")
    
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