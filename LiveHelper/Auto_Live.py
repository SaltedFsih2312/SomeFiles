
import argparse, os, pyinputplus, time, multiprocessing, random
from modules import Choices_Cookie, Config_Manage, Check_Cookie, Mod_Ver, timing, Receive_Reward, live_time, Check_Proxy
from Live_Modules import Load_Data, Live_Ver, OBS_Client, Switch_OBS_Media_File, Switch_File, Start_Live, Stop_Live, get_example_conf, Change_Area

version = '20231012Test' + f', Mod_Ver: {Mod_Ver()}, Live_Ver: {Live_Ver()}'

# 运行环境检测并配置
if __name__ == '__main__':
    # 检查系统是否有代理设置
    Check_Proxy()

    # 检测参数
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-c', '--cookie', metavar="Num", type=int, nargs=1, help="输入配置文件中 Cookie 的序号")
    parser.add_argument('-m', action='store_true', help="需要领取任务奖励时使用")
    parser.add_argument('--delay', help="对指定的每日任务的运行时间进行延迟，可选值：10，60，120，用 , 分隔")
    parser.add_argument('--no-daily', action='store_true', help="不领取每日任务奖励，只直播")
    parser.add_argument('--count', action='store_true', help="统计添加的视频文件总时长，统计完会退出")
    parser.add_argument('--stop-live', action='store_true', help="停止直播，特殊情况下才使用，例如程序崩溃了没有按程序正常下播")
    parser.add_argument('--get-example', action='store_true', help="查看样例配置")
    parser.add_argument('-v', '--version', action='version', version=version, help="输出当前脚本的版本信息")

    group0 = parser.add_mutually_exclusive_group()
    group0.add_argument('--timing', default=False, nargs='?', help="定时运行，格式：hhmmss")
    group0.add_argument('--next-day', action='store_true', help="完成下一天的任务，当天的不完成，并等待到 23 点 45 分开始")
    # 选择活动类型
    act_type = parser.add_mutually_exclusive_group()
    act_type.add_argument('--xx', action='store_true', help="参与活动：XX")
    act_type.add_argument('--yy', action='store_true', help="参与活动：YY")

    args = parser.parse_args()

    # 如果没有选择活动类型，则设置为XX
    act_type_selected = args.xx + args.yy
    if act_type_selected == 0:
        print('没有指定活动，默认选择XX，使用 -h 查看活动相关选项')
        args.xx = True

    # 设置数据前缀
    if args.xx == True:
        print('参与活动：XX')
        prefix = "xx_"
        area_id = 000
        area_name = 'xx'
    elif args.yy == True:
        print('参与活动：YY')
        prefix = "yy_"
        area_id = 000
        area_name = 'yy'

    # 获取配置样例
    if args.get_example == True:
        get_example_conf()
        exit()

    # 加载每日任务列表
    try: daily_task_list = Config_Manage.Load_Data.Daily_Task(prefix=prefix)
    except: print('加载每日任务列表失败，请使用 Config_Manage.py 添加数据后继续使用'); exit()

    # 加载活动配置
    try: 
        act_settings = Load_Data.Active_Settings(prefix=prefix)
        file_list = act_settings['files']
    except: print('加载活动配置失败，请检查配置文件'); exit()

    # 加载直播配置
    try: live_settings = Load_Data.Live_Settings()
    except: print('加载直播配置失败，请检查配置文件'); exit()

    # 检查配置
    live_settings_options = ['obs_ws_address', 'obs_ws_port', 'obs_ws_password', 'browser']
    act_settings_options =['next_day_start_time', 'switch_media_method', 'effective_time']
    not_in = []
    for i in live_settings_options:
        if i not in live_settings: not_in.append(i)
    # 如果 browser 没有设置，则设置一个默认值
    if 'browser' in not_in:
        live_settings['browser'] = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        not_in.remove('browser')    
    if len(not_in) != 0:
        print(f'配置文件中缺少以下参数，请根据注释添加：{not_in}，使用 --get-example 查看样例配置'); exit()

    # 有效时长
    effective_time = int(act_settings['effective_time'])
    # 切换视频文件的方式，按列表顺序、随机
    switch_media_method = act_settings['switch_media_method']
    # 跨天直播时当天的开始时间（不是下一天）
    next_day_start_time = act_settings['next_day_start_time']

    # 统计添加的视频文件总时长
    duration_count = 0
    for i in file_list: duration_count += i['duration']
    # 显示视频可播放时长
    print(f"添加的视频文件可以播放 {duration_count // 3600} 小时 {(duration_count % 3600) // 60} 分 {(duration_count % 3600) % 60} 秒")
    # 使用选项查看时应该只是用作确认，所以直接退出
    if args.count == True: exit()

    # 加载 Cookie
    if args.cookie == None: cookies = Choices_Cookie(cookies_list=Config_Manage.Load_Data.Cookie())
    else: cookies = Config_Manage.Load_Data.Cookie()[args.cookie[0]]['cookies']

    # 检查 Cookie 有效性
    cookie_validity = Check_Cookie(cookies=cookies)[1]
    if cookie_validity['code'] == -123:
        print("Cookie 失效，请重新获取 Cookie"); exit()
    elif cookie_validity['code'] == 0:
        name = cookie_validity['data']['uname']
        print(f"当前用户：{cookie_validity['data']['uname']}")
        print(live_time(area_id, area_name, cookies))

    # 配置 OBS 客户端
    client = OBS_Client(live_settings['obs_ws_address'], live_settings['obs_ws_port'], live_settings['obs_ws_password'])
    # 当前配置配置文件
    current_profile_name = client.get_profile_list().current_profile_name
    print('全程由程序控制，不要有人为控制 OBS 的操作。如果程序进入等待开始的状态后，重启 OBS 后程序也需要重启')

    # 如果 OBS 场景集合没有 Auto_Live，则创建一个
    if 'Auto_Live' not in client.get_scene_collection_list().scene_collections: client.create_scene_collection('Auto_Live')
    # 如果当前场景集合不是 Auto_Live 则切换场景集合为 Auto_Live
    if 'Auto_Live' != client.get_scene_collection_list().current_scene_collection_name:
        client.set_current_scene_collection('Auto_Live')
    print('切换到场景集合 Auto_Live，如果需要切换回去在：顶部场景集合——[列表下面]')

    # 如果来源没有 Auto_Live_Media 则创建一个
    if {'inputKind': 'ffmpeg_source', 'inputName': 'Auto_Live_Media', 'unversionedInputKind': 'ffmpeg_source'} not in client.get_input_list().inputs:
        input_settings = client.get_input_default_settings('ffmpeg_source').default_input_settings
        input_settings['hw_decode'] = True
        input_settings['local_file'] = ''
        client.create_input('场景', 'Auto_Live_Media', 'ffmpeg_source', input_settings, True)

    ### 计算总直播时间线 ###
    now = int(time.time())
    if args.next_day == True:
        now_day = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime()), '%Y-%m-%d')))
        next_day = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime(now_day + 86400)), '%Y-%m-%d')))
        now = next_day
        start_time = int(time.mktime(time.strptime(time.strftime('%Y-%m-%d', time.localtime()) + next_day_start_time, '%Y-%m-%d%H%M%S')))
        end_time = now_day + 86400 + effective_time
        # 总直播时长
        effective_time = end_time - start_time
    else:
        start_time = now

        # 如果设置了定时，就不减当天直播的时间
        if args.timing != False:
            if args.timing == None:
                runtime = pyinputplus.inputTime(prompt="请输入开始的时间，如果输入的时间早于当前时间则会加一天。格式：hhmmss，默认值：000100\n", formats=['%H%M%S'], default='00:01:00', limit=1)
                runtime = time.mktime(time.strptime(time.strftime('%Y%m%d', time.localtime()) + str(runtime), '%Y%m%d%H:%M:%S'))
            else:
                runtime = args.timing
                runtime = time.mktime(time.strptime(time.strftime('%Y%m%d', time.localtime()) + str(runtime), '%Y%m%d%H%M%S'))

            if int(runtime) < int(time.time()): runtime += 86400
            start_time = runtime
        else:
            # 根据已直播时间减去相应的秒数
            effective_time -= live_time(area_id, area_name, cookies, True)

        end_time = now + effective_time

    if effective_time < 0: effective_time = 0
    else:
        # 随机额外添加直播时长，避免每次直播时间相同
        random_add = random.randrange(60,300)
        print(f'有效时长增加 {random_add} 秒，防止多次直播时长相同')
        effective_time += random_add

    # 显示需要直播的时间
    print(f'需要直播 {effective_time // 3600} 小时 {(effective_time % 3600) // 60} 分 {(effective_time % 3600) % 60} 秒，有效时长 {effective_time} 秒，预计下播时间 {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time + effective_time))}')

    # 领取任务奖励开始时间
    running_time = {}
    # 领取连续观看满 10 分钟任务奖励的开始时间（000950）
    running_time['10'] = now + 600 - 10
    # 领取当日开播＞60分钟任务奖励的开始时间（005950）
    running_time['60'] = now + 3600 - 10
    # 领取当日开播＞120分钟任务奖励的开始时间（015950）
    running_time['120'] = now + 7200 - 10

    # 根据设置对每日任务运行时间进行延迟
    if args.delay != None:
        try:
            # 去重
            for a in list(set([str(int(a)) for a in args.delay.split(',')])):
                try:
                    running_time[a] += 120
                    print('任务延迟执行', a)
                except: print('无法延迟任务：无法匹配', a)
        except: pass

    on_live = False

# 定时开始
if __name__ == '__main__' and True:
    if args.timing != False:
        timing(runtime)
    elif args.next_day == True:
        # 等待到开始时间
        timing(start_time)

# 开播
if __name__ == '__main__' and True:
    if args.stop_live == False and effective_time > 0:
        on_live = True
        # XYZ开播
        xyz_response = Start_Live(cookies)
        if xyz_response[0]['data']['status'] == "LIVE": print('已在 XYZ开播')

        # 调整当前分区
        if Change_Area(area_id, cookies) == True: print(f'已将当前分区调整为{area_name}分区')

        rtmp_addr = xyz_response[0]['data']['rtmp']['addr']
        rtmp_code = xyz_response[0]['data']['rtmp']['code']
        room_id = xyz_response[1]
        live_url = f"http://live.xyz.com/{room_id['data']['room_id']}"

        # 打开浏览器
        os.system(f'cmd /C start "" {live_settings["browser"]} {live_url}')
        print('打开浏览器观看直播，需要手动关闭网页')

        # 如果正在推流则停止推流
        if client.get_stream_status().output_active == True: client.stop_stream()

        # 检测推流参数是否符合当前用户
        stream_service_settings = client.get_stream_service_settings().stream_service_settings
        # 如果推流配置中的推流码不同则替换为新的推流码
        if stream_service_settings['key'] != rtmp_code: 
            stream_service_settings['key'] = rtmp_code
            client.set_stream_service_settings('rtmp_custom', stream_service_settings)
        # 如果推流配置中的推流地址不同则替换为新的推流地址
        if stream_service_settings['server'] != rtmp_addr: 
            stream_service_settings['server'] = rtmp_addr
            client.set_stream_service_settings('rtmp_custom', stream_service_settings)

        # OBS 开始推流
        client.start_stream()
        print('OBS 开始推流')

# 创建领取任务奖励进程
if __name__ == '__main__' and True:
    if args.stop_live == False and args.no_daily == False:
        thread_pool = []
        keep_going, detail, silent, before_task_status = False, False, True, True
        for i in daily_task_list:
            if '10分钟' in i['task_name']:
                if effective_time >= 600:
                    print(f"任务 {i['task_name']} 将在 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(running_time['10']))} 开始")
                    # thread_pool.append(multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '10', keep_going, detail, running_time['10'], silent, before_task_status), name=i['task_name']))
                    multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '10', keep_going, detail, running_time['10'], silent, before_task_status), name=i['task_name']).start()
                else: print(f"有效时长无法满足 {i['task_name']} 的完成条件，故不启动该任务")
            elif '60分钟' in i['task_name']:
                if effective_time >= 3600:
                    print(f"任务 {i['task_name']} 将在 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(running_time['60']))} 开始")
                    # thread_pool.append(multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '60', keep_going, detail, running_time['60'], silent, before_task_status), name=i['task_name']))
                    multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '60', keep_going, detail, running_time['60'], silent, before_task_status), name=i['task_name']).start()
                else: print(f"有效时长无法满足 {i['task_name']} 的完成条件，故不启动该任务")
            elif '120分钟' in i['task_name']:
                if args.m == False:
                    if effective_time >= 7200:
                        print(f"任务 {i['task_name']} 将在 {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(running_time['120']))} 开始")
                        # thread_pool.append(multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '120', keep_going, detail, running_time['120'], silent, before_task_status), name=i['task_name']))
                        multiprocessing.Process(target=Receive_Reward, args=(i['single_task_url'], cookies, '120', keep_going, detail, running_time['120'], silent, before_task_status), name=i['task_name']).start()
                    else: print(f"有效时长无法满足 {i['task_name']} 的完成条件，故不启动该任务")
                else: print('本次直播需要领取任务奖励，将暂停领取开播 2 小时的奖励')

        # for thread in thread_pool: thread.start()
    else:
        print('本次运行不需要领取每日任务奖励')

# 直播中切换视频
if __name__ == '__main__' and True:
    if args.stop_live == False and on_live == True:
    # if args.stop_live == False and True:
        print('此时可以使用 Ctrl + C 来结束切换视频的过程，直接到下播环节')
        try:
            Switch_OBS_Media_File(client, file_list, effective_time, switch_media_method)
        except KeyboardInterrupt: pass

# 下播
if __name__ == '__main__' and True:
    if on_live == True or args.stop_live == True:
        # 下播时间
        print(f"下播时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")

        # OBS 停止推流
        try: client.stop_stream()
        except: pass
        print('OBS 停止推流')

        # XYZ下播
        xyz_response = Stop_Live(cookies)
        if xyz_response['data']['status'] == "PREPARING":
            print('XYZ已关播')

        # 确保每次第一次开 OBS 时，这个源是黑屏的
        Switch_File(client, '')

        # 显示直播时长
        print(live_time(area_id, area_name, cookies))

        # 强制退出，结束所有子进程
        exit()
