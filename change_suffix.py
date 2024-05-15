import os, sys, re

text = '''批量修改指定后缀的文件为新后缀文件，后缀格式：.exe、.py等格式
第一个参数指定原后缀，第二个参数指定新后缀'''
print(text)


# 指定原后缀
if len(sys.argv) >= 2: old_suffix = sys.argv[1]
else: old_suffix = input('原后缀名：')

# 指定新后缀
if len(sys.argv) >= 3: new_suffix = sys.argv[2]
else: new_suffix = input('新后缀名：')

print('{} --> {}'.format(old_suffix, new_suffix))

# 获取目录下的文件列表
for root, dirs, files in os.walk(os.getcwd()):
    outputdir_root, outputdir_dirs, outputdir_files = root, dirs, files
    break

for i in outputdir_files:
    if re.search(rf'({old_suffix})$', i):
        print('{} --> {}'.format(i, re.search(rf'.*[^({old_suffix})$]', i).group() + new_suffix))
        os.rename(i, re.search(rf'.*[^({old_suffix})$]', i).group() + new_suffix)

