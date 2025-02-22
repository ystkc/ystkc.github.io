import re
 
def compress_html(html_code):
    # 移除注释
    html_code = re.sub(r"<!--(.*?)-->", "", html_code)
    # 移除多余空格
    html_code = re.sub(r">\s+", ">", html_code)
    html_code = re.sub(r"\s+<", "<", html_code)
    # 移除换行符和缩进
    html_code = re.sub(r"\n", "", html_code)
    html_code = re.sub(r"\s{2,}", " ", html_code)
    html_code = html_code.strip()
    return html_code
 
# 使用示例
html_code = input("请输入HTML代码：")
 
compressed_html = compress_html(html_code)
print(compressed_html)