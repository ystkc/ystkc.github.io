# check_bad_words.py
'''【独立工具】用于导入新的违禁词，同时检测是否存在已被接受的公告中'''
'''写入默认违禁词库， --enhanced 写入加强违禁词库'''
'''已被接受的公告来源于automata'''
import os
import json
import pyperclip
import zipfile
import re

def encoder(text):
    # 转化成bytearray类型
    input = bytearray(text.encode())
    
    for i in range(len(input)):
        # 将byte的后5位取反
        input[i] = input[i] ^ 0b00011111
    
    return input


enhanced = False
if '--enhanced' in os.sys.argv:
    enhanced = True

bad_words = []
if not enhanced:
    print("如果要检查已有违禁词，请保存到bad_words.json或bad_words.txt文件中，启动时会自动读取。")
    print("bad_words.json会被覆盖。bad_words.txt不会被覆盖。现有违禁词：")
    if os.path.exists('./assets/bad_words.json'):
        with open('./assets/bad_words.json', 'r', encoding='utf-8') as f:
            bad_words = json.load(f)
else:
    print("如果要检查已有违禁词，请保存到\033[1;31menhanced_\033[0mbad_words.json或bad_words.txt文件中，启动时会自动读取。")
    print("bad_words.json会被覆盖。bad_words.txt不会被覆盖。现有违禁词：")
    if os.path.exists('./assets/enhanced_bad_words.json'):
        with open('./assets/enhanced_bad_words.json', 'r', encoding='utf-8') as f:
            bad_words = json.load(f)
print(bad_words)
print(len(bad_words))
if os.path.exists('bad_words.txt'):
    with open('bad_words.txt', 'r', encoding='utf-8') as f:
        bad_words.extend(f.read().splitlines())
bad_words = list(set(bad_words))
invalid_bad_words = []

accept_notice = ""
if os.path.exists('accept_notice.txt'):
    with open("accept_notice.txt", "r", encoding="utf-8") as f:
        accept_notice = f.read()

replace_dict = {
    '一': '1',
    '二': '2',
    '三': '3',
    '四': '4',
    '五': '5',
    '六': '6',
    '七': '7',
    '八': '8',
    '九': '9',
    '零': '0',
    '壹': '1',
    '贰': '2',
    '叁': '3',
    '肆': '4',
    '伍': '5',
    '陆': '6',
    '柒': '7',
    '捌': '8',
    '玖': '9',
    '貮': '2',
    '两': '2',
    '〇': '0'
}
def cbw(check_word, accept_notice):
    if check_word[0] == '!' or check_word[0] == '?':
        check_word = check_word[1:]
    if check_word in accept_notice:
        result = max(accept_notice.index(check_word) - 10, 0)
        return accept_notice[result:result+len(check_word)+20]
    elif check_word[0] == '/': # 正则表达式
        try:
            result = re.search(check_word[1:-1], accept_notice)
        except:
            return "Invalid regular expression"
        if result:
            result = max(result.start() - 10, 0)
            return accept_notice[result:result+len(check_word)+20]
    elif '|' in check_word:
        sub_words = check_word.split('|')
        temp_accept_notice = accept_notice
        valid = True
        result = []
        i = 0
        while i < len(sub_words):
            try:
                sub_word = sub_words[i]
                index = temp_accept_notice.index(sub_word)
                # 提取到index_new位置
                if i == 0 or '\\\\' not in temp_accept_notice[:index]: # 跨公告了，不算
                    result.append(temp_accept_notice[max(index - 10, 0):max(index - 10, 0)+len(check_word)+20])
                    temp_accept_notice = temp_accept_notice[index+len(sub_word):]
                    i += 1
                else:
                    # 重新查找上一个sub_word的位置
                    i -= 1
                    result.pop()
                    continue
            except ValueError:
                valid = False
                break
        if valid:
            return '|'.join(result)
    return ""


for check_word in bad_words:
    result = cbw(check_word, accept_notice)
    if result != "":
        print(f'{check_word} \033[33m已存在于被接受的通知中\033[0mresult:{result}')
        if check_word[0] != '!':
            bad_words.remove(check_word)
            invalid_bad_words.append(check_word)
        else:
            print(f"黑名单【保留】：{check_word[1:]}")

check_word = input('请输入要检查/添加的词，一行一个!强制?取消强制#退出：')
no_check = False
while check_word!= '#':
    no_check = False
    if check_word[0] == '!':
        no_check = True
    elif check_word[0] == '?':
        check_word = check_word[1:]
        for i in range(len(bad_words)):
            if bad_words[i][0] == '!' and bad_words[i][1:] == check_word:
                print(f'{check_word} \033[32m已取消强制\033[0m')
                bad_words[i] = check_word
                break
        else:
            print(f'{check_word} \033[31m不存在\033[0m')
    elif check_word[0] == '-':
        check_word = check_word[1:]
        try:
            bad_words.remove(check_word)
            print(f'{check_word} \033[32m已从黑名单中移除\033[0m')
        except ValueError:
            print(f'{check_word} \033[31m不存在\033[0m')
    else:
        if check_word in bad_words:
            print(f'{check_word} \033[32m已存在于黑名单中\033[0m')
        else:
            result = cbw(check_word, accept_notice)
            if result != "":
                print(f'{check_word} \033[33m已存在于被接受的通知中\033[0mresult:{result}')
                if no_check:
                    bad_words.append(check_word)
                    print(f'{check_word} 已添加到黑名单中')
            else:
                bad_words.append(check_word)
                print(f'{check_word} 已添加到黑名单中')
    check_word = input('请输入要检查/添加的词，一行一个#退出：')

print(bad_words)
pyperclip.copy(' '.join(bad_words))
input('已拷贝违禁词，换行继续拷贝失效违禁词')
pyperclip.copy(' '.join(invalid_bad_words))

if not enhanced:
    if input('已拷贝结果。是否输出到bad_words.bin和json？y/n') == 'y':
        with open("./assets/bad_words.json", "w", encoding="utf-8") as f:
            json.dump(bad_words, f, ensure_ascii=False)
        # 去除叹号
        for i in range(len(bad_words)):
            if bad_words[i][0] == '!':
                bad_words[i] = bad_words[i][1:]
        with open("./assets/bad_words.bin", "wb") as f:
            f.write(encoder(json.dumps(bad_words, ensure_ascii=False)))
        # 输出到zip文件
        with zipfile.ZipFile('./assets/bad_words.bin.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write('./assets/bad_words.bin', arcname='bad_words.bin')
else:
    if input('已拷贝结果。是否输出到\033[1;31menhanced_\033[0mbad_words.bin和json？y/n') == 'y':
        with open("./assets/enhanced_bad_words.json", "w", encoding="utf-8") as f:
            json.dump(bad_words, f, ensure_ascii=False)
        # 去除叹号
        for i in range(len(bad_words)):
            if bad_words[i][0] == '!':
                bad_words[i] = bad_words[i][1:]
        with open("./assets/enhanced_bad_words.bin", "wb") as f:
            f.write(encoder(json.dumps(bad_words, ensure_ascii=False)))
        # 输出到zip文件
        with zipfile.ZipFile('./assets/enhanced_bad_words.bin.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write('./assets/enhanced_bad_words.bin', arcname='enhanced_bad_words.bin')