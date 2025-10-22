
# 读取config.yaml文件，获取mobileIp

import yaml
import os

with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    mobileIp = config['mobileIp']
    print(mobileIp)

pair_port=input("请输入配对端口: ")

os.system(f"adb pair {mobileIp}:{pair_port}")

connect_port=input("请输入连接端口: ")

os.system(f"adb connect {mobileIp}:{connect_port}")




