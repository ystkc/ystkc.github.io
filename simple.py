
import json

def parse_text(text: str) -> list:
    '''将文本解析长度为2的所有字串列表'''
    result = []
    for i in range(len(text)-1):
        result.append(text[i])
        result.append(text[i] + text[i+1])
    result.append(text[-1])
    return result

input_str = ""
while True:
    str_t = input("查找违禁词，输入#结束：")
    if str_t == "#":
        break
    input_str += str_t + "\n"

pos_list = []
matched_list = []
with open("./assets/bad_words.json", "r", encoding="utf-8") as f:
    bad_words = json.load(f)
with open("./assets/accept_words.json", "r", encoding="utf-8") as f:
    accept_words = set(json.load(f))
with open("./assets/warn_words.json", "r", encoding="utf-8") as f:
    warn_words = set(json.load(f))


def set_invalid_storage(invalid_storage: dict, position, char, length=1):
    for i in range(position, position+length):
        if i not in invalid_storage:
            invalid_storage[i] = [char]
        else:
            invalid_storage[i].append(char)

def slice_invalid_char(text: str):
    # 去除并存储无效字符的位置
    invalid_chars = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/','"',"'",'、','‘','’','“','”','(',')','（','）']
    invalid_storage = {}
    position = 0
    new_text = ""
    for char in text:
        if char in invalid_chars:
            set_invalid_storage(invalid_storage, position, char)
        else:
            position += 1
            new_text += char
    return new_text, invalid_storage


def restore_invalid_char(text: str, invalid_storage: dict):
    # 插入无效字符
    bad = False # 优先级从高到低
    accept = False
    warn = False
    new_text = ""
    for position in range(len(text)):
        if position in invalid_storage:
            min_char = "9"
            for char in invalid_storage[position]:
                if char.isdigit():
                    min_char = min(min_char, char)
                else:
                    new_text += char
            if min_char == "1":
                new_text += '\033[31m'
                bad = True
            elif min_char == "2":
                new_text += '\033[32m'
                accept = True
            elif min_char == "3":
                new_text += '\033[33m'
                warn = True
            elif bad or accept or warn:
                new_text += '\033[0m'
                bad = False
                accept = False
                warn = False
        new_text += text[position]
    return new_text


valid_input_str, invalid_storage = slice_invalid_char(input_str)
for pattern in bad_words:
    try:
        temp_valid_input_str = valid_input_str
        pos = 0
        while True:
            pos += temp_valid_input_str.index(pattern)
            # if pattern == '骚':
            #     print(temp_valid_input_str, pos)
            temp_valid_input_str = valid_input_str[pos+len(pattern):]
            set_invalid_storage(invalid_storage, pos, "1", length=len(pattern)) # 31m
            pos += len(pattern)
            matched_list.append(pattern)
    except ValueError:
        pass
# 匹配accept_words标为绿色（取交集）
text_set = set(parse_text(valid_input_str))
text_accept_set = text_set.intersection(accept_words)
for word in text_accept_set:
    try:
        temp_valid_input_str = valid_input_str
        pos = 0
        while True:
            pos += temp_valid_input_str.index(word)
            temp_valid_input_str = valid_input_str[pos+len(word):]
            set_invalid_storage(invalid_storage, pos, f"2", length=len(word))   # 32m
            pos += len(word)
    except ValueError:
        pass
# 匹配warn_words标为黄色
text_set = set(parse_text(valid_input_str))
text_bad_set = text_set.intersection(warn_words)
for word in text_bad_set:
    try:
        temp_valid_input_str = valid_input_str
        pos = 0 
        while True:
            pos += temp_valid_input_str.index(word)
            temp_valid_input_str = valid_input_str[pos+len(word):]
            set_invalid_storage(invalid_storage, pos, "3", length=len(word)) # 33m
            pos += len(word)
    except ValueError:
        pass
print(restore_invalid_char(valid_input_str, invalid_storage))
print("\033[0m\n匹配到的词汇：", matched_list)
