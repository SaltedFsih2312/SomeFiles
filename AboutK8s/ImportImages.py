import logging, re, os
logging.basicConfig(format='[{levelname:^8s}] {asctime} - {message}', level=logging.INFO, style='{')

# 执行命令
def exec(command: str):
    logging.info(f"Exec Command: {command}")
    os.system(command)

# 导入镜像
def ImportImages(ImageURLs: list):
    for ImageURL in ImageURLs:
        ImagePath = '/'.join(ImageURL.split('/')[1:])
        ImageFullName = ImageURL.split('/')[-1]
        ImageName = ImageFullName.split(':')[0]
        ImageTag = ImageFullName.split(':')[-1]
        FileName = f"{ImageName}.tar"
        File = f"Images/{FileName}"

        exec(f"docker load < {File}")
        exec(f"rm -f {File}")
        exec(f"docker tag {ImageURL} ResNode.k8s.exam/{ImagePath}")
        exec(f"docker push ResNode.k8s.exam/{ImagePath}")
        exec(f"docker rmi {ImageURL}")

    exec(f"rm -fr Images/")
    exec(f"rm -f Images.tar")

if __name__ == '__main__':
    exec(f"curl -o Images.tar https://obs/public-files/Images.tar")
    exec(f"tar xvf Images.tar")

    with open('./Images/ImagesURLs') as f:
    # with open('./ImagesURLs.txt') as f:
        ImageURLs = [re.sub('\n', '', i) for i in f.readlines()]

    ImportImages(ImageURLs)
