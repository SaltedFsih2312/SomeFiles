## 配置 Keppalived

>环境：
>系统：CentOS 8.3，使用 `CentOS-8.3.2011-x86_64-dvd1.iso` 内自带的软件包，启用防火墙、SELinux
>主机：www1.example.com (172.20.83.1/16) -- CentOS 8.3
>www1.example.com (172.20.83.2/16) -- CentOS 8.3
>www.example.com (172.20.100.100/16) (虚拟 IP) -- CentOS 8.3

```bash
#安装服务
dnf -y install keepalived

#修改配置文件 /etc/keepalived/keepalived.conf
#主服务器的配置，如果只是提供 HTTP/HTTPS 服务的话只需要保留下面的这些
global_defs {
   router_id WWW1
}

vrrp_instance VI_1 {
    state MASTER		#表示这是主还是备
    interface ens33		#在什么网卡上广播 ARP
    virtual_router_id 50
    priority 150		#优先级
    advert_int 1
    authentication {
        auth_type PASS
        auth_pass 2021
    }
    virtual_ipaddress {
        172.20.100.100/16		#可以指定掩码，默认是 32
    }
}

virtual_server 172.20.100.100 80 {
    delay_loop 6
    lb_algo rr
    lb_kind NAT
    persistence_timeout 50
    protocol TCP

    real_server 172.20.83.1 80 {
        weight 1
    }
}

#备份服务器，可以直接把主服务器的配置复制过来改，下面这些是要改的
router_id WWW2
state BACKUP
priority 50
real_server 172.20.83.2 80

#放行 VRRP 协议
firewall-cmd --add-protocol=112
firewall-cmd --add-protocol=112 --per

#启动 Keepalive 服务
systemctl enable keepalived.service --now
```
### 测试

```
检查浮动 IP 是否存在于优先级最高的主节点中
检查其他节点是否存在浮动 IP
关闭拥有浮动 IP 的节点的 Keepalived 服务，看看浮动 IP 是否已经迁移到其他节点上
```



## IPv6

IPv6 的地址直接写上去就行，不需要加 [] ，但是要把 IPv6 地址后缀写上
```bash
...
virtual_ipaddress {
		2021::10/64
}
...
```



## 参考链接

https://www.redhat.com/sysadmin/keepalived-basics