## 使用squid反向代理httpd

安装了squid的服务器可以不用安装httpd服务，但是要能访问到要代理网页
使用反向代理可以把httpd等服务放到内网，squid放在外网和内网之间，可以提高一定的安全性和性能
环境：
httpd: web1.example.com(192.168.1.2/24) web2.example.com(192.168.1.3/24)
squid: www.example.com(192.168.1.1/24) 

## httpd

> 这里的httpd服务提供网页文件，可以使用ssl的连接
> 这里的配置只是一个例子，根据实际需要进行配置

/etc/httpd/conf/httpd.conf
在最后新增
```bash
alias /phpinfo "/var/www/html/info.php"
<directory "/var/www/html/info.php">
require all granted
</directory>
<location /status>
sethandler server-status
</location>
```

后续

```bash
echo "web1" >> /var/www/html/index.html
echo "<?php phpinfo()?>" >> /var/www/html/info.php
openssl req -new -x509 -keyout /var/www/web.key -out /var/www/web.crt -nodes
sed -i 's=SSLCertificateFile .*=SSLCertificateFile /var/www/web.crt=' /etc/httpd/conf.d/ssl.conf
sed -i 's=SSLCertificateKeyFile .*=SSLCertificateKeyFile /var/www/web.key=' /etc/httpd/conf.d/ssl.conf
#也可以直接去'/etc/httpd/conf.d/ssl.conf'里面找到上面这两个修改
systemctl restart httpd
```

## squid

> 这里的配置只是一个例子，根据实际需要进行配置
> 如果squid配置了缓存，那么如果后端网页更新了就要等一段时间或者重启squid服务才能刷新

/etc/squid/squid.conf

```bash
http_port 80 vhost
https_port 443 accel cert=/etc/squid/squ.crt key=/etc/squid/squ.key
cache_men 512 MB
cache_dir ufs /cache 5120 16 256
cache_peer web1.example.com parent 80 0 proxy-only		#proxy-only 是仅代理模式，不进行缓存
cache_peer web2.example.com parent 80 0 proxy-only
sslproxy_cert_error allow all
http_access allow all
```
如果后端httpd服务支持ssl也可以这样配置
```bash
...
cache_peer web1.example.com parent 443 0 proxy-only ssl
cache_peer web2.example.com parent 443 0 proxy-only ssl
...
```


后续

```bash
mkdir /cache
chown squid:squid /cache
openssl req -new -x509 -keyout /etc/squid/squ.key -out /etc/squid/squ.crt -nodes
squid -z
systemctl restart squid
```

## 测试

```bash
curl -k https://www.example.com
curl http://www.example.com
curl http://www.example.com/phpinfo
curl http://www.example.com/status
```

一些问题
处理php等文件时会在squid里处理 而不是在httpd端处理完后发送给squid 即使仅代理模式也一样