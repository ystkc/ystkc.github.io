# 递归扫描当前文件夹（包含子文件夹）下的所有md、markdown、html文件，找到最近创建或修改的10个文件，输出到latest.json文件中。

import os
import json
from datetime import datetime

# 读取_config.yml文件中的排除信息
import yaml
with open('_config.yml', 'r', encoding='utf-8') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)
    excludes = config.get('exclude', [])

exclude_dirs = []
exclude_files = []
for item in excludes:
    if item.startswith('*'):
        exclude_files.append(item[1:])
    else:
        exclude_dirs.append(item)

exclude_dirs = [d[:-1].replace('/', '\\') for d in exclude_dirs]
print("已排除：", exclude_dirs)


def getinfo(file_path):
    '''根据文件路径获取时间，以及是否新文件。如果是新文件则返回创建时间，否则返回修改时间'''
    ttype = 0 # 0: 最近创建的文件，1: 最近修改的文件
    ftime = os.path.getctime(file_path)
    mtime = os.path.getmtime(file_path)
    if mtime > ftime+86401: # 最近修改的文件
        ttype = 1
        ftime = mtime
    return ttype, ftime

def get_latest_files(path, num=5):
    f_list = []
    base_len = len(path)
    zip_dict = {}
    # 先扫描一次zip文件，获取资源文件的更新时间
    for root, dirs, files in os.walk(path):
        relative_path = root[base_len+1:]
        if relative_path.startswith('_') or relative_path.startswith('.') or relative_path in exclude_dirs:
            continue # 忽略下划线开头的隐藏、模板或缓存文件夹
        for file in files:
            if file.endswith('.zip'):
                file_path = os.path.join(root, file)
                ttype, file_time = getinfo(file_path)
                url = file_path[base_len:].replace('\\', '/').split('.')[0]
                file_name = url.split('/')[-1]
                zip_dict[file_name] = {'path': url, 'time': int(file_time), 'type': ttype}

            
    for root, dirs, files in os.walk(path):
        relative_path = root[base_len+1:]
        if relative_path.startswith('_') or relative_path.startswith('.') or relative_path in exclude_dirs:
            continue # 忽略下划线开头的隐藏、模板或缓存文件夹
        for file in files:
            if file == 'index.html':
                continue # 忽略index.html文件
            if file.endswith('.md') or file.endswith('.markdown') or file.endswith('.html'):
                file_path = os.path.join(root, file)
                ttype, file_time = getinfo(file_path)
                url = file_path[base_len:].replace('\\', '/').split('.')[0]
                if url == '/check': # 特殊处理：违禁词检查的修改时间需要取bad_words.bin.zip和accept_words.bin.zip文件的修改时间
                    bad_words_time = zip_dict.get('bad_words', {'time': 0})['time']
                    print(bad_words_time)
                    accept_words_time = zip_dict.get('accept_words', {'time': 0})['time']
                    file_time = max(file_time, bad_words_time, accept_words_time)
                    print('检测到/check，更新时间：', datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S'))
                elif url == '/wafer': # 特殊处理：黑名单检查需要blacklist.bin.zip文件的修改时间
                    blacklist_time = zip_dict.get('blacklist', {'time': 0})['time']
                    file_time = max(file_time, blacklist_time)
                    print('检测到/wafer，更新时间：', datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S'))
                f_list.append({'path': url, 'time': int(file_time), 'type': ttype})
    f_list.sort(key=lambda x: x['time'], reverse=True)
    return f_list[:num]

if __name__ == '__main__':
    cur_path = os.getcwd()
    file_list = get_latest_files(cur_path)
    
    with open('latest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(file_list, ensure_ascii=False, indent=0).replace('\n', ''))
    print('最新文件列表已更新至latest.json文件。注意：仅支持.md、.markdown、.html文件，不包含在_config.yml文件中的排除文件，以及路径上含有.的文件')