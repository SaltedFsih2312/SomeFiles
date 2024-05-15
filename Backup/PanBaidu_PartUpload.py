# 多进程执行样例文件
'''
def rename_me（需改名）
参数：items: list, headers: dict, proxies: dict={'all': 'socks5://127.0.0.1:10808'}, output_dir: str=None, thread: int=8, max_retry: int=3, retry: bool=False

输入：任务列表（items），应该是一个包含了具有相同处理方法的数据的列表
输出：{'Success': 0, 'Failure': 0, 'Total': len(url_list), 'reTry': 0, 'Result': {}}
Result：以item为key，获取结果为value（{'abc': 'data_abc', 'abcd': 'abcd_data'}）
'''

from multiprocessing import Manager, Process, Queue
from time import sleep
from pyinputplus import inputChoice
import logging, os, json, urllib.parse, requests

# 工作子进程样例结构
'''
要实现的基本功能
1、static_data包含了完成任务所需要的所有静态数据
2、成功后如果需要返回获取的数据，需要使用：status['Result'][task] = Result，这种方法返回
'''
def worker(static_data, q_task, status, fails, q_reporter, worker_name):
    while True:
        # 获取任务
        task = q_task.get()
        if task == 'Done': exit(0)
        retry_count = 0

        # 实现功能部分
        while retry_count < static_data['retry']:
            data = {
                "method": "upload", "type": "tmpfile",
                "access_token": static_data['access_token'],
                "path": static_data['path'],
                "uploadid": static_data['uploadid'],
                "partseq": task,
            }
            url = f"https://d.pcs.baidu.com/rest/2.0/pcs/superfile2?{urllib.parse.urlencode(data)}"
            with open(static_data['local_path'], 'rb') as f:
                f.seek(static_data['block_size']*task)
                result = requests.post(url, files=[('file', f.read(static_data['block_size']))])
                response = json.loads(result.text)
            if result.status_code == 200:
                q_reporter.put(task)
                status['Success'] += 1
                break
            else:
                print(f'\n{response}')
                retry_count += 1
                status['reTry'] += 1
                continue
        # 超过最大重试次数
        else:
            fails.append(task)
            status['Failure'] += 1

# 主进程
def PartUpload(items: list, task_file: str, access_token: str, thread: int=None, max_retry: int=3, retry: bool=False) -> dict:
    # 检查运行环境
    if thread == None:
        thread = os.cpu_count()
    if type(items) == list:
        working = items.copy()

    # 准备运行环境
    man = Manager()
    q_task = Queue(thread)
    q_reporter = Queue(thread)
    status = man.dict({'Success': 0, 'Failure': 0, 'Total': len(items), 'reTry': 0})
    fails = man.list()
    task = json.load(open(task_file, 'r', encoding='utf-8'))
    block_list = task['block_list']
    static_data = {
        'retry': max_retry, 
        'access_token': access_token, 
        'path': task['remote_path'], 
        'uploadid': task['uploadid'], 
        'local_path': task['local_path'],
        'block_size': task['block_size']
    }

    # 开始运行
    while True:
        pool = [Process(target=worker, args=(static_data, q_task, status, fails, q_reporter, f'worker{i}'), name=f'worker{i}') for i in range(thread)]
        for p in pool: p.start()
        while True:
            # 处理成功的结果
            while q_reporter.empty() == False:
                result = q_reporter.get()
                task['finish_block'].append(block_list[result])
                json.dump(task, open(task_file, 'w', encoding='utf-8'), indent=4)

            # 显示当前状态
            print(f"\r上传分片中... 成功：{status['Success']} / {status['Total']}", end='')
            if status['Failure'] != 0:
                print(f"，失败：{status['Failure']}", end='')
            if status['reTry'] != 0:
                print(f"，重试次数：{status['reTry']}", end='')

            # 添加任务到工作队列
            if q_task.full() == False:
                if len(working) != 0:
                    md5 = block_list[working[0]]
                    if md5 not in task['finish_block']:
                        q_task.put(working[0])
                    working.pop(0)
                else:
                    q_task.put('Done')

            finish = 0
            # 维护进程池，保证在任务完成前有足够数量的进程
            for p in pool:
                match p.exitcode:
                    case None : pass
                    # 正常退出的进程
                    case 0: finish += 1
                    # 遇到异常退出或其他exitcode的情况
                    case _:
                        name = p.name
                        p.close()
                        pool.pop(pool.index(p))
                        new = Process(target=worker, args=(static_data, q_task, status, fails, q_reporter, name), name=f'{name}')
                        pool.append(new)
                        new.start()

            # 结束
            if finish == thread:
                print()
                logging.info(f"分片上传结束，共 {status['Total']} 个分片，成功：{status['Success']}，失败：{status['Failure']}，重试次数：{status['reTry']}")
                break
            sleep(0.001)

        if status['Failure'] != 0:
            if retry == True:
                select = inputChoice(['y', 'n'], prompt='有部分分片上传失败，是否重试（y/n）：', default='n', limit=3)
            else:
                select = 'n'
            if select == 'y':
                # 重设环境
                status['Failure'] = 0
                status['reTry'] = 0
                working = list(fails).copy()
                pool.clear()
                while q_task.empty() != True: q_task.get()
                continue
            else:
                status['Status'] = 'Failure'
                break
        # 全部成功则处理结果并退出
        else:
            status['Status'] = 'Success'
            break

    # 清理环境并返回结果
    result = dict(status)
    man.shutdown()
    q_task.close()
    return result
