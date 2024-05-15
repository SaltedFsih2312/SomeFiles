import sys, os, re
from table import *
from aes_cbc import *
from Public import calc_size, Chose_Local_File, Package_File, Load_Config, Decode_Filename

option = {
    '分卷大小': Load_Config('Package_Setting', 'volume'),
    '密码': Load_Config('Package_Setting', 'password'),
    'key': Load_Config('Package_Setting', 'key'),
    'iv': Load_Config('Package_Setting', 'iv'),
}

# 选择要归档的文件或目录
def chose_dir(row):
    select = input("\n选择要归档的文件或目录（使用 , 隔开多个项目）：").split(',')
    if select == ['']: exit()
    chose = []

    for i in select:
        for dir in row:
            try: chose.index(dir)
            except:
                if dir['序号'] == int(i): chose.append(dir)

    print(); table(column=column, row=chose); print()
    return chose

### 自定义参数 ###
print('打包时使用的部分可自定义参数')
row = [
    {'选项': '分卷大小', '值': option['分卷大小']},
    {'选项': '密码', '值': option['密码']},
]
table(column=['选项', '值'], row=row); print()

分卷大小 = input('指定分卷大小，留空使用默认设置，设置为 0 则不分卷：')
if 分卷大小 != '': option['分卷大小'] = 分卷大小

密码 = input('指定密码，留空使用默认设置：')
if 密码 != '': option['密码'] = 密码


### 前置参数配置 ###
# 指定原文件目录
print('第一个参数指定原文件目录，第二个参数指定输出目录，使用 - 来指定当前目录，不指定输出目录则默认同原文件目录\n')
if len(sys.argv) == 1 or sys.argv[1] == '-': workdir = os.getcwd()
else: workdir = os.path.abspath(sys.argv[1])

# 指定输出目录
if 1 >= len(sys.argv) >= 2: outputdir = workdir
else: outputdir = os.path.abspath(sys.argv[2])

if re.search(r'\/$|\\$', workdir) == None: workdir = workdir + '/'    # 给原文件目录添加斜杠
if os.path.isdir(workdir) == False: print('为原文件目录指定的路径不是目录'); exit()

if re.search(r'\/$|\\$', outputdir) == None: outputdir = outputdir + '/'    # 给输出目录添加斜杠
if os.path.isdir(outputdir) == False: print('为输出目录指定的路径不是目录'); exit()

print(f'原文件目录：{workdir}')
print(f'输出目录：{outputdir}\n')

chose = Chose_Local_File(workdir)

### 对选中的文件或目录进行处理 ###
crypt = input('对文件名进行加密（y/确认，回车/不加密）：')
if crypt == 'y': crypt_info = {'key': option['key'], 'iv': option['iv']}
else: crypt_info = False

### 7-Zip 压缩部分 ###
print('\n开始归档选中的文件或目录\n采用不压缩的方式进行归档，部分选项参照下表')
option_row = [
    {'选项': '分卷大小', '值': option['分卷大小']},
    {'选项': '密码', '值': option['密码']},
]
table(column=['选项', '值'], row=option_row); print()

for i in chose:
    Package_File(sour_path=i["path"], sour_name=i['filename'], dest_dir=outputdir, password=option['密码'], crypt=crypt_info, volume=option['分卷大小'])


### 验证 ###
# 获取目录下的文件列表
for root, dirs, files in os.walk(outputdir): break

column, row, done = ['文件名', '文件大小'], [], 0
if crypt == 'y': column[0] = '解码后文件名'

# 验证成功打包的目录
for i in chose:
    i = re.sub(r'\/$|\\$', '', i['文件名'])
    for o in files:
        if crypt == 'y':
            try: o = decrypt(re.sub(r'(-\d*-\d*.7z.*)', '', o), option['key'], option['iv'])
            except: pass

        if re.sub(r'(-\d*-\d*.7z.*)', '', o) == i:
            try: 
                if re.search(r'(\d{3})$', o)[0] == '001': done += 1
            except: done += 1

print(f'\n需要打包的文件有 {len(chose)} 个，打包完成的文件有 {done} 个')
print('查看输出目录中的文件，用于验证')

for i in files:
    file_size = calc_size(os.path.getsize(outputdir+i))
    if crypt == 'y':
        i = Decode_Filename(i, {'key': option['key'], 'iv': option['iv']})
        row.append({'解码后文件名': i, '文件大小': file_size})
        continue
    row.append({'文件名': i, '文件大小': file_size})

table(column=column, row=row)
