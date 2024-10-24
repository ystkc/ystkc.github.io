import os
import json
import pyperclip

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

for check_word in bad_words:
    if check_word in accept_notice:
        print(f'{check_word} \033[33m已存在于被接受的通知中\033[0m')
        bad_words.remove(check_word)
        invalid_bad_words.append(check_word)

check_word = input('请输入要检查/添加的词，一行一个#退出：')
while check_word!= '#':
    if check_word in bad_words:
        print(f'{check_word} \033[32m已存在于黑名单中\033[0m')
    else:
        if check_word in accept_notice:
            print(f'{check_word} \033[33m已存在于被接受的通知中\033[0m')
            invalid_bad_words.append(check_word)
        else:
            bad_words.append(check_word)
            print(f'{check_word} 已添加到黑名单中')
    check_word = input('请输入要检查/添加的词，一行一个#退出：')

print(bad_words)
pyperclip.copy(' '.join(bad_words))
input('已拷贝违禁词，换行继续拷贝失效违禁词')
pyperclip.copy(' '.join(invalid_bad_words))

if not enhanced:
    if input('已拷贝结果。是否输出到bad_words.json？y/n') == 'y':
        with open("./assets/bad_words.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(bad_words, ensure_ascii=False))
else:
    if input('已拷贝结果。是否输出到\033[1;31menhanced_\033[0mbad_words.json？y/n') == 'y':
        with open("./assets/enhanced_bad_words.json", "w", encoding="utf-8") as f:
            f.write(json.dumps(bad_words, ensure_ascii=False))