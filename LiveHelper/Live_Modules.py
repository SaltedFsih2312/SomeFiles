import time, json, re, os, configparser, pymediainfo, random, requests
import obsws_python as obs

# 模块版本
def Live_Ver(): return '20230720'

# OBS websocket 客户端
def OBS_Client(host: str, port: str, password: str, need_obs: bool = True, quite: bool = False):
    try:
        return obs.ReqClient(host=host, port=port, password=password)
    except:
        if quite == False:
            print('检查 OBS 是否启动，并启用 websocket：工具——obs-websocket 设置\n若 OBS 版本低于 28 则需要额外安装 websocket 插件\n')
            print('打开设置后需要配置以下参数：开启 WebStocket 服务器、生成密码\n点击显示连接信息后将服务器 IP、端口、密码分别填入到 Auto_Live.ini 中')
        if need_obs == True: exit()
        return False

# 切换文件
def Switch_File(client, path):
    temp_settings = client.get_input_settings('Auto_Live_Media').input_settings
    temp_settings['local_file'] = path
    client.set_input_settings('Auto_Live_Media', temp_settings, True)

# 切换 OBS 媒体源文件
def Switch_OBS_Media_File(client, file_list: list, effective_time: int, switch_media_method: str=('order', 'random')):
    # 按顺序
    if switch_media_method == 'order':
        for i in file_list:
            if effective_time > int(i['duration']):
                Switch_File(client, i['path'])
                effective_time -= int(i['duration'])
                print(f'切换视频 {i["path"]}，下次切换将在 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + int(i["duration"]) + 2))}')

                time.sleep(int(i['duration']) + 2)

            elif int(i['duration']) > effective_time >= 0:
                Switch_File(client, i['path'])
                effective_time -= int(i['duration'])
                print(f'切换视频 {i["path"]}，此视频播放完就下播，预计下播时间 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + (int(i["duration"]) + effective_time)))}')

                time.sleep(int(i['duration']) + effective_time)

    # 随机切换
    elif switch_media_method == 'random':
        while effective_time > 0:
            choice = random.choice(file_list)
            file_list.remove(choice)

            Switch_File(client, choice['path'])
            effective_time -= int(choice['duration'])

            if effective_time > 0:
                print(f'切换视频 {choice["path"]}，下次切换将在 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + int(choice["duration"]) + 2))}')
                time.sleep(int(choice['duration']) + 2)

            elif effective_time <= 0:
                print(f'切换视频 {choice["path"]}，此视频播放完就下播，预计下播时间 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + (int(choice["duration"]) + effective_time)))}')
                time.sleep(int(choice['duration']) + effective_time)

# 开播
def Start_Live(cookies, area_v2: str = '000', raw=False):
    headers = {
        "Cookie": cookies,
        "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="104"',
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63",
        "Origin": "https://link.abc.com",
        "Referer": "https://link.abc.com"
    }

    csrf = re.sub('abc_jct=', '', re.search(r'abc_jct=(\w){32}?', cookies).group())

    room_id = json.loads(requests.get(url="https://api.live.abc.com/xlive/app-blink/v1/streamingRelay/relayInfo", headers=headers).text)
    if room_id['code'] ==  -123: print(room_id['message'])

    data = {'room_id': room_id['data']['room_id'], 'platform': 'pc', 'area_v2': area_v2, 'csrf_token': csrf, 'csrf': csrf}
    response = requests.post(url="https://api.live.abc.com/room/v1/Room/startLive", data=data, headers=headers).text

    if raw == True: return response, room_id
    return json.loads(response), room_id

# 下播
def Stop_Live(cookies, raw=False):
    headers = {
        "Cookie": cookies,
        "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="104"',
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63",
        "Origin": "https://link.abc.com",
        "Referer": "https://link.abc.com"
    }

    csrf = re.sub('abc_jct=', '', re.search(r'abc_jct=(\w){32}?', cookies).group())

    room_id = json.loads(requests.get(url="https://api.live.abc.com/xlive/app-blink/v1/streamingRelay/relayInfo", headers=headers).text)
    if room_id['code'] ==  -123: print(room_id['message'])

    data = {'room_id': room_id['data']['room_id'], 'platform': 'pc', 'csrf_token': csrf, 'csrf': csrf}
    response = requests.post(url="https://api.live.abc.com/room/v1/Room/stopLive", data=data, headers=headers).text

    if raw == True: return response
    return json.loads(response)

# 获取配置样例
def get_example_conf():
    example_conf = ''''''

    print(example_conf)

# 调整当前直播分区
def Change_Area(area_id: int, cookies: str=''):
    headers = {
        "Cookie": cookies,
        "Sec-Ch-Ua": '" Not A;Brand";v="99", "Chromium";v="104"',
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.102 Safari/537.36 Edg/104.0.1293.63",
        "Origin": "https://link.abc.com",
        "Referer": "https://link.abc.com"
    }

    room_id = json.loads(requests.get(url="https://api.live.abc.com/xlive/app-blink/v1/streamingRelay/relayInfo", headers=headers).text)
    if room_id['code'] ==  -123: print(room_id['message'])
    headers['Referer'] += f"/{room_id['data']['room_id']}"

    # 从 Cookie 中获取 csrf
    csrf = re.sub('abc_jct=', '', re.search(r'abc_jct=(\w){32}?', cookies).group())

    # 调整当前分区
    data = {'room_id': room_id['data']['room_id'], 'area_id': area_id, 'platform': 'pc', 'csrf_token': csrf, 'csrf': csrf}
    response = json.loads(requests.post(url="https://api.live.abc.com/room/v1/Room/update", headers=headers, data=data).text)
    if response['code'] == 0: return True

# 加载数据
class Load_Data:
    config_file = rf'{os.path.dirname(os.path.abspath(__file__))}/Auto_Live.ini'

    # 配置 configparser
    def config(config_file=config_file):
        if os.path.isfile(config_file) == True:
            config = configparser.ConfigParser()
            config.read(filenames=config_file, encoding='utf-8')
            return config
        else: 
            print('配置文件不存在')
            exit()

    # 加载直播设置
    def Live_Settings(config_file=config_file):
        live_settings = {}
        config = Load_Data.config(config_file=config_file)
        for i in config.items('Live_Settings'):
            live_settings[i[0]] = i[1]
        
        if len(live_settings) == 0:
            print('配置文件中缺少 [Live_Settings]'); exit()

        return live_settings

    # 加载活动配置
    def Active_Settings(config_file=config_file, prefix=''):
        def duration(path):
            try:
                file_info = json.loads(pymediainfo.MediaInfo.parse(path).to_json())
                duration = int(file_info['tracks'][0]['duration'] / 1000)
            except:
                print(f"找不到文件 {path}")
                duration = 0
            return duration

        config = Load_Data.config(config_file=config_file)
        result = {'files': []}

        if prefix != '' and prefix.endswith('_') == False: prefix += '_'
        section = f'{prefix}Settings'

        if section in config.sections():
            options = config.options(section)
            files = [i for i in options if 'file' in i]
            settings = list(set(options).difference(files))
            for i in settings: result[i] = config.get(section, i)
            for i in files:
                path = re.sub(r'[/\\]+$', '', re.sub(r'[\\/]+', '/', config.get(section, i)))
                result['files'].append({'path': path, 'duration': duration(path)})

            if len(result['files']) == 0: result['files'].append({'path': '', 'duration': 86400})

            return result
        else:
            raise ValueError(f'未添加活动配置 {prefix}')

