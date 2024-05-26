import requests, sys, re, os, logging
from bs4 import BeautifulSoup
# apt install -y python3-bs4

logging.basicConfig(format='[{levelname:^8s}] {asctime} - {message}', level=logging.INFO, style='{')

url = sys.argv[1]
action = sys.argv[2]
try: prefix = sys.argv[3]
except IndexError: prefix = ''

# 执行命令
def exec(command: str):
    logging.info(f"Exec Command: {command}")
    os.system(command)

response = requests.get(url)

bs = BeautifulSoup(response.text, 'lxml')
yaml_list = []

for i in bs.select('a'):
    href = i.attrs.get('href')
    if re.search(f'(^{prefix}).*((\.yaml)$|(\.yml)$)', href) != None: yaml_list.append(href)

if len(yaml_list) == 0: logging.info(f"没有找到 {prefix} 作为开头的文件"); exit()

print(f"在 {url} 目录下找到以下 .yaml / .yml 文件")
for i in yaml_list: print(i)
try: input("\n按下 <Enter> 继续...")
except KeyboardInterrupt: exit()

for f in yaml_list: exec(f"kubectl {action} -f {url}{f}")
