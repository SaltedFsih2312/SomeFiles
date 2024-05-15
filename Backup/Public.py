# 参数格式
# 文件参数：{'num': '', 'filename': '', 'size_byte': '', 'size_human': '', 'path': '', 'packtype': 'Source|Volume', 'status': 'Success|Failed', 'isdir': '0|1'}
# 文件参数字段：['num', 'filename', 'size_byte', 'size_human', 'path', 'packtype', 'status', 'isdir']

# 用于存放一些公共函数
import os, time, re, configparser, hashlib
from table import *
from aes_cbc import *

config_file = rf'{os.path.dirname(os.path.abspath(__file__))}/config.ini'

# 计算文件大小以设置单位
def calc_size(result):
    count = 0
    while result > 1024:
        result = result / 1024
        count += 1
    
    if count == 0: result = '{}B'.format(round(result, 2))
    elif count == 1: result = '{}KB'.format(round(result, 2))
    elif count == 2: result = '{}MB'.format(round(result, 2))
    elif count == 3: result = '{}GB'.format(round(result, 2))
    elif count == 4: result = '{}TB'.format(round(result, 2))

    return result

# 选择本地文件
def Chose_Local_File(path, only_dir=False):
    '''传入目录路径，通过交互式菜单返回多个文件参数组成的列表'''
    if os.path.isdir(path) == False: print(f"该路径不是目录，检查输入的路径：{path}"); exit()

    # 规范路径，将目录路径的反斜杠转换成斜杠，不管目录最后面有没有斜杠都添加一个，有多个就替换成只有一个
    path = re.sub(r'/$', '', re.sub(r'[\\/]+', '/', path)) + '/'

    column = ['num', 'filename', 'size_human', 'isdir']
    alias = {'num': '序号', 'filename': '文件名', 'size_human': '文件大小', 'isdir': '是否为目录'}

    while True:
        row = Get_File_List(path, only_dir)

        print(f'目录：{path}')
        table(column=column, row=row, alias=alias)

        select = input("\n填写序号选择文件或目录（使用 , 隔开多个项目，不选择则退出）：").split(',')
        if select == ['']: exit()

        chose = []
        for i in select:
            try: chose.append(row[int(i)])
            except: pass

        print(); table(column=column, row=chose, alias=alias); print()
        while True:
            confirm = input('以上是选中的文件或目录（y/确认，n/重选）：')
            if confirm != '': break
        if confirm == 'y': break
    return chose

# 打包文件或目录
def Package_File(sour_path, sour_name, dest_dir, password, crypt=False, volume=0):
    '''返回成功打包后的文件名 \n
sour_path：待打包文件的完全路径 \n
sour_name：待打包文件的文件名 \n
dest_dir：输出目录 \n
password：压缩包密码 \n
crypt=False：默认False，需要传入格式为：{'key': 'key', 'iv': 'iv'} 才能生效 \n
volume=0：分卷大小，0为不开。例子：1G \n
'''
    sour_name = re.sub(r'\/$|\\$', '', sour_name)    # 把目录最后面的斜杠去掉
    if re.search(r'\/$|\\$', dest_dir) == None: dest_dir = dest_dir + '/'    # 如果目标目录最后面没有斜杠则添加一个

    # 如果传入的是字典类型，则根据字典内容对文件名进行加密
    if type(crypt) == dict:
        sour_name = encrypt(sour_name, crypt['key'], crypt['iv']).decode('utf-8')

    dest = f'{dest_dir}{sour_name}-{time.strftime("%Y%m%d-%H%M%S")}.7z'

    if volume == '0':
        option = f'-mx=0 -mhe=on -scsUTF-8 -y -r -p{password} "{dest}" "{sour_path}"'
    else:
        option = f'-v{volume} -mx=0 -mhe=on -scsUTF-8 -y -r -p{password} "{dest}" "{sour_path}"'

    os.system(f"{os.path.dirname(os.path.abspath(__file__))}/7z a -t7z {option}")
    return dest

# 从配置文件中加载指定的值
def Load_Config(part: str, key: str, config_file=config_file):
    '''
    config_file：配置文件路径，采用 INI 格式 \n
    part：在配置文件中的哪一段 \n
    key：在配置文件中的哪一段的哪个键 \n
    '''
    config = configparser.ConfigParser()
    try:
        config.read(filenames=config_file, encoding='utf-8')
        result = config.get(part, key)
    except: print(f'无法加载配置文件中 {part} 部分的 {key} 的值'); return ''
    else: return result

# 为文件名解密
def Decode_Filename(string, crypt):
    '''
    crypt：需要传入格式为：{'key': 'key', 'iv': 'iv'} 才能生效 \n
    如果解密失败会返回原文件名
    '''
    try:
        if type(crypt) == dict:
            string = decrypt(re.sub(r'(-\d*-\d*.7z.*)', '', string), crypt['key'], crypt['iv'])
    except: pass
    return string

# 递归列出指定目录的文件
def list_files(path):
    '''传入一个目录路径，返回该目录下的文件路径列表'''
    if os.path.isdir(path) == False: print(f"该路径不是目录，检查输入的路径：{path}"); exit()
    file_list = []
    for item in os.listdir(path):
        sub_path = re.sub('\\\\', '/', os.path.join(path, item))
        if os.path.isfile(sub_path): file_list.append(sub_path)
        else: file_list += list_files(sub_path)
    return file_list

# 获取指定目录路径的文件列表，并生成符合文件参数的列表
def Get_File_List(path, only_dir=False):
    '''传入目录路径，返回多个文件参数组成的列表'''
    # 规范路径，将目录路径的反斜杠转换成斜杠，不管目录最后面有没有斜杠都添加一个，有多个就替换成只有一个
    path = re.sub(r'/$', '', re.sub(r'[\\/]+', '/', path)) + '/'

    for root, dirs, files in os.walk(path): break

    file_list, count = [], 0

    for i in dirs:
        file_parameters = {'num': str(count), 'filename': i, 
                           'size_byte': os.path.getsize(path+i), 
                           'size_human': calc_size(os.path.getsize(path+i)), 
                           'path': path+i, 'packtype': '', 'status': '', 'isdir': '1'}
        file_list.append(file_parameters); count += 1
    if only_dir == False:
        for i in files: 
            file_parameters = {'num': str(count), 'filename': i, 
                            'size_byte': os.path.getsize(path+i), 
                            'size_human': calc_size(os.path.getsize(path+i)), 
                            'path': path+i, 'packtype': '', 'status': '', 'isdir': '0'}
            file_list.append(file_parameters); count += 1

    return file_list

# 计算输入二进制数据的 MD5 值
def md5_hash(binary):
    md5 = hashlib.md5()
    md5.update(binary)
    return md5.hexdigest()
