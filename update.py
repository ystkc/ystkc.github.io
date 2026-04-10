# 递归扫描当前文件夹（包含子文件夹）下的所有md、markdown、html文件，找到最近创建或修改的10个文件，输出到latest.json文件中。
import os
import random
import string
import base64
import json
from datetime import datetime
import threading
import time
import httpx
import certifi
import hashlib
import urllib.parse

config_json = {}
# 检查config.json是否存在
if not os.path.exists('config.json'):
    input('config.json文件不存在，请手动配置后运行')
    exit()

with open('config.json', 'r', encoding='utf-8') as f:
    config_json = json.load(f)

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



class http2_cilent_m:
    def __init__(self, access_token: str):
        self.client = None
        self.lock = threading.Lock()
        self._closing_state = False # 用于结束多个线程
        self.DEFAULT_COOKIE = config_json.get("DEFAULT_COOKIE")
        if not self.DEFAULT_COOKIE:
            raise ValueError('DEFAULT_COOKIE不能为空')
        self.DEFAULT_COOKIE['access_token'] = access_token
        self.DEFAULT_COOKIE['device_id'] = (hashlib.md5(access_token.encode('utf-8')).hexdigest())[:16]
        self.DEFAULT_HEADERS = config_json.get('DEFAULT_HEADERS')
        if not self.DEFAULT_HEADERS:
            raise ValueError('DEFAULT_HEADERS不能为空')
        self.headers = self.DEFAULT_HEADERS.copy()
        self.headers['Cookie'] = self.DEFAULT_COOKIE.copy()

    def updateHeader(self):
        '''更新请求头'''
        time_short = int(time.time()) # 10位时间戳
        # 将cookie中的时间戳更新
        self.headers['Cookie'] = self.DEFAULT_COOKIE.copy()
        self.headers['Cookie']['client_time'] = str(time_short)
        device_id = self.headers['Cookie']['device_id']
        self.headers['Cookie']['serial'] = f"{device_id[:6]}{device_id[13:]}{str(time_short & 67108863)}"
        # 将cookie转换为字符串
        self.headers['Cookie'] = '; '.join([f'{urllib.parse.quote(k)}={urllib.parse.quote(v)}'
                                    for k, v in self.headers['Cookie'].items()])

    def set_closing_state(self, state):
        self._closing_state = state

    def check_closing_state(self):
        if self._closing_state: # 结束当前线程
            raise AssertionError('http2 client is closing')

    def get(self, url, timeout=10):
        '''同步get'''
        client = self.get_http2_client()
        self.updateHeader()
        failed_count = 0
        while True:
            try:
                response = client.get(url, headers=self.headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 get error: {e}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(1.2)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    self.rua(self.reload_http2_client())
                    self.set_proxy(False)
                    time.sleep(60)
                    failed_count = 0
                continue

    def get_http2_client(self):
        '''获取client，避免重复创建'''
        with self.lock:
            if self.client is None or self.client.is_closed:
                self.client = httpx.Client(http2=True, verify=certifi.where())
            return self.client
                
    def __del__(self):
        if not(self.client is None or self.client.is_closed):
            self.client.close()

def getGroupInfo(access_token: str, share_key: str, http2_client_obj: http2_cilent_m):
    '''获取【班内主页】信息group/information'''
    
    auth_data = {}
    url = config_json.get('SyncURL')
    if not url:
        raise ValueError('SyncURL不能为空')
    url = url + share_key
    auth_response = http2_client_obj.get(url, timeout=10)
    if auth_response.status_code != 200 or auth_response.json().get('code') != 1:
        raise Exception(f'使用内部授权令牌获取分享码为{share_key}的小班信息失败! 小班不存在或内部授权令牌无效')
    auth_data = auth_response.json()['data']
    return auth_data


def rc4(key: bytes, data: bytes) -> bytes:
    """
    RC4加密/解密函数 - 纯Python实现
    注意：RC4加密和解密使用相同的函数
    key: 密钥（字节串）
    data: 待加密/解密数据（字节串）
    返回: 加密/解密结果（字节串）
    """
    # KSA: Key Scheduling Algorithm
    S = list(range(256))
    j = 0
    key_len = len(key)
    for i in range(256):
        j = (j + S[i] + key[i % key_len]) & 0xFF
        S[i], S[j] = S[j], S[i]
    
    # PRGA: Pseudo-Random Generation Algorithm
    i = 0
    j = 0
    result = bytearray()
    for byte in data:
        i = (i + 1) & 0xFF
        j = (j + S[i]) & 0xFF
        S[i], S[j] = S[j], S[i]
        k = S[(S[i] + S[j]) & 0xFF]
        result.append(byte ^ k)
    
    return bytes(result)

def binaryTob64(binary: bytes) -> str:
    '''将二进制数据转换为base64字符串'''
    return base64.b64encode(binary).decode('utf-8')

def b64Tobinary(b64: str) -> bytes:
    '''将base64字符串转换为二进制数据'''
    return base64.b64decode(b64)

import secrets
def randomKey() -> bytes:
    '''生成随机密钥'''
    # return random.choice(string.hexdigits.upper()).encode('utf-8')
    return secrets.token_bytes(64)

def updateGroupInfo(access_token: str, http2_client_obj: http2_cilent_m):
    '''从class.yml中读取班级列表并检查更新'''
    # 加载class.yml文件
    config = None
    with open('_data/class.yml', 'r', encoding='utf-8') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        updateTime = config.get('updateAt', 0)
        groups = config.get('groups', {})
    # 如果今天已经更新过了，则不更新
    if time.time() - updateTime < 86400:
        print('今天已经更新过了，跳过')
        return
    # 遍历每个班级
    for share_key, group_initial_info in groups.items():
        if not group_initial_info:  # 初始有可能是None
            group_initial_info = {}
        auth_data = getGroupInfo(access_token, share_key, http2_client_obj)
        group_info = auth_data.get('groupInfo', {})
        name = group_info.get('name', '')
        RC4Key = randomKey()
        avatar = group_info.get('avatar')
        if avatar.startswith('/'): # 相对路径
            cdn = config_json.get('CDNURL')
            if not cdn:
                raise ValueError('CDNURL不能为空')
            avatar = cdn + avatar
        avatar = rc4(RC4Key, avatar.encode('utf-8'))
        introduction = group_info.get('introduction', '')
        # inviteCode保持不变，此项为手动修改项
        rank = group_info.get('rank', '')
        avatar_frames = group_info.get('avatarFrame', {})
        if not avatar_frames: # 有可能是None
            avatar_frames = {}
        avatar_frame = rc4(RC4Key, avatar_frames.get('frame', '').encode('utf-8'))
        leader_id = -1
        leader = ''
        finishing_rate = round(group_info.get('finishingRate', '')*100, 1)
        # 查找leader_id
        for member in auth_data.get('members', []):
            if member['leader']:
                leader_id = member['uniqueId']
                leader = member['nickname']
        inviteCodeEncrypted = group_initial_info.get('inviteCodeEncrypted', False)
        inviteCode = group_initial_info.get('inviteCode', '保密')
        if not inviteCodeEncrypted:
            # 使用RC4加密邀请码
            inviteCodeEncrypted = True
        else:
            # 先用原来的密钥解密
            initKey = group_initial_info.get('key', '')
            inviteCode = rc4(b64Tobinary(initKey), b64Tobinary(inviteCode)).decode('utf-8')
        encryptedInviteCode = binaryTob64(rc4(RC4Key, inviteCode.encode('utf-8')))
        # 更新groups
        groups[share_key] = {
            'name': name,
            'avatar': binaryTob64(avatar),
            'intro': introduction,
            'inviteCode': encryptedInviteCode,
            'inviteCodeEncrypted': inviteCodeEncrypted,
            'rank': rank,
            'avatar_frame': binaryTob64(avatar_frame),
            'leader_id': leader_id,
            'leader': leader,
            'finishing_rate': finishing_rate,
            'key': binaryTob64(RC4Key)
        }
        print(f"更新班级{name}完成：{share_key}，邀请码：{inviteCode}")
    # 更新config
    config['updateAt'] = int(time.time())
    config['groups'] = groups
    # 写入class.yml文件
    with open('_data/class.yml', 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        f.write('\n')
        f.write('# 更新时间：')
        f.write(datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
        f.write('\n')
    print('班级信息已更新至class.yml文件')
                
        
    

if __name__ == '__main__':
    cur_path = os.getcwd()
    file_list = get_latest_files(cur_path)
    
    with open('latest.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(file_list, ensure_ascii=False, indent=0).replace('\n', ''))
    print('最新文件列表已更新至latest.json文件。注意：仅支持.md、.markdown、.html文件，不包含在_config.yml文件中的排除文件，以及路径上含有.的文件')

    # 更新班级信息
    
    access_token = config_json.get('access_token')
    if not access_token:
        input('config.json文件中未配置access_token，请手动配置后运行')
        exit()
    
    http2_client_obj = http2_cilent_m(access_token)
    updateGroupInfo(access_token, http2_client_obj)
    
