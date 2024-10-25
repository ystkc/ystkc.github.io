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
if os.path.exists('bad_words.txt'):
    with open('bad_words.txt', 'r', encoding='utf-8') as f:
        bad_words.extend(f.read().splitlines())
bad_words = list(set(bad_words))
invalid_bad_words = []

accept_notice = ""
if os.path.exists('accept_notice.txt'):
    with open("accept_notice.txt", "r", encoding="utf-8") as f:
        accept_notice = f.read()


def cbw(check_word, accept_notice):
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
                    index = max(index - 10, 0)
                    result.append(temp_accept_notice[index:index+len(check_word)+20])
                    temp_accept_notice = temp_accept_notice[index+len(sub_word):]
                    i += 1
                else:
                    # 重新查找上一个sub_word的位置
                    i -= 1
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
        bad_words.remove(check_word)
        invalid_bad_words.append(check_word)

check_word = input('请输入要检查/添加的词，一行一个#退出：')
while check_word!= '#':
    if check_word in bad_words:
        print(f'{check_word} \033[32m已存在于黑名单中\033[0m')
    else:
        result = cbw(check_word, accept_notice)
        if result != "":
            print(f'{check_word} \033[33m已存在于被接受的通知中\033[0mresult:{result}')
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
        with open("./assets/bad_words.bin", "wb") as f:
            f.write(encoder(json.dumps(bad_words, ensure_ascii=False)))
        # 输出到zip文件
        with zipfile.ZipFile('./assets/bad_words.bin.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write('./assets/bad_words.bin', arcname='bad_words.bin')
else:
    if input('已拷贝结果。是否输出到\033[1;31menhanced_\033[0mbad_words.bin和json？y/n') == 'y':
        with open("./assets/enhanced_bad_words.json", "w", encoding="utf-8") as f:
            json.dump(bad_words, f, ensure_ascii=False)
        with open("./assets/enhanced_bad_words.bin", "wb") as f:
            f.write(encoder(json.dumps(bad_words, ensure_ascii=False)))
        # 输出到zip文件
        with zipfile.ZipFile('./assets/enhanced_bad_words.bin.zip', 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write('./assets/enhanced_bad_words.bin', arcname='enhanced_bad_words.bin')