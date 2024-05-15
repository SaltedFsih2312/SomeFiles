## Apache HTTPD 基本配置

> 本篇文档仅演示基本功能或格式，更多详细参数需要查阅 Apache HTTPD 的[官方文档][1]。

### 配置虚拟主机

```bash
#案例
<VirtualHost *:80>
	ServerName www.example.com
	DocumentRoot /usr/www/
	DirectoryIndex index.php
</VirtualHost>
<Directory "/usr/www/">
	Require all granted #全部允许访问，二选一
	Require all denied #全部拒绝访问，二选一
</Directory>

#修改指定的虚拟主机配置
#可以指定虚拟主机监听的域名
ServerName www.example.com
#也可以自定义虚拟主机监听的 IP 地址和端口
<VirtualHost [IP]:[Port]>...</VirtualHost>
#要在全局配置里添加虚拟主机监听的端口或 IP 地址
Listen [IP]:[Port]
```



### SSL

```bash
#需要安装 mod_ssl 模块
dnf install -y mod_ssl

#在需要的配置中添加
SSLEngine on
SSLCertificateFile /etc/pki/tls/certs/server.crt
SSLCertificateKeyFile /etc/pki/tls/certs/server.key

#把 /etc/httpd/conf.d/ssl.conf 禁用
ssl.conf --> ssl.conf.bak
```

#### 只允许使用域名通过 SSL 访问

```bash
<VirtualHost *:443>
	ServerName 172.20.83.1
	SSLEngine on
	SSLCertificateFile /etc/pki/tls/certs/server.crt
	SSLCertificateKeyFile /etc/pki/tls/certs/server.key
	<Location />
		Order allow,deny
		Deny from all
	</Location>
</VirtualHost>
```



### 使用401认证

```bash
#创建 .htpasswd 文件
#配置第一个用户的时候需要加上-c参数创建文件
htpasswd -c /路径/文件名 用户名

#在需要401认证的虚拟主机或者全局里添加
<LocationMatch "^/+$">
	AuthName "login"		#验证框提示的文本
	AuthType basic			#验证的模式
	AuthUserFile "/www/.htpasswd"	#htpasswd的文件位置，绝对路径
	Require valid-user		#允许通过验证的用户访问
</LocationMatch>
```



### 目录浏览

在主配置文件 `/etc/httpd/conf/httpd.conf` 中添加，一般默认加载，可以不用添加

```bash
LoadModule autoindex_module modules/mod_autoindex.so
LoadModule dir_module modules/mod_dir.so
```


在要设置目录浏览的配置里的 `<Directory></Directory>` 中添加

```bash
Options +Indexes +FollowSymLinks
```

> 这里使用 +\- 号来控制功能开关
> FollowSymLinks 控制符号链接开关
> Indexes 控制是否打开目录浏览，如果要关闭目录浏览，请使用 `Options -Indexes`

要把 `/etc/httpd/conf.d/welcome.conf` 里的 `Options -Indexes` 删去减号，不然会没有效果

在 IndexOptions 后加的一些参数

```bash
Charset=utf8		#设置字符集，以消除中文乱码
NameWidth=50		#指定目录列表可以显示最长为25字节的文件/目录名
```



### Apache 的监控页面

> 在全局或虚拟主机里添加

```bash
<Location /[虚拟目录名]>
	SetHandler server-status
</Location>
```



### 虚拟目录

> 在全局或虚拟主机里添加

```bash
Alias /[虚拟目录] "[真实目录]"
<Directory "[真实目录]">
	Require all granted
</Directory>
```



### IPv6

设置基于地址的虚拟主机，配置文件里也用类似格式使用 IPv6 地址

```xml
<VirtualHost [2020::1]:80></VirtualHost>
```

访问使用 IPv6 的网站

```bash
curl http://[2020::1]/
```



### 重定向

#### 使用 mod_rewrite 模块进行 HTTP --> HTTPS 重定向

> 可以在全局或虚拟主机里添加

```xml
<IfModule mod_rewrite.c>
	RewriteEngine on
	RewriteCond %{SERVER_PORT} !^443$
	RewriteRule ^/(.*)$ https://www.example.com/$1 [R=301,L]
</IfModule>
```

#### 使用指令重定向

> 可以在全局或虚拟主机里添加，不怎么建议使用

```bash
#此重定向告诉客户端资源已永久移动，这与 HTTP 状态 301 相对应
Redirect permanent /username http://example.com/~username/

#temp 状态是默认行为，表示仅是临时的，默认状态是重定向
Redirect temp /username http://example.com/~username/

#对应 HTTP 状态 302。发送 another 状态以指示所请求的信号：该资源已被另一个资源替换（HTTP 状态 303） 
Redirect seeother /username http://example.com/~username/

#gone 状态告诉客户端资源已被（永久）删除； 这发送 HTTP 状态 410 作为不可用 404 状态的替代。 如果是 leaved 重定向，请忽略最终网址
Redirect gone /username


#Apache 还提供了另外两个永久性和临时性重定向指令，它们更加清晰。 它们如下
RedirectPermanent /username/bio.html http://example.com/~username/bio/
RedirectTemp /username/bio.html http://example.com/~username/bio/

#Apache 还可以使用 RedirectMatch 指令来使用正则表达式将请求类型重定向到新地址
#该指令匹配对扩展名为 .jpg 的文件的任何请求，并将其替换为第二个域上的位置
RedirectMatch (.*)\.jpg$ http://static.example.com$1.jpg
```



## 参考链接

[1]:https://httpd.apache.org/docs/2.4/zh-cn/

https://httpd.apache.org/docs/2.4/zh-cn/mod/directives.html

