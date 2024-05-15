## postfix和dovecot配置ssl加密连接

## postfix

/etc/postfix/main.cf
在文件末尾新增
```bash
smtpd_use_tls = yes
smtpd_tls_cert_file = /etc/pki/tls/certs/mail.crt		#ssl证书路径
smtpd_tls_key_file = /etc/pki/tls/certs/mail.key		#ssl私钥路径
smtpd_tls_session_cache_database = btree:/etc/postfix/smtpd_scache
```

/etc/postfix/master.cf
在文件中找到这两行

```bash
26 smtps     inet  n       -       n       -       -       smtpd
28   -o smtpd_tls_wrappermode=yes
```

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
systemctl restart postfix dovecot.service
```

## 测试

用邮件程序测试需要勾上ssl认证
