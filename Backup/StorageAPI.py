import logging, time, os, json, urllib.parse, requests, configparser, re
from Public import calc_size, md5_hash

token_file = rf'{os.path.dirname(os.path.abspath(__file__))}/tokens.ini'

### Test ###
logging.basicConfig(format='[{levelname:^10s}] {asctime} - {message}', level=logging.DEBUG, style='{')

# 保存 Access Token 到文件中
def SaveAccessToken(APIName, Access_Token) -> None:
    global token_file
    config = configparser.ConfigParser()
    config.read(filenames=token_file, encoding='utf-8')
    config.add_section(APIName)
    for key in Access_Token:
        config.set(APIName, key, str(Access_Token[key]))
    config.write(open(token_file, 'w', encoding='utf-8'))

# 从文件中加载 Access Token
def LoadAccessToken(APIName) -> dict:
    global token_file
    if os.path.isfile(token_file):
        config = configparser.ConfigParser()
        Access_Token = {}
        config.read(filenames=token_file, encoding='utf-8')
        try:
            for key in config.items(APIName):
                Access_Token[key[0]] = key[1]
        except configparser.NoSectionError:
            logging.error(f'在 tokens.ini 中找不到此 API({APIName}) 的 Access Token 记录')
        else:
            return Access_Token
    else:
        logging.warning('用于存放 Access Token 的 tokens.ini 文件不存在')
    return False

# 百度网盘
class PanBaidu:
    # 初始化
    def __init__(self) -> None:
        self.access_token = LoadAccessToken('PanBaidu')
        self.app_info = {
            'AppKey': 'AppKey',
            'SecretKey': 'SecretKey',
            'SignKey': 'SignKey',
        }

        # 检查 Access Token 是否过期，过期则刷新，刷新失败则重新授权
        if self.access_token == False: self.GetAccessToken()
        if self.is_expiration():
            if self.RefreshAccessToken() == False: self.GetAccessToken()

        # 获取用户信息
        self.GetUserInfo()

        # 根据提供的用户信息，选择不同的分片大小，普通用户4M，普通会员16M，超级会员32M，小于分片大小的文件选择直接上传模式
        self.SetPartSize()

    # 设置分片大小（单位：MB）
    def SetPartSize(self, size: int=None):
        '设置分片大小（单位：MB）'
        if size == None:
            match self.user_info['vip_type']:
                case 1: size = 16
                case 2: size = 32
                case _: size = 4
        self.PartSize = size * 1024 * 1024

    # 错误处理
    def ErrnoParse(self, errno: int) -> bool:
        match errno:
            case 0: return True
            case -6: logging.error('身份验证失败，Cookie 已过期')
            case 111: logging.error('access token 失效，更新 access token')
            case 2: logging.error('参数错误')
            case 6: logging.error('不允许接入用户数据，建议10分钟之后用户再进行授权重试。')
            case 31034: logging.error('接口请求过于频繁，注意控制。')
            case -9: logging.error('文件或目录不存在')
            case -7: logging.error('文件或目录无权访问')
            case 10: logging.error('转存文件已经存在')
            case _: logging.error(f'其他错误：{errno}')
        return False

    # 检查 Access Token 是否过期
    def is_expiration(self) -> bool:
        '''未到期返回 False，到期返回 True'''
        if int(self.access_token['expiration'])-86400 > int(time.time()): return False
        else: return True

    # 授权应用获取 Access Token
    def GetAccessToken(self) -> None:
        while True:
            code = ''
            if code == '':
                print(f"在浏览器中打开此链接：http://openapi.baidu.com/oauth/2.0/authorize?response_type=code&client_id={self.app_info['AppKey']}&redirect_uri=oob&scope=basic,netdisk&")
                code = input('在此输入授权码：')
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self.app_info['AppKey'],
                "client_secret": self.app_info['SecretKey'],
                "redirect_uri": "oob",
            }
            url = f"https://openapi.baidu.com/oauth/2.0/token?{urllib.parse.urlencode(data)}"
            access_token = json.loads(requests.get(url).text)
            access_token['expiration'] = access_token['expires_in'] + int(time.time())

            if "error" in access_token.keys():
                logging.info('授权码无效，授权码已过期或已吊销')
                code = ''
            elif "access_token" in access_token.keys():
                logging.info('成功获取 Access Token，已更新 tokens.ini')
                self.access_token = access_token
                SaveAccessToken('PanBaidu', access_token)
                return

    # 刷新 Access Token
    def RefreshAccessToken(self) -> bool:
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.access_token['refresh_token'],
            "client_id": self.app_info['AppKey'],
            "client_secret": self.app_info['SecretKey'],
        }
        url = f"https://openapi.baidu.com/oauth/2.0/token?{urllib.parse.urlencode(data)}"
        access_token = json.loads(requests.get(url).text)
        access_token['expiration'] = access_token['expires_in'] + int(time.time())
        if "access_token" in access_token.keys():
            logging.info('刷新 Access Token 成功，已更新 tokens.ini')
            self.access_token = access_token
            SaveAccessToken('PanBaidu', access_token)
        else:
            logging.info('刷新 Access Token 失败')
            return False

    # 获取用户信息
    def GetUserInfo(self) -> None:
        access_token = self.access_token['access_token']

        # 获取用户信息
        user_info_url = f"https://pan.baidu.com/rest/2.0/xpan/nas?access_token={access_token}&method=uinfo"
        user_info = json.loads(requests.get(user_info_url).text)

        # 获取网盘容量信息
        capacity_info_url = f"https://pan.baidu.com/api/quota?access_token={access_token}&checkfree=1"
        capacity_info = json.loads(requests.get(capacity_info_url).text)

        if self.ErrnoParse(user_info['errno']) and self.ErrnoParse(capacity_info['errno']):
            if user_info['netdisk_name'] == '':
                user_info['netdisk_name'] = user_info['baidu_name']
            user_info['capacity_total'] = capacity_info['total']
            user_info['capacity_expire'] = capacity_info['expire']
            user_info['capacity_used'] = capacity_info['used']
            user_info['capacity_free'] = capacity_info['free']
            self.user_info = user_info
        else:
            self.user_info = None

    # 显示用户信息
    def ShowUserInfo(self) -> None:
        user_info = self.user_info
        infos = f"{user_info['netdisk_name']} 的网盘，总容量：{calc_size(user_info['capacity_total'])}，已使用 {calc_size(user_info['capacity_used'])}，剩余 {calc_size(user_info['capacity_free'])}"
        print(infos)

    # 获取目录列表
    def GetFileList(self, path, listdir: bool=False) -> list:
        '''listdir 默认为 False，即是否只返回文件夹，False 返回所有，True 只返回文件夹，且属性只返回 path 字段'''
        if listdir == True: folder = 1
        else: folder = 0
        data = {
            "method": "list", "web": "0", "start": "0", "desc": "1", "folder": folder, "limit": "1000", "order": "time",
            "access_token": self.access_token['access_token'],
            "dir": path,
        }

        url = f"https://pan.baidu.com/rest/2.0/xpan/file?{urllib.parse.urlencode(data)}"
        response = json.loads(requests.get(url=url).text)

        if self.ErrnoParse(response['errno']):
            return response['list']
        else:
            return None

    # 检测百度网盘里是否存在该目录
    def HasDir(self, path) -> bool:
        '''检测百度网盘里是否存在该目录，则返回 True，否则返回 False'''
        path = re.sub('/$', '', path)
        upper_dir = '/'.join(path.split('/')[0:-1])
        if path.split('/')[-1] == '': upper_dir = '/'.join(path.split('/')[0:-2])
        if re.search(r'\/$|\\$', upper_dir) == None: upper_dir = upper_dir + '/'

        for i in self.GetFileList(upper_dir, listdir=True):
            if path == i['path']: return True
        return False

    # 在百度网盘上创建目录
    def CreateDiretcory(self, path) -> dict:
        '''在百度网盘上创建目录，返回创建的响应信息'''
        data = {"method": "create", "access_token": self.access_token['access_token']}
        payload = {'isdir': '1', "path": path}
        url = f"https://pan.baidu.com/rest/2.0/xpan/file?{urllib.parse.urlencode(data)}"
        response = json.loads(requests.post(url=url, data=payload).text)
        return response

    # 递归创建目录，返回创建最后一个目录的响应数据
    def RecursionCreateDiretcory(self, path) -> bool | dict:
        path = re.sub(r'/+', '/', path)
        step = 2
        result = True
        # 从第一个目录开始，递归创建目录
        while step <= len(path.split('/')):
            if self.HasDir('/'.join(path.split('/')[:step])) == True: step += 1
            else:
                result = self.CreateDiretcory('/'.join(path.split('/')[:step]))

        return result


    # 上传文件
    # Test
    def Upload(self, local_path: str, remote_path: str):
        local_path = re.sub(r'\\', '/', local_path)
        block_list = []
        access_token = self.access_token['access_token']
        file_size = os.path.getsize(local_path)
        # 任务文件
        task_file = "{}/{}.UploadTask.json".format(os.path.dirname(local_path), re.sub(r'(\.\w+)$', '', os.path.basename(local_path)))
        if os.path.exists(task_file):
            data = json.load(open(task_file, 'r', encoding='utf-8'))
        else:
            data = {
                'local_path': local_path, 
                'remote_path': remote_path, 
                'block_size': self.PartSize, 
                'block_list': block_list,
                'finish_block': [],
            }
            json.dump(data, open(task_file, 'w', encoding='utf-8'), indent=4)

        # 分片
        if data['block_list'] != []:
            block_list = data['block_list']
        else:
            with open(local_path, 'rb') as f:
                while f.tell() != os.path.getsize(local_path):
                    block_list.append(md5_hash(f.read(self.PartSize)))

        # 预上传
        if 'uploadid' not in data.keys():
            url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=precreate&access_token={access_token}"
            payload = {
                'rtype': '2', 'isdir': '0', 'autoinit': '1',
                'path': remote_path,
                'size': file_size,
                'block_list': json.dumps(block_list)
            }
            PreUpload_response = json.loads(requests.post(url, data=payload).text)
            if self.ErrnoParse(PreUpload_response['errno']):
                if PreUpload_response['return_type'] == 2:
                    logging.info('文件已存在于云端，上传完成')
                    return 'Have File'
                elif PreUpload_response['return_type'] == 1:
                    uploadid = PreUpload_response["uploadid"]
            else:
                return 'Failed'

            data['uploadid'] = uploadid
            json.dump(data, open(task_file, 'w', encoding='utf-8'), indent=4)
        else:
            uploadid = data['uploadid']

        # 分片上传
        from PanBaidu_PartUpload import PartUpload
        result = PartUpload(
            items=list(range(len(block_list))), 
            task_file=task_file,
            access_token=access_token,
            thread=4
        )

        # 创建文件
        if result == 'Success':
            url = f"https://pan.baidu.com/rest/2.0/xpan/file?method=create&access_token={access_token}"
            payload = {
                'rtype': '2', 'isdir': '0',
                'path': remote_path,
                'size': file_size,
                'uploadid': uploadid,
                'block_list': json.dumps(block_list),
            }
            CreateFile_response = json.loads(requests.post(url, payload).text)
            if self.ErrnoParse(CreateFile_response['errno']):
                os.remove(task_file)
                logging.info(f"文件上传成功！上传时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(CreateFile_response['ctime']))}")
                return 'Success'
            else:
                logging.info('文件上传失败')
                return 'Failed'
        else:
            logging.info('文件上传失败')
            return 'Failed'
