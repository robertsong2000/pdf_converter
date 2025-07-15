import re
import os
from pathlib import Path

def parse_testcases(md_file_path, output_dir):
    """解析Markdown文件中的测试用例并保存为单独文件"""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 从文件名提取前缀
    md_filename = os.path.basename(md_file_path)
    prefix = os.path.splitext(md_filename)[0] + '_'
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 匹配测试用例模式
    testcase_pattern = re.compile(
        r'(?:\d+\.\d+(?:\.\d+)?\s+)?Test case :(.*?)(?=(?:\d+\.\d+(?:\.\d+)?\s+)?Test case :|Test Specification:|$)', 
        re.DOTALL
    )
    
    testcases = testcase_pattern.findall(content)
    
    for i, testcase in enumerate(testcases, 1):
        # 清理测试用例内容
        # 合并多个 re.sub 调用
        patterns = [
            r'RELEASED.*?[A-Z]+ DVM\n',
            r'Document Type.*?',
            r'Vehicle Manufacturer.*?',
            r'Document Release Status.*?'
        ]
        for pattern in patterns:
            testcase = re.sub(pattern, '', testcase, flags=re.DOTALL if '\n' in pattern else 0)

        # 尝试从测试用例内容中提取名称
        name_match = re.search(r'(.*?)$', testcase, re.MULTILINE)
        if name_match:
            testcase_name = name_match.group(1).strip()
            # 清理名称，替换非法字符为下划线，并限制长度
            testcase_name = re.sub(r'[^a-zA-Z0-9_\-]', '_', testcase_name)
            testcase_name = testcase_name[:50] # 限制文件名长度
            if not testcase_name: # 如果清理后为空，则使用默认名称
                testcase_name = f'testcase_{i}'
            testcase_name = prefix + testcase_name
        else:
            testcase_name = prefix + f'testcase_{i}'

        # 保存为单独文件
        output_file = os.path.join(output_dir, f'{testcase_name}.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Test Case: ")
            f.write(testcase)
    
    print(f"成功解析并保存了{len(testcases)}个测试用例到{output_dir}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='解析Markdown文件中的测试用例')
    parser.add_argument('md_file', help='输入的Markdown文件路径')
    parser.add_argument('-o', '--output', default='testcases', 
                       help='输出目录路径，默认为当前目录下的testcases文件夹')
    
    args = parser.parse_args()
    parse_testcases(args.md_file, args.output)