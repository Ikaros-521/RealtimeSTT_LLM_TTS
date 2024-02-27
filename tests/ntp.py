import ntplib
from time import ctime

def get_ntp_time(server="ntp.aliyun.com"):
    c = ntplib.NTPClient()
    response = c.request(server, version=3)
    return response.tx_time

# 获取网络时间的时间戳
timestamp = get_ntp_time()

print("网络时间戳:", timestamp)
print("可读时间:", ctime(timestamp))
