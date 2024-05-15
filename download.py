# 多进程下载（只需导入这个函数）
# url_list：由多个文件URL组成的列表
# output_dir：输出目录
# thread：同时下载数

# 主进程
def download(url_list: list, headers: dict, output_dir: str, thread: int=8, proxies: dict={'all': 'socks5://127.0.0.1:10808'}, max_retry: int=3, retry: bool=False) -> dict:
    from multiprocessing import Manager, Process, Queue
    from re import search
    from time import sleep
    from pyinputplus import inputChoice
    man = Manager()
    q_task = Queue(thread)
    q_reporter = Queue(thread)
    status = man.dict({'Success': 0, 'Failure': 0, 'Total': len(url_list), 'reTry': 0})
    fails = man.list()
    share_data = {'headers': headers, 'proxies': proxies, 'output_dir': output_dir, 'retry': max_retry}

    if search(r'[/\\]$', output_dir) == None: output_dir += '/'

    working = [{'url': url, 'retry': 0} for url in url_list]

    while True:
        pool = [Process(target=worker, args=(share_data, q_task, status, fails, q_reporter), name=f'worker{i}') for i in range(thread)]
        for p in pool: p.start()
        while True:
            status['Failure'] = len(fails)
            if q_reporter.empty() == False:
                q_reporter.get()
                status['reTry'] += 1

            # 显示当前状态
            print(f"\r下载中... 成功：{status['Success']}/{status['Total']}", end='')
            if status['Failure'] != 0:
                print(f"，失败：{status['Failure']}", end='')
            if status['reTry'] != 0:
                print(f"，重试次数：{status['reTry']}", end='')

            # 工作队列
            if q_task.full() == False:
                if len(working) != 0:
                    q_task.put(working[0])
                    working.pop(0)
                else:
                    q_task.put('Done')

            finish = 0
            # 维护线程池，保证在任务完成前有足够数量的进程
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
                        new = Process(target=worker, args=(share_data, q_task, status, fails, q_reporter), name=f'{name}')
                        pool.append(new)
                        new.start()

            # 结束条件
            if finish == thread: print(); break
            sleep(0.001)

        if status['Failure'] != 0:
            if retry == True:
                select = inputChoice(['y', 'n'], prompt='有部分链接无法下载，是否重试（y/n）：', default='n', limit=3)
            else:
                select = 'n'
            if select == 'y':
                # 重设环境
                status['Failure'] = 0
                status['reTry'] = 0

                for i in range(len(fails)):
                    fails[0]['retry'] = 0
                    working.append(fails[0])
                    fails.pop(0)

                for i in range(len(pool)): pool.pop(0)

                while q_task.empty() != True: q_task.get()

                continue
            else:
                print(f'有部分链接无法下载，请手动下载：{output_dir}failure.txt')
                status['Status'] = 'Failure'
                with open(output_dir+'failure.txt', 'w', encoding='utf-8') as f:
                    for i in fails: f.write(i['url']+'\n')
                break
        else:
            status['Status'] = 'Success'
            break

    result = dict(status)
    man.shutdown()
    q_task.close()
    return result

# 下载（子进程）
def worker(share_data, q_task, status, fails, q_reporter):
    from requests import get
    from time import sleep
    while True:
        task = q_task.get()
        if task == 'Done': exit(0)
        try:
            url = task['url']
        except: print(task, 'url')
        retry_count = 0

        while retry_count < share_data['retry']:
            try:
                response = get(url, headers=share_data['headers'], proxies=share_data['proxies'])
            except:
                retry_count += 1
                q_reporter.put('reTry')
                continue
            else:
                if response.status_code == 200:
                    open(share_data['output_dir'] + url.split('/')[-1], 'wb').write(response.content)
                    status['Success'] += 1
                    break
                else:
                    retry_count += 1
                    q_reporter.put('reTry')
                    continue
        else:
            fails.append(task)


