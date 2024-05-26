import sys, logging, re, os
logging.basicConfig(format='[{levelname:^8s}] {asctime} - {message}', level=logging.INFO, style='{')

# 执行命令
def exec(command: str):
    logging.info(f"Exec Command: {command}")
    os.system(command)

# 下载镜像
def DownImages(ImageURLs: list):
    exec('mkdir Images/')
    with open(f"Images/ImagesURLs", 'w', encoding='utf-8') as f:
        for i in ImageURLs: f.write(i+'\n')

    for ImageURL in ImageURLs:
        ImageFullName = ImageURL.split('/')[-1]
        ImageName = ImageFullName.split(':')[0]
        ImageTag = ImageFullName.split(':')[-1]
        FileName = f"{ImageName}.tar"
        File = f"Images/{FileName}"

        # 下载镜像并上传到OBS后删除本地文件
        exec(f"podman pull {ImageURL}")
        exec(f"podman save {ImageURL} > {File}")

    exec(f"tar cvf Images.tar Images/")
    exec(f"mc cp Images.tar local/public-files/")
    logging.info(f"Download Link: https://obs/public-files/Images.tar")

    # 清理
    try:
        input("导入完成后按下 [Enter] 清理环境...")
    except KeyboardInterrupt:
        pass
    for ImageURL in ImageURLs:
        exec(f"podman rmi {ImageURL}")

    exec(f"rm -fr Images/ Images.tar")
    exec(f"mc rm local/public-files/Images.tar")

if __name__ == '__main__':
    if len(sys.argv) == 1:
        logging.error("需要传入容器镜像参数或存有容器镜像的文本文件路径"); exit()

    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            ImageURLs = [re.sub('\n', '', i) for i in f.readlines()]

    except FileNotFoundError:
        ImageURLs = [sys.argv[1]]

    DownImages(ImageURLs)
