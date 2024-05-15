from modules import Check_Proxy, Mod_Ver, Choices_Cookie, Config_Manage, live_time, Check_Cookie
from Live_Modules import OBS_Client, Load_Data, Start_Live, Stop_Live, Change_Area, Live_Ver
import argparse

version = '20230609' + f', Mod_Ver: {Mod_Ver()}, Live_Ver: {Live_Ver()}'

# 检查系统是否有代理设置
Check_Proxy()

# 检测参数
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('-c', '--cookie', metavar="Num", type=int, nargs=1, help="输入配置文件中 Cookie 的序号")
parser.add_argument('--with-obs', action='store_true', help="联动 OBS，自动配置、开播推流、下播关闭推流")
action = parser.add_mutually_exclusive_group()
action.add_argument('--start-live', action='store_true', help="开始直播")
action.add_argument('--stop-live', action='store_true', help="停止直播")

# 选择活动类型
act_type = parser.add_mutually_exclusive_group()
act_type.add_argument('--aa', action='store_true', help="参与活动：AA")
act_type.add_argument('--bb', action='store_true', help="参与活动：BB")

args = parser.parse_args()

# 如果没有选择活动类型，则设置为AA
act_type_selected = args.aa + args.bb
if act_type_selected == 0:
    print('没有指定活动，默认选择AA，使用 -h 查看活动相关选项')
    args.aa = True

# 设置数据前缀
if args.aa == True:
    print('参与活动：AA')
    prefix = "aa_"
    area_id = 000
    area_name = 'aa'
elif args.bb == True:
    print('参与活动：BB')
    prefix = "bb_"
    area_id = 000
    area_name = 'bb'

# 加载直播配置
try: live_settings = Load_Data.Live_Settings()
except: pass
# 配置 OBS 客户端
client = OBS_Client(live_settings['obs_ws_address'], live_settings['obs_ws_port'], live_settings['obs_ws_password'], need_obs=False)

# 选择 Cookie
if args.cookie == None: cookies = Choices_Cookie(cookies_list=Config_Manage.Load_Data.Cookie())
else: cookies = Config_Manage.Load_Data.Cookie()[args.cookie[0]]['cookies']

print(f"当前用户：{Check_Cookie(cookies=cookies)[1]['data']['uname']}")
print(live_time(area_id, area_name, cookies))

if args.start_live == True:
    response = Start_Live(cookies)
    rtmp_addr = response[0]['data']['rtmp']['addr']
    rtmp_code = response[0]['data']['rtmp']['code']
    room_id = response[1]
    print(f"{response[0]['data']['status']}\n直播间：http://live.efgefg.com/{room_id['data']['room_id']}\nrtmp_addr: {rtmp_addr}\n推流码：{rtmp_code}")

    # 切换分区
    if Change_Area(area_id, cookies) == True: print(f'已将当前分区调整为{area_name}分区')

    if client != False:
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

elif args.stop_live == True:
    if client != False:
        # OBS 停止推流
        try: client.stop_stream()
        except: pass
        print('OBS 停止推流')

    response = Stop_Live(cookies)
    if response['data']['status'] == "PREPARING":
        print('下班咯~')
        print(live_time(area_id, area_name, cookies))
