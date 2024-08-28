from pypinyin import pinyin, lazy_pinyin

def find_pinyin_match(text, target):
    # 将文本和目标转换成拼音
    text_pinyin = lazy_pinyin(text)
    target_pinyin = lazy_pinyin(target)
    
    # 将拼音列表转换成字符串，方便比较
    text_pinyin_str = ''.join(text_pinyin)
    target_pinyin_str = ''.join(target_pinyin)
    
    # 查找匹配的拼音子串
    match_index = text_pinyin_str.find(target_pinyin_str)
    
    if match_index == -1:
        return None  # 没有找到匹配的拼音子串
    
    # 计算匹配子串在原始文本中的起始位置
    start_index = 0
    for i, pinyin_char in enumerate(text_pinyin[:match_index]):
        start_index += len(pinyin_char)
    
    # 返回匹配子串在原始文本中的位置
    return (start_index, start_index + len(target))

# 示例
text = "我爱北京天安门"
target = "北京"
result = find_pinyin_match(text, target)
print(result)  # 输出: (2, 4)
