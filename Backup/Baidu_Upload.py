import sys, os, re
from Baidu_Modules import Load_AccessToken, Get_AccessToken, Save_AccessToken, is_expiration, Refresh_AccessToken, Get_User_Info, Choice_Dir, calc_file_md5, Upload, Recursion_Create_Diretcory
from table import *
from Public import Chose_Local_File, Load_Config, Package_File, calc_size, list_files

access_token = Load_AccessToken()
if access_token == False:
    print('加载 Access Token 失败，检查 config.ini 文件')
    access_token = Get_AccessToken()
    Save_AccessToken(access_token=access_token)

if is_expiration == True: Refresh_AccessToken(); access_token = Load_AccessToken()

print(Get_User_Info(access_token))


options = {}


# 指定本地目录
print('第一个参数指定本地目录，默认当前目录，第二个参数指定百度网盘上的文件目录，使用 - 来代表当前目录')

# 检测第一个参数是否存在，不存在则使用当前目录
try:
    options['local_path'] = sys.argv[1]

    # 存在则判断是否为 -，是则使用当前目录
    if options['local_path'] == '-':
        options['local_path'] = os.getcwd()

    if os.path.isdir(options['local_path']) == False: 
        print('提供的路径不是一个目录，将使用当前目录')
        raise
except:
    options['local_path'] = os.getcwd()

options['local_path'] = re.sub(r'[/\\]+$', '', re.sub(r'[\\/]+', '/', options['local_path'])) + '/'    # 不管路径末尾是否有斜杠都变成 /


# if len(sys.argv) == 1 or sys.argv[1] == '-': local_path = os.getcwd()
# else: local_path = os.path.abspath(sys.argv[1])
# local_path = re.sub(r'[/\\]+$', '', local_path) + '/'    # 不管路径末尾是否有斜杠都变成 /


# 选择百度网盘上的目录路径作为基本路径
try: options['baidu_path'] = sys.argv[2]
except: options['baidu_path'] = Choice_Dir(access_token, path='/')

# if len(sys.argv) > 2: baidu_path = sys.argv[2]
# else: baidu_path = Choice_Dir(access_token, path='/')


### 上传方式 ###
print('选择上传方式')
row = [
    {'num': '0', 'dest': '直接将选择的文件或目录上传，直接上传，默认选项'},
    {'num': '1', 'dest': '在直接上传的基础上根据目录结构上传，结构上传'},
    {'num': '2', 'dest': '将选择目录下的所有文件和选择的文件上传到一个目录下，扁平上传'},
]
table(column=['num', 'dest'], row=row, alias={'num': '序号', 'dest': '描述'})
upload_type = input('请选择上传方式，输入序号：')
if re.match('^[012]$', upload_type) == None: upload_type = '0'


# 获取目录下的文件列表
chose_replace = Chose_Local_File(options['local_path'])
file_list = []

### 结构上传，处理文件参数列表 ###
if upload_type == '1':
    # 临时存储文件元数据的列表
    temp_file_list = []
    switch = input('结构上传时的路径处理，默认以相对路径进行上传（a|绝对/r|相对）：')
    if switch == 'a' or switch == 'r': pass
    else: switch = 'r'

    # 使用目录列表，分析要上传文件需要的目录，检索目标目录
    dir_list = []

    # 遍历目录将文件处理成文件参数格式
    for i in chose_replace:
        count = 0
        if i['isdir'] == '1': 
            for file_path in list_files(i['path']):
                file_para = {'num': f"{i['num']}-{count}", 'filename': os.path.basename(file_path), 
                            'size_byte': os.path.getsize(file_path), 'size_human': calc_size(os.path.getsize(file_path)), 
                            'path': file_path, 'packtype': '', 'status': '', 'isdir': '0'}
                temp_file_list.append(file_para)
                count += 1
        elif i['isdir'] == '0': 
            temp_file_list.append(i)

    for i in temp_file_list:
        # {'num': 0, 'filename': 'file.txt', 'size_byte': 0, 'size_human': '0B', 'path': 'F:/Cache/1/dir1/file.txt', 'packtype': '', 'status': '', 'isdir': '0'}
        file_info = i
        # 绝对路径的处理方式
        if switch == 'a':
            upload_path = options['baidu_path'] + '/' + re.sub(':', '', i['path'])
        # 相对路径的处理方式
        elif switch == 'r':
            upload_path = options['baidu_path'] + '/' + re.sub(':', '', re.sub(rf'^{options["local_path"]}[/\\]?', '', i['path']))

        # 注意 upload_dir 和 upload_filename 要用 / 连起来，一般建议直接用 upload_path
        upload_dir = '/'.join(upload_path.split('/')[:-1])
        upload_filename = upload_path.split('/')[-1]

        if upload_dir not in dir_list: dir_list.append(upload_dir)

        file_info['upload_path'] = upload_path
        file_info['upload_dir'] = upload_dir
        file_info['upload_filename'] = upload_filename

        file_list.append(file_info)

    # 对目录列表进行处理：去重、检测是否存在目录并创建不存在的目录
    dir_list.sort()

    for i in dir_list:
        for k in dir_list:
            if re.match(i, k) != None and i != k:
                if i in dir_list: dir_list.remove(i)

    for i in dir_list:
        for k in dir_list:
            if re.search(i, k) != None and i != k:
                if i in dir_list: dir_list.remove(i)

    print('开始创建需要的目录')
    for i in dir_list:
        result = Recursion_Create_Diretcory(i, access_token)
        if result == True: print(f'目录已存在 {i}'); continue

        print(f"已创建目录 {result['path']}")










# 打包相关参数
package = input('是否需要打包后上传（y/确认，回车/直接上传）：')
if package != 'y':
    package = ''
else:
    while True:
        pack_dir = input('输入压缩包存放目录路径，用 - 代表与文件同目录：')
        if pack_dir == '-': pack_dir = options['local_path']; break
        elif os.path.isdir(pack_dir) == False: print('输入的路径不是目录，请重新输入'); continue
        else:
            pack_dir = re.sub(r'[/\\]+$', '/', pack_dir)    # 如果目录最后面没有斜杠则添加一个
            print(f'压缩包存放目录：{pack_dir}')
            break

    print('压缩包密码在配置文件中配置')
    password = Load_Config('Package_Setting', 'password')
    print(f'压缩包密码：{password}')

    crypt = input('对文件名进行加密（y/确认，回车/不加密）：'); crypt_info = False
    if crypt == 'y':
        crypt_info = {'key': Load_Config('Package_Setting', 'key'), 'iv': Load_Config('Package_Setting', 'iv')}
    print(f'文件名加密参数：{crypt_info}')

    volume = input('指定分卷大小，留空使用默认设置，设置为 0 则不分卷：')
    if volume == '':
        volume = Load_Config('Package_Setting', 'volume')
    print(f'分卷大小：{volume}')

print('分块大小在配置文件中指定，默认4，单位：MiB，建议不超过64')
block_size = int(Load_Config('Baidu_Setting', 'block_size'))
if block_size == '' or block_size < 4: block_size = 4
elif block_size > 64: block_size = 64
print(f'分块大小：{block_size}')

# 打包（如果需要）
if package == 'y':
    print(''.rjust(100, '#'), '打包部分'.center(94, ' ').center(96, '#'), ''.ljust(100, '#'), sep='\n'); print()
    for fileinfo in chose_replace:
        print(f" {chose_replace.index(fileinfo)+1} / {len(chose_replace)} ".center(100, '='))

        if fileinfo['packtype'] == 'Source':
            print(f'此文件已使用分卷存储，跳过打包：{fileinfo["path"]}')
            print(''.center(100, '=')); print()
            continue
        elif fileinfo['packtype'] == 'Volume':
            print(f'此文件是分卷文件，跳过打包：{fileinfo["path"]}')
            print(''.center(100, '=')); print()
            continue

        fileinfo['path'] = Package_File(sour_path=fileinfo['path'], sour_name=fileinfo['filename'], dest_dir=pack_dir, password=password, crypt=crypt_info, volume=volume)
        fileinfo['filename'] = os.path.basename(fileinfo['path'])

        # 如果压缩包分卷，则添加分卷的配置
        if volume != '0':
            fileinfo['packtype'] = 'Source'
            for root, dirs, files in os.walk(pack_dir): break
            for sub_file in files:
                if re.search(f"{os.path.basename(fileinfo['path'])}", sub_file) != None: 
                    sub_fileinfo = {'num': f"{fileinfo['num']}-"+re.search(r'(\d{3})$', sub_file)[0], 
                                    'filename': sub_file, 'size_byte': os.path.getsize(pack_dir+sub_file), 
                                    'size_human': calc_size(os.path.getsize(pack_dir+sub_file)), 
                                    'path': pack_dir+sub_file, 'packtype': 'Volume', 'status': '', 'isdir': '1'}
                    chose_replace.append(sub_fileinfo)
        print(''.center(100, '=')); print()

print(''.rjust(100, '#'), '上传部分'.center(94, ' ').center(96, '#'), ''.ljust(100, '#'), sep='\n'); print()
for fileinfo in chose_replace:
    print(f" {chose_replace.index(fileinfo)+1} / {len(chose_replace)} ".center(100, '='))

    if fileinfo['packtype'] == 'Source':
        print(f"文件 {fileinfo['path']} 打包时采用分卷存储，此文件不执行上传")
        print(''.center(100, '=')); print()
        continue

    # 计算文件分片的 MD5
    calc_file_md5(fileinfo['path'], block_size)

    # 开始上传
    Upload_status = Upload(fileinfo, options['baidu_path'], access_token)
    chose_replace[chose_replace.index(fileinfo)]['status'] = Upload_status

    print(''.center(100, '=')); print()

print('完成情况')
table(column=['num', 'filename', 'size_human', 'path', 'packtype', 'status', 'isdir'], row=chose_replace, 
      alias={'num': '序号', 'filename': '文件名', 'size_human': '文件大小', 'path': '文件路径', 'status': '上传状态', 'packtype': '文件类型', 'isdir': '是否为目录'})





