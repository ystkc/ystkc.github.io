
import os
import json
from fuzzywuzzy import process

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("./sentences-bundle-master/categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)


sentences = {}
for category in categories:
    key = category["key"]
    with open(f"./sentences-bundle-master/sentences/{key}.json", "r", encoding="utf-8") as f:
        sentences[key] = json.load(f)

# 根据用户输入的句子进行模糊搜索
def search_sentences(searchSentence):
    results = {}
    for cat in categories:
        k = cat["key"]
        description = cat["name"]
        result = process.extract(searchSentence, sentences[k], limit=5)
        results[description] = result
    return results

def fmt(results):
    res = ""
    for k, v in results.items():
        title = False
        for tp in v:
            sen, score = tp
            if score < 30:
                continue
            if not title:
                res += f"\n\n【{k}】\n\n"
                title = True
            res += f"▲ 相似度：{score}\n"
            for sk, sv in sen.items():
                res += f"{sk}：{sv}\n"
            res += "\n"
    return res

while True:
    s = input("请输入句子(#结束)：")
    sentence = ""
    while s != '#':
        sentence += s + " "
        s = input("请输入句子(#结束)：")
    print(fmt(search_sentences(sentence)))