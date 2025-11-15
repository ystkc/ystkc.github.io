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

def get_latest_files(path, num=5):
    file_list = []
    base_len = len(path)
    for root, dirs, files in os.walk(path):
        relative_path = root[base_len+1:]
        if relative_path.startswith('_') or relative_path.startswith('.') or relative_path in exclude_dirs:
            continue # 忽略下划线开头的隐藏、模板或缓存文件夹
        for file in files:
            if file == 'index.html':
                continue # 忽略index.html文件
            if file.endswith('.md') or file.endswith('.markdown') or file.endswith('.html'):
                file_path = os.path.join(root, file)
                ttype = 0 # 0: 最近创建的文件，1: 最近修改的文件
                ftime = os.path.getctime(file_path)
                mtime = os.path.getmtime(file_path)
                if mtime > ftime+86401: # 最近修改的文件
                    ttype = 1
                    ftime = mtime
                file_list.append({'path': file_path[base_len:].replace('\\', '/').split('.')[0], 'time': int(ftime), 'type': ttype})
    file_list.sort(key=lambda x: x['time'], reverse=True)
    return file_list[:num]

if __name__ == '__main__':
    path = os.getcwd()
    file_list = get_latest_files(path)
    
    with open('latest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(file_list, ensure_ascii=False, indent=0).replace('\n', ''))
    print('最新文件列表已更新至latest.json文件。注意：仅支持.md、.markdown、.html文件，不包含在_config.yml文件中的排除文件，以及路径上含有.的文件')