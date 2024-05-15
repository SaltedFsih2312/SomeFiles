> 本篇配置都可以写到全局和虚拟主机里

## 配置正向代理

#### 访问规则

```xml
<Proxy *>
Order allow,deny
Allow from all
</Proxy>
```

#### 启用正向代理

```xml
ProxyRequests On
ProxyVia On
```



## 配置反向代理

```bash
ProxyRequests off
#这下面的 [/example] 是本机 url，[http://www.reverse.com/example] 是后端主机的 url
ProxyPass /example http://www.reverse.com/example
ProxyPassReverse /example http://www.reverse.com/example
```



## 反向代理 - 负载均衡

> 这里是最低程度实现负载均衡，其他配置需要自行配置

>环境：
>系统：CentOS 8.3，使用 `CentOS-8.3.2011-x86_64-dvd1.iso` 内自带的软件包，启用防火墙、SELinux
>主机：www.example.com (172.20.83.1) -- CentOS 8.3
>www1.example.com (172.20.83.2) -- CentOS 8.3
>www2.example.com (172.20.83.3) -- CentOS 8.3
>client.example.com (172.20.100.1) -- Windows 10

```xml
<Proxy balancer://mycluster>
BalancerMember http://172.20.83.2:80
BalancerMember http://172.20.83.3:80
</Proxy>

ProxyPass / balancer://mycluster/
ProxyPassReverse / balancer://mycluster/
```

还需要配置 SELinux 的布尔值才能使前端 httpd 连到后端网站上

```bash
semanage boolean -m -1 httpd_can_network_connect
```



## 参考链接

https://httpd.apache.org/docs/2.4/zh-cn/mod/directives.html

https://www.server-world.info/en/note?os=CentOS_8&p=httpd&f=12

