
import requests
import json
import time
import sqlite3
import hashlib
import os
import re
import threading
import random
from pypinyin import pinyin, Style

class_list_url = 'https://group.baicizhan.com/group/get_group_rank'
notice_url = 'https://group.baicizhan.com/group/information'
class BCZNotice:
    def __init__(self):
        # 连接数据库
        self.conn = sqlite3.connect('bcz_notice.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS notice (
            SHARE_KEY TEXT,
            NAME TEXT,
            RANK_TYPE INTEGER, -- 7王者; 6星耀;5钻石;4铂金;3黄金;2白银;1青铜
            RANK INTEGER,   
            HASH_VALUE TEXT,
            CONTENT TEXT,
            DATE TEXT,
            SCORE INTEGER
        )''')
        self.conn.commit()

        with open('access_token.txt', 'r', encoding='utf-8') as f:
            self.main_token = f.read().strip()

        self.rank_type_dict = {
            7: '王者',
            6: '星耀',
            5: '钻石',
            4: '铂金',
            3: '黄金',
            2: '白银',
            1: '青铜'
        }
        with open('default_headers.json', 'r', encoding='utf-8') as f:
            self.default_headers = json.load(f)
        with open('default_cookie.json', 'r', encoding='utf-8') as f:
            self.default_cookie = json.load(f)
        
        self.hash_rmb = {}
        # 初始化违禁词库
        with open('patterns.json', 'r', encoding='utf-8') as f:
            self.patterns = json.load(f) # dict{pattern: {expired_index: int}}
        

        self.update_patterns()

    def __del__(self):
        self.conn.close()

    def update_patterns(self):
        '''更新正则表达式'''
        
        # 将patterns组合成一个正则表达式，使用|分隔各个模式  
        # 为了确保不会误匹配子模式的组合，我们可以对每个模式使用re.escape()  
        pattern_str = '|'.join(re.escape(p) for p, _ in self.patterns.items())  
        self.pattern = re.compile(pattern_str) 
        # 拼音转换库
        self.pinyin_list = []
        self.pinyin_reference = []
        for p, _ in self.patterns.items():
            p_pinyin = pinyin(p, style=Style.TONE3)
            self.pinyin_list.append([''.join(word) for word in p_pinyin])
            self.pinyin_reference.append(p)
        # 示例：[[['shi'], ['li']],...]
        # 符号列表，用于从原文中去除特殊符号和标点符号
        self.punc = [',', '.', '!', '?', ':', ';', '，', '。', '！', '？', '：', '；','\n',' ','/']

        self.punc_pattern = re.compile(r'[' + ''.join(self.punc) + ']')


    def find_all_subsequences(self, main_list, sub_list, pattern):  
        """  
        在主列表中找到子列表作为连续子序列出现的所有起始索引。  
        如果找不到，返回一个空列表。  
        """  
        indexes = []  
        n = len(sub_list)  
        for i in range(len(main_list) - n + 1):  
            if main_list[i:i+n] == sub_list:  
                indexes.append((i, i+n, pattern))  
        return indexes  
  
        
        
    def replace_non_overlapping_substrings(self, text, published: bool = False) -> list:  
        '''将文本中的违禁词标黄，加标点违禁词标绿，谐音违禁词标蓝，NLP标紫'''
        # 使用finditer找到所有非重叠的匹配  
        try:
            matches = [(m.start(), m.end(), m.group()) for m in self.pattern.finditer(text)]  
        except:
            print('\033[31m 正则表达式匹配失败 \033[0m\n')
            return []
        if published:
            # 如果是已经发布的公告，则将所有出现的违禁词的过期指数+1
            for start, end, pattern in matches:
                if self.patterns.get(pattern) is not None:
                    if 'expired_index' not in self.patterns[pattern]:
                        self.patterns[pattern]['expired_index'] = 0
                    self.patterns[pattern]['expired_index'] += 1
                    if self.patterns[pattern]['expired_index'] >= 12:
                        # 如果过期指数超过3，则删除该模式
                        del self.patterns[pattern]
                        # 重新生成正则表达式
                        self.update_patterns()

        # 第2-4步是为了探测违禁词
        # 第二步：去除原文中的特殊符号和标点符号，再次判断是否有违禁词
        text_without_punc = self.punc_pattern.sub('', text)
        # 全部转小写
        text_without_punc = text_without_punc.lower()
        text_without_punc_index = []
        for current_position, char in enumerate(text):
            if char not in self.punc:# 不是标点符号，记录位置
                text_without_punc_index.append(current_position)
        text_without_punc_index.append(len(text))   
        without_punc_matches = [(m.start(), m.end(), m.group()) for m in self.pattern.finditer(text_without_punc)]

        # 第三步：转化成拼音，找是否有谐音违禁词（此处要求音调相同）
        pinyin_with_tone = pinyin(text, style=Style.TONE3)
        pinyin_text = [''.join(word) for word in pinyin_with_tone]
        pinyin_matches = []
        pinyin_index = [] # 记录拼音列表每项对应原字符串的位置
        current_position = 0
        for pinyin_word in pinyin_text:
            pinyin_index.append(current_position)
            if pinyin_word in text: # 在原文中也有，则不是中文，记录长度
                current_position += len(pinyin_word)
            else:# 是中文，长度=2
                current_position += 1
                # python中的中文字符长度为1！out of the blue
        pinyin_index.append(current_position)

        for i, target in enumerate(self.pinyin_list):
            pinyin_matches.extend(self.find_all_subsequences(pinyin_text, target, self.pinyin_reference[i]))
        
        # 第4步：NLP标注
        url = "http://localhost:8080/wordscheck"  
        data = json.dumps({'content': text_without_punc})  
        # 如果配置了Header token验证, 填到这里 
        access_token = ""  
        headers = {  
            'Content-Type': 'application/json',  
            'Authorization': f'Bearer {access_token}'  
        }  
        response = requests.post(url, data=data, headers=headers)  
        if response.status_code!= 200:  
            print('\033[31m NLP标注失败 \033[0m\n')
            return []
        result = json.loads(response.text)

        
        control_char = []
        for item in result['word_list']:
            positions = item['position'].split(',')
            for pair in positions:
                position = pair.split('-')
                control_char.append({'num': text_without_punc_index[int(position[0])], 'type': f'\033[45m({item["category"]}:{item["keyword"]})'}) 
                control_char.append({'num': text_without_punc_index[int(position[1])], 'type': '\033[0m'})
            
        
        for start, end, pattern in matches:
            control_char.append({'num': start, 'type': f'\033[43m({pattern})'})
            control_char.append({'num': end, 'type': '\033[0m'})
        for start, end, pattern in without_punc_matches:    
            control_char.append({'num': text_without_punc_index[start], 'type': f'\033[42m({pattern})'})
            control_char.append({'num': text_without_punc_index[end], 'type': '\033[0m'})
        for start, end, pattern in pinyin_matches:
            control_char.append({'num': pinyin_index[start], 'type': f'\033[44m({pattern})'})
            control_char.append({'num': pinyin_index[end], 'type': '\033[0m'})
        
        
        # 按num排序
        control_char.sort(key=lambda x: x['num'])
        
        return control_char 
    
    def getHeaders(self, token: str = '') -> dict:
        '''获取请求头'''
        if (not token):
            token = self.main_token

        current_headers = self.default_headers['default_headers_dict']

        if token not in self.hash_rmb:
            # 使用哈希函数计算字符串的哈希值
            hash_value = hash(token)
            # 将哈希值转换为unsigned long long值，然后取反，再转换为16进制字符串
            hex_string = format((~hash_value) & 0xFFFFFFFFFFFFFFFF, '016X')
            self.hash_rmb[token] = {'hex_string': hex_string }

        current_cookie = self.default_cookie.copy()
        current_cookie['device_id'] = f'{self.hash_rmb[token]["hex_string"]}'
        current_cookie['access_token'] = token
        current_cookie['client_time'] = str(int(time.time()))
        current_headers['Cookie'] = ''
        for key, value in current_cookie.items():
            key = key.replace(";","%3B").replace("=","%3D")
            value = value.replace(";","%3B").replace("=","%3D")
            current_headers['Cookie'] += f'{key}={value};'
        # 需要转为str
        return current_headers
    
    def controlCharToStr(self, control_char: list, content: str) -> str:
        '''将控制字符列表转换为带控制字符的文本'''
        result = ''
        last_index = 0
        for item in control_char:
            result += content[last_index:item['num']]
            result += item['type']
            last_index = item['num']
        result += content[last_index:]
        return result

    
    
    def getNotice(self, rank_type: int = 7, automated: bool = False) -> list: # 7王者; 6星耀;5钻石;4铂金;3黄金;2白银;1青铜
        '''获取通知列表'''
        # 获取今天日期的个位数，获取排名百位与日期各位数相同的班级的通知(每天获取100个班级)
        today_date = time.strftime('%Y-%m-%d', time.localtime())
        today_date_digit = (int(today_date[-1]) % 5) * 2
        # 先获取班级列表
        class_list_response = requests.get(f"{class_list_url}?rank={rank_type}", headers=self.getHeaders())
        class_list_json = json.loads(class_list_response.text)
        class_list = class_list_json['data']['list']
        # 先将排名储存到数据库中
        for i, class_item in enumerate(class_list):
            class_share_key = class_item['shareKey']
            class_name = class_item['groupName']
            class_score = class_item['score']
            self.cursor.execute(f"INSERT OR IGNORE INTO notice (SHARE_KEY, NAME, RANK_TYPE, RANK, HASH_VALUE, CONTENT, DATE, SCORE) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                (class_share_key, class_name, rank_type, i + 1, '', '', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), class_score))
        self.conn.commit()
        # 获取排名为today_date_digit * 100后的100个班级

        class_list = class_list[today_date_digit * 100 + 1:(today_date_digit + 2) * 100 - 1]
        rank_base = today_date_digit * 100 + 1
        os.system('cls')
        print(f'📚 → 今日获取段位{self.rank_type_dict[rank_type]}从{rank_base}到{rank_base + len(class_list) - 1}')
        if not automated:
            print('🔥 → 按回车下一个班级，输入q退出')
        # 遍历班级列表，获取通知
        notice_list = []
        for i, class_item in enumerate(class_list):
            class_share_key = class_item['shareKey']
            class_name = class_item['groupName']
            # 获取通知
            notice_response = requests.get(f'{notice_url}?shareKey={class_share_key}', headers=self.getHeaders())
            notice_json = json.loads(notice_response.text)
            content = notice_json['data']['groupInfo']['notice']
            control_char = self.replace_non_overlapping_substrings(content, False)
            # 找班长昵称
            members = notice_json['data']['members']
            for member in members:
                if member['leader'] == True:
                    class_name = f"{class_name}(班长：{member['nickname']})"
            if automated:
                print(f'❤️ → 获取到排名{rank_base + i}的班级{class_name}的通知\n')
            else:
                print(f'❤️ → 获取到排名{rank_base + i}的班级{class_name}的通知：\n{self.controlCharToStr(control_char, content)}\n')
            # 检测当前通知是否已存在数据库
            hash_value = hashlib.md5(content.encode('utf-8')).hexdigest()
            self.cursor.execute(f"SELECT NAME FROM notice WHERE HASH_VALUE='{hash_value}'")
            result = self.cursor.fetchone()
            if not result or content == '':
                # 保存通知到数据库
                self.cursor.execute("""
                    INSERT INTO notice (SHARE_KEY, NAME,RANK_TYPE, RANK, HASH_VALUE, CONTENT, DATE, SCORE) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (class_share_key, class_name, 7, rank_base + i, hash_value, content, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), class_item['score']))
                self.conn.commit()
            else:
                print(f'🙈 → 排名{rank_base + i}的班级{class_name}的通知已存在数据库，跳过')
                
            
            notice_list.append({'share_key': class_share_key, 'name': class_name, 'date': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()), 'content': content})
            
            # 自己看公告用，或者随机延时3-10秒
            # time.sleep(random.randint(3, 10))
            if automated:
                time.sleep(random.randint(3, 10))
            else:
                if input('🔥 → 换行继续') == 'q':
                    print('🛑 → 已中断')
                    break
            os.system('cls')
        if os.path.exists(f'./archive/notice{time.strftime("%Y%m%d", time.localtime())}.json'):
            with open(f'./archive/notice{time.strftime("%Y%m%d", time.localtime())}.json', 'r', encoding='utf-8') as f:
                notice_list.extend(json.load(f))
        with open(f'./archive/notice{time.strftime("%Y%m%d", time.localtime())}.json', 'w', encoding='utf-8') as f:
            json.dump(notice_list, f, ensure_ascii=False, indent=4)
        return notice_list
    
    def save_patterns(self):
        with open('patterns.json', 'w', encoding='utf-8') as f:
            json.dump(self.patterns, f, ensure_ascii=False, indent=4)

import socket
def check_port(host, port):
    try:
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((host, port))
        sock.close()
        return True
    except:
        return False
    finally:
        sock.close()

def start_server():
    # 检测wordscheck_win.exe是否在运行
    if not check_port('localhost', 8080):
        # with open("blacklist.txt","w", encoding='utf-8') as f:
        #     f.write('\n'.join(bcz_notice.patterns.keys()))
        # nut-wall 的nlp黑箱，但是识别不了符号，所以要手动排除特殊符号的违禁词
        os.system('start /min /D "./NLP" ./NLP/wordscheck_win.exe')


if __name__ == '__main__':
    bcz_notice = BCZNotice()
    threading.Thread(target=start_server).start()

    print("违禁词无需删除，在公告微调时会自动更新")
    num = input('1:获取通知\n2:检测违禁词\n3:添加违禁词\n请输入：')
    if num == '1':
        bcz_notice.getNotice((int)(input("请输入排名类型(1-7)：")))
    elif num == '2':
        lines = []
        while True:
            line = input("请输入文本（输入#换行结束）：")
            if line == '#':
                break
            lines.append(line)
        text = '\n'.join(lines)
        print(bcz_notice.controlCharToStr(bcz_notice.replace_non_overlapping_substrings(text), text))
    
    elif num == '3':
        pattern = input("请输入违禁词：")
        if pattern not in bcz_notice.patterns:
            bcz_notice.patterns[pattern] = {'expired_index': 0}
            bcz_notice.update_patterns()
        else:
            print("该违禁词已存在")
            bcz_notice.patterns[pattern]['expired_index'] = 0

    bcz_notice.save_patterns()