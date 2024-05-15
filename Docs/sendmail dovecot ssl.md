## sendmail和dovecot配置ssl加密连接

## sendmail

/etc/mail/sendmail.mc
找到下面几行修改并解除注释

```bash
60 dnl define(`confCACERT_PATH', `/etc/pki/tls/certs')dnl		#设置CA的证书路径，没有也可以不用注释
61 dnl define(`confCACERT', `/etc/pki/tls/certs/ca-bundle.crt')dnl		#设置CA证书，没有也可以不用注释
62 dnl define(`confSERVER_CERT', `/etc/pki/tls/certs/mail.crt')dnl		#服务器的证书
63 dnl define(`confSERVER_KEY', `/etc/pki/tls/certs/mail.key')dnl		#服务器的密钥
136 dnl DAEMON_OPTIONS(`Port=smtps, Name=TLSMTA, M=s')dnl		#开启smtps端口
```

### 使用 sasl 给 sendmail 进行账号认证

/etc/mail/sendmail.mc

```bash
52  dnl TRUST_AUTH_MECH(`EXTERNAL DIGEST-MD5 CRAM-MD5 LOGIN PLAIN')dnl
53  dnl define(`confAUTH_MECHANISMS', `EXTERNAL GSSAPI DIGEST-MD5 CRAM-MD5 LOGIN PLAIN')dnl
118 DAEMON_OPTIONS(`Port=smtp,Addr=0.0.0.0, Name=MTA, M=Ea')dnl		#在'Name=MTA'后加'M=Ea'用来强制验证，可选
```

如果出现无法收发邮件可以尝试把 `/etc/mail/sendmail.cf` 中的 `Cwlocalhost` 改成 `Cwexample.com` example.com是你的域名

## dovecot

/etc/dovecot/dovecot.conf 修改

```bash
24 protocols = imaps pop3s		#只保留这两个协议就行
```

/etc/dovecot/conf.d/10-auth.conf

```bash
10 disable_plaintext_auth = yes		#解除注释
```

/etc/dovecot/conf.d/10-ssl.conf

```bash
ssl = required		#改为yes
ssl_cert = </etc/pki/tls/certs/mail.crt		#ssl证书路径
ssl_key = </etc/pki/tls/certs/mail.key		#ssl私钥路径
```

配置完了就重启服务

```bash
systemctl restart sendmail dovecot.service saslauthd
```

## 测试

用邮件程序测试需要勾上ssl认证

## 存在的问题
smtp使用ssl连接会出现无法发邮件

