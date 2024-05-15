# 参数格式
# {'num': '', 'filename': '', 'size_byte': '', 'size_human': '', 'path': '', 'packtype': 'RAW|Volume', 'status': 'Success|Failed'}
# ['num', 'filename', 'size_byte', 'size_human', 'path', 'packtype', 'status']

import requests, json, time, configparser, os, pyinputplus, re, urllib.parse, hashlib
from aes_cbc import *
from Public import calc_size

app_info = {
    'AppKey': 'AppKey',
    'SecretKey': 'SecretKey',
    'SignKey': 'SignKey'
}
config_file = rf'{os.path.dirname(os.path.abspath(__file__))}/token.ini'

# 错误处理
def Errno_Code(errno):
    if errno == 0: pass
    elif errno == -6: print('身份验证失败，Cookie 已过期')
    elif errno == 111: print('access token 失效，更新 access token')
    elif errno == 2: print('参数错误')
    elif errno == 6: print('不允许接入用户数据，建议10分钟之后用户再进行授权重试。')
    elif errno == 31034: print('接口请求过于频繁，注意控制。')
    elif errno == -9: print('文件或目录不存在')

# 授权应用获取 Access Token
def Get_AccessToken():
    global app_info
    while True:
        code = ''
        if code == '':
            print(f"在浏览器中打开此链接：http://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={app_info['AppKey']}&redirect_uri=oob&scope=basic,netdisk&")
            code = input('在此输入授权码：')
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": app_info['AppKey'],
            "client_secret": app_info['SecretKey'],
            "redirect_uri": "oob",
        }
        url = f"https://openapi.baidu.com/oauth/2.0/token?{urllib.parse.urlencode(data)}"
        access_token = json.loads(requests.get(url).text)
        access_token['expiration'] = access_token['expires_in'] + int(time.time())
        if "error" in access_token.keys(): print('授权码无效，授权码已过期或已吊销'); code = ''; continue
        elif "access_token" in access_token.keys(): return access_token

# 刷新 Access Token
def Refresh_AccessToken(access_token):
    global app_info
    data = {
        "grant_type": "refresh_token",
        "refresh_token": access_token['refresh_token'],
        "client_id": app_info['AppKey'],
        "client_secret": app_info['SecretKey'],
    }
    url = f"https://openapi.baidu.com/oauth/2.0/token?{urllib.parse.urlencode(data)}"
    access_token = json.loads(requests.get(url).text)
    access_token['expiration'] = access_token['expires_in'] + int(time.time())
    if "access_token" in access_token.keys():
        Save_AccessToken(access_token)
        print('刷新 Access Token 成功，已更新至 token.ini')
        return access_token
    else: print('刷新 Access Token 失败'); return False

# 获取用户信息
def Get_User_Info(access_token, json_format=''):
    user_info_url = f"https://pan.baidu.com/rest/2.0/xpan/nas?access_token={access_token['access_token']}&method=uinfo"
    user_info = json.loads(requests.get(user_info_url).text)
    Errno_Code(user_info['errno'])
    if user_info['netdisk_name'] == '': user_info['netdisk_name'] = user_info['baidu_name']
    capacity_info_url = f"https://pan.baidu.com/api/quota?access_token={access_token['access_token']}&checkfree=1"
    capacity_info = json.loads(requests.get(capacity_info_url).text)
    if json_format == True: return {'netdisk_name': user_info['netdisk_name'], 'total': capacity_info['total'], 'free': capacity_info['free'], 'used': capacity_info['used']}
    else: return f"{user_info['netdisk_name']} 的网盘，总容量：{calc_size(capacity_info['total'])}，已使用 {calc_size(capacity_info['used'])}，剩余 {calc_size(capacity_info['free'])}"

# 检测 Access Token 是否到期
def is_expiration(access_token):
    '''False 为未到期，True 为到期'''
    if access_token['expiration']-86400 > int(time.time()): return False
    else: return True

# 保存 Access Token 到文件中
def Save_AccessToken(access_token, config_file=config_file):
    config = configparser.ConfigParser()
    config.add_section(f'Access_Token')
    config.set(f'Access_Token', 'expiration', str(access_token['expiration']))
    config.set(f'Access_Token', 'expires_in', str(access_token['expires_in']))
    config.set(f'Access_Token', 'refresh_token', str(access_token['refresh_token']))
    config.set(f'Access_Token', 'access_token', str(access_token['access_token']))
    config.set(f'Access_Token', 'session_secret', str(access_token['session_secret']))
    config.set(f'Access_Token', 'session_key', str(access_token['session_key']))
    config.set(f'Access_Token', 'scope', str(access_token['scope']))
    config.write(open(config_file, 'w', encoding='utf-8'))

# 从文件中加载 Access Token
def Load_AccessToken(config_file=config_file):
    config = configparser.ConfigParser()
    try:
        config.read(filenames=config_file, encoding='utf-8')
        expiration = config.get(f'Access_Token', 'expiration')
        expires_in = config.get(f'Access_Token', 'expires_in')
        refresh_token = config.get(f'Access_Token', 'refresh_token')
        access_token = config.get(f'Access_Token', 'access_token')
        session_secret = config.get(f'Access_Token', 'session_secret')
        session_key = config.get(f'Access_Token', 'session_key')
        scope = config.get(f'Access_Token', 'scope')
    except: return False
    else:
        access_token = {'expiration': int(expiration), 'expires_in': int(expires_in), 'refresh_token': refresh_token, 'access_token': access_token, 'session_secret': session_secret, 'session_key': session_key, 'scope': scope}
        return access_token

# 解密文件名
def decrypt_filename(filename, option):
    filename = re.sub('(-\d{8}-\d{6}.7z(\.\d{3})?)$', '', filename)
    try: decrypted = decrypt(filename.split('-')[0], option['key'], option['iv'])
    except: decrypted = filename
    return decrypted

# 获取百度网盘目录列表
def Get_File_list(path, access_token, listdir=False):
    '''listdir 默认为 False，即是否只返回文件夹，False 返回所有，True 只返回文件夹，且属性只返回 path 字段'''
    if listdir == True: folder = 1
    else: folder = 0
    data = {
        "method": "list", "web": "0", "start": "0", "desc": "1", "folder": folder, "limit": "1000", "order": "time",
        "access_token": access_token['access_token'],
        "dir": path,
    }

    url = f"https://pan.baidu.com/rest/2.0/xpan/file?{urllib.parse.urlencode(data)}"
    response = json.loads(requests.get(url=url).text)

    if response['errno'] == 0: return response['list']
    elif response['errno'] == -6 or response['errno'] == -9: Errno_Code(response['errno']); exit()
    else: print(f'未知错误\n{response}'); exit()

# 从 / 开始选择目录
def Choice_Dir(access_token, path='/'):
    while True:
        if path == '': path = '/'
        select_item = []
        for i in Get_File_list(path, access_token, listdir=True):
            select_item.append(i['path'])
        select_item.append('返回')
        select_item.append('确认')
        choice = pyinputplus.inputMenu(prompt=f"输入对应选项的数字，不输入则确认，当前目录：{path}\n", choices=select_item, numbered=True, default='确认', limit=1)
        if choice == '确认': return path
        elif choice == '返回': path = '/'.join(path.split('/')[:-1]); continue
        else: path = choice

# 根据 mtime 进行降序排序
def sort_by_mtime(data, reverse=False):
    '''根据 mtime 进行降序排序'''
    for l in range(len(data)):
        for r in range(l+1, len(data)):
            left = time.mktime(time.strptime(data[l]['mtime'], '%Y-%m-%d %H:%M:%S'))
            right = time.mktime(time.strptime(data[r]['mtime'], '%Y-%m-%d %H:%M:%S'))
            if left > right and reverse == False:
                data[l], data[r] = data[r], data[l]
            if left < right and reverse == True:
                data[l], data[r] = data[r], data[l]
    return data

# 计算输入二进制数据的 MD5 值
def md5_hash(binary):
    md5 = hashlib.md5()
    md5.update(binary)
    return md5.hexdigest()

# 检测百度网盘里是否存在该目录
def Have_Directory(path, access_token):
    '''检测百度网盘里是否存在该目录，则返回 True，否则返回 False'''
    path = re.sub('/$', '', path)
    upper_dir = '/'.join(path.split('/')[0:-1])
    if path.split('/')[-1] == '': upper_dir = '/'.join(path.split('/')[0:-2])
    if re.search(r'\/$|\\$', upper_dir) == None: upper_dir = upper_dir + '/'

    for i in Get_File_list(upper_dir, access_token, listdir=True):
        if path == i['path']: return True

    return False

# 在百度网盘上创建目录
def Create_Diretcory(path, access_token):
    '''在百度网盘上创建目录，返回创建的响应信息'''
    data = {"method": "create", "access_token": access_token['access_token']}
    payload = {'isdir': '1', "path": path}
    url = f"https://pan.baidu.com/rest/2.0/xpan/file?{urllib.parse.urlencode(data)}"
    response = json.loads(requests.post(url=url, data=payload).text)
    return response

### 上传 ###
# 计算文件分块后的 MD5 值
def calc_file_md5(file, block_size=32):
    '''block_size 单位 MiB，计算出来的 MD5 会保存到与文件相同的目录下'''
    logfile = open(f"{os.path.dirname(file)}\{os.path.basename(file)}.partmd5", 'w', encoding='utf-8')
    logfile.write(f"{len(str(block_size))}{str(block_size)}")
    with open(file, 'rb') as f:
        while f.tell() != os.path.getsize(file): logfile.write(md5_hash(f.read(block_size*1024*1024)))
    logfile.close()

# 上传文件
def Upload(fileinfo, baidu_path, access_token):
    '''fileinfo 的格式必须是 Public.Chose_Local_File() 的格式'''
    logfile = f"{fileinfo['path']}.partmd5"
    block_list = []
    with open(logfile, 'r', encoding='utf-8') as f:
        block_size = int(f.read(int(f.read(1))))
        while f.tell() != os.path.getsize(logfile): block_list.append(f.read(32))
    destpath = baidu_path + '/' + fileinfo['filename']
    print(f"正在上传 {fileinfo['path']} 到百度网盘 {destpath} 中")
    print(f"文件大小：{fileinfo['size_human']}，共 {len(block_list)} 个分片")

    # 预上传
    def PreUpload():
        url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=precreate&access_token={access_token['access_token']}"
        payload = {
            'rtype': '2', 'isdir': '0', 'autoinit': '1',
            'path': destpath,
            'size': fileinfo['size_byte'],
            'block_list': json.dumps(block_list)
        }
        PreUpload_response = json.loads(requests.post(url, data=payload).text)
        if PreUpload_response['errno'] == 0:
            if PreUpload_response['return_type'] == 2: print('文件已存在于云端，上传完成'); return 'Have File'
            elif PreUpload_response['return_type'] == 1: return PreUpload_response["uploadid"]
        else:
            print('PreUpload_response', PreUpload_response)
            return 'Failed'

    # 分片上传
    def PartUpload(uploadid):
        file = open(f"{fileinfo['path']}", 'rb')
        for part in block_list:
            data = {
                "method": "upload", "type": "tmpfile",
                "access_token": access_token['access_token'],
                "path": destpath,
                "uploadid": uploadid,
                "partseq": block_list.index(part),
            }
            url = f"https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?{urllib.parse.urlencode(data)}"
            PartUpload_response = json.loads(requests.post(url, files=[('file', file.read(block_size*1024*1024))]).text)
            print(f"\r上传分片进度：{block_list.index(part)+1} / {len(block_list)}，MD5：{PartUpload_response['md5']}".ljust(66), end='')

    # 创建文件
    def CreateFile():
        url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token={access_token['access_token']}"
        payload = {
            'rtype': '2', 'isdir': '0',
            'path': destpath,
            'size': fileinfo['size_byte'],
            'uploadid': uploadid,
            'block_list': json.dumps(block_list),
        }
        CreateFile_response = json.loads(requests.post(url, payload).text)
        if CreateFile_response['errno'] == 0:
            print("\n文件上传成功！")
            print(f"网盘文件 MD5：{CreateFile_response['md5']}")
            print(f"上传时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(CreateFile_response['ctime']))}")
            return True
        else:
            print('\n文件上传失败')
            print('CreateFile_response', CreateFile_response)
            return False

    uploadid = PreUpload()
    if uploadid == 'Have File' or uploadid == 'Failed': return uploadid
    PartUpload(uploadid)
    CreateFile_status = CreateFile()
    if CreateFile_status == True: return 'Success'
    else: return 'Failed'

# 递归创建目录，返回创建最后一个目录的响应数据
def Recursion_Create_Diretcory(path, access_token) -> bool | dict:
    path = re.sub(r'/+', '/', path)
    step = 2
    result = True
    # 从第一个目录开始，递归创建目录
    while step <= len(path.split('/')):
        if Have_Directory('/'.join(path.split('/')[:step]), access_token) == True: step += 1
        else:
            result = Create_Diretcory('/'.join(path.split('/')[:step]), access_token)

    return result



