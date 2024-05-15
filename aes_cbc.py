from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

# 如果text不足16位的倍数就用空格补足为16位
def add_to_16(text):
    if len(text.encode('utf-8')) % 16:
        add = 16 - (len(text.encode('utf-8')) % 16)
    else:
        add = 0
    text = text + ('\0' * add)
    return text.encode('utf-8')

# 加密函数
def encrypt(text, key, iv):
    mode = AES.MODE_CBC
    text = add_to_16(text)
    cryptos = AES.new(key=key.encode('utf-8'), mode=mode, iv=iv.encode('utf-8'))
    cipher_text = cryptos.encrypt(text)
    # 因为AES加密后的字符串不一定是ascii字符集的，输出保存可能存在问题，所以这里转为16进制字符串
    return b2a_hex(cipher_text)

# 解密后，去掉补足的空格用strip() 去掉
def decrypt(text, key, iv):
    mode = AES.MODE_CBC
    cryptos = AES.new(key=key.encode('utf-8'), mode=mode, iv=iv.encode('utf-8'))
    plain_text = cryptos.decrypt(a2b_hex(text))
    return bytes.decode(plain_text).rstrip('\0')

# # 使用方式，key 和 iv 必须为 16 位以上
# e = encrypt("hello world","1234567812345678","1234567812345678")  # 加密
# d = decrypt(e,"1234567812345678","1234567812345678")  # 解密
# print(e)
# print(d)