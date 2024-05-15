'''
找出未备份文件（本地文件名、创建时间）
查看已上传文件信息（文件名——对应本地文件名、文件大小、上传时间——创建时间、修改时间）
'''

import requests, json, re, os, sys, time, pyinputplus
from table import *
from Baidu_Modules import *

cookie = ''
# cookie = ''
option = {
    '密码': '密码',
    'key': 'key',
    'iv': 'iv',
}

# 指定本地目录
print('第一个参数指定本地目录，第二个参数指定百度网盘上的文件目录，使用 - 来代表当前目录，不指定输出目录则默认同本地目录')
if len(sys.argv) == 1 or sys.argv[1] == '-': local_path = os.getcwd()
else: local_path = os.path.abspath(sys.argv[1])

# 百度网盘上的文件目录
if len(sys.argv) > 2: baidu_path = sys.argv[2]
else: baidu_path = Choice_Dir(path='/', cookie=cookie)

# 获取本地目录文件列表
local_list = []
if os.path.isdir(local_path) == True:
    for root, dirs, files in os.walk(local_path, ):
        for i in dirs: 
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(root+'/'+i)))
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(root+'/'+i)))
            size = os.path.getsize(root+'/'+i)
            local_list.append({'filename': i, 'isdir': '1', 'ctime': ctime, 'mtime': mtime, 'size': size})
        for i in files:
            ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getctime(root+'/'+i)))
            mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(root+'/'+i)))
            size = os.path.getsize(root+'/'+i)
            local_list.append({'filename': i, 'isdir': '0', 'ctime': ctime, 'mtime': mtime, 'size': size})
        break

# 获取百度网盘文件列表
result = Get_File_list(baidu_path, cookie)
baidu_list = []
for i in result:
    ctime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['server_ctime']))
    mtime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i['server_mtime']))
    size = i['size']
    isdir = i['isdir']
    baidu_list.append({'filename': i['server_filename'], 'isdir': isdir, 'ctime': ctime, 'mtime': mtime, 'size': size})


# 预处理，将百度网盘文件列表里的文件名解密
use_volumes = {}
for i in baidu_list:
    if re.search('(\d{3})$', i['filename']) == None:
        # print(decrypt_filename(i['filename']))
        baidu_list[baidu_list.index(i)]['filename'] = decrypt_filename(i['filename'], option)
    else:
        # 将分卷了的压缩包单独列出来
        volume_name = re.search('.*[^(.\d{3})$]', i['filename']).group()
        use_volumes.setdefault(volume_name, [])
        use_volumes[volume_name].append(i)

# 预处理，将列出来的分卷压缩包进行处理，合并文件大小
for i in use_volumes.keys():
    size = 0
    filename = decrypt_filename(use_volumes[i][0]['filename'], option)
    ctime = use_volumes[i][0]['ctime']
    mtime = use_volumes[i][0]['mtime']
    for v in use_volumes[i]:
        baidu_list.remove(v)
        size += v['size']
    baidu_list.append({'filename': filename, 'isdir': '0', 'ctime': ctime, 'mtime': mtime, 'size': size})

# 预处理，将两个列表根据修改时间进行升序排序
local_list = sort_by_mtime(local_list, reverse=True)
baidu_list = sort_by_mtime(baidu_list, reverse=True)

# 找出未备份的文件
baidu_filename = []
for i in baidu_list: baidu_filename.append(i['filename'])
local_filename = []
for i in local_list: local_filename.append(i['filename'])
not_backup_filename = [y for y in local_filename if y not in baidu_filename]

未备份 = []
已备份 = []

# 未备份文件
for l in local_list:
    if l['filename'] in not_backup_filename:
        filename = l['filename']
        ctime = l['ctime']
        mtime = l['mtime']
        size = calc_size(l['size'])
        未备份.append({'本地文件': filename, '文件大小': size, '创建时间': ctime, '修改时间': mtime})

# 已备份文件
for l in local_list:
    if l['filename'] not in not_backup_filename:
        filename = l['filename']
        local_ctime = l['ctime']
        local_mtime = l['mtime']
        for b in baidu_list:
            if b['filename'] == l['filename']:
                baidu_ctime = b['ctime']
                baidu_mtime = b['mtime']
                baidu_size = calc_size(b['size'])
        已备份.append({'本地文件': filename, '备份文件大小': baidu_size, '本地创建时间': local_ctime, '本地修改时间': local_mtime, '备份创建时间': baidu_ctime, '备份修改时间': baidu_mtime})


# 结果输出
output_type = pyinputplus.inputMenu(prompt="选择导出模式，默认直接输出表格\n", choices=['表格', 'csv'], numbered=True, default='表格', limit=1)

if output_type == '表格': interval=' '
elif output_type == 'csv': interval=','

if len(已备份) != 0:
    print('以下文件或目录已备份至百度网盘')
    table(column=['本地文件', '备份文件大小', '本地创建时间', '本地修改时间', '备份创建时间', '备份修改时间'], row=已备份, interval=interval)
    print()

if len(未备份) != 0:
    print('以下文件或目录未备份至百度网盘')
    table(column=['本地文件', '文件大小', '创建时间', '修改时间'], row=未备份, interval=interval)
