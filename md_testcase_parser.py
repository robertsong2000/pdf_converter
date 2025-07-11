import re
import os
from pathlib import Path

def parse_testcases(md_file_path, output_dir):
    """解析Markdown文件中的测试用例并保存为单独文件"""
    with open(md_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 匹配测试用例模式
    testcase_pattern = re.compile(
        r'Test case :(.*?)(?=Test case :|$)', 
        re.DOTALL
    )
    
    testcases = testcase_pattern.findall(content)
    
    for i, testcase in enumerate(testcases, 1):
        # 清理测试用例内容
        testcase = testcase.strip()
        testcase = re.sub(r'RELEASED.*?[A-Z]+ DVM\n', '', testcase, flags=re.DOTALL)
        testcase = re.sub(r'Document Type.*?', '', testcase)
        testcase = re.sub(r'Vehicle Manufacturer.*?\n', '', testcase)
        
        # 保存为单独文件
        output_file = os.path.join(output_dir, f'testcase_{i}.md')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Test Case {i}\n\n")
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