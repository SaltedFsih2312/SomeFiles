## 使用 Keepalive+HAProxy 提供高可用网页

Keepalive 提供高可用，HAProxy提供负载均衡
环境：
keepalive+haproxy: www1.example.com(192.168.1.1/24) www2.example.com(192.168.1.2/24)
httpd: web1.example.com(192.168.1.3/24) web2.example.com(192.168.1.4/24)
keepalive浮动ip: www.example.com(192.168.1.10/24)

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

## haproxy
> 这里的配置只是一个例子，根据实际需要进行配置

/etc/haproxy/haproxy.cfg

```bash
...
frontend web
	bind *:80
	bind *:443 ssl crt /etc/haproxy/web.pem
	mode http
	option forwardfor
	redirect scheme https code 301 if !{ ssl_fc }		#设置http重定向到https
	default_backend httpd

backend httpd
	mode http
	balance roundrobin
	server web1 web1.example.com:80 check inter 2000 rise 3 fall 3 weight 1
	server web2 web2.example.com:80 check inter 2000 rise 3 fall 3 weight 1
...
```

如果后端httpd服务支持ssl也可以这样配置

```bash
...
	server web1 web1.example.com:443 ssl verify none check inter 2000 rise 3 fall 3 weight 1
	server web2 web2.example.com:443 ssl verify none check inter 2000 rise 3 fall 3 weight 1
#加了'verify none'代表haproxy不验证ssl证书是否有效
...
```

后续

```bash
openssl req -new -x509 -keyout /etc/haproxy/web.pem -out /etc/haproxy/web.pem -nodes
systemctl restart haproxy
```

## keepalive

> 这里的配置只是一个例子，根据实际需要进行配置
> 这个配置是支持ssl连接
> 备份服务器只需改几个参数即可

/etc/keepalived/keepalived.conf

```bash
global_defs {
   router_id LVS_DEVEL
}
vrrp_instance VI_1 {
    state MASTER
    interface ens33
    virtual_router_id 50
    priority 200
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 2020
    }
    virtual_ipaddress {
        172.20.1.10
    }
}
virtual_server 172.20.1.10 443 {
    delay_loop 6
    lb_algo rr
    lb_kind NAT
    persistence_timeout 50
    protocol TCP
    real_server 172.20.1.1 443 {
        weight 1
            connect_timeout 3
    }
}
```

后续

```bash
systemctl restart keepalived
```

## 测试

> 这里建议用有图形化界面的浏览器测试，可以看到 haproxy 重定向的效果
> 多访问几次同一个网页，可以看到负载均衡的效果，因为在 haproxy 里设置的服务器权重值都为1

```bash
curl -k https://www.example.com
curl -k https://www.example.com/phpinfo
curl -k https://www.example.com/status
curl -k https://www1.example.com
curl -k https://www2.example.com
```

## 注意

php模块只需要在装了httpd服务的服务器上装即可

