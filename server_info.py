
"""
采集机器自身信息
主机名
内存
ip与mac地址
cpu信息
硬盘分区信息
制造商信息
出厂日期
系统版本
"""
import socket
import psutil
import subprocess
import time
import platform
import json
import requests

device_white = ['ens36']


def get_hostname():
    return socket.gethostname()


def get_meminfo():
    cmd="""free -gh|grep Mem|awk '{print $2}' """
    mem_data=subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    for mem in mem_data.stdout.readlines():
        mem=mem.strip().decode()
        return mem


def get_device_info():
    for device, device_info in psutil.net_if_addrs().items():
        if device in device_white:
            tmp_device = {}
            for sinc in device_info:
                if sinc.family == 2:
                    ip = sinc.address
                if sinc.family == 17:
                    mac = sinc.address
    return ip,mac   

def get_cpu_info():
    ret = {'cpu':'','num':0}
    with open('/proc/cpuinfo') as f:
        for line in f:
            tmp = line.split(":")
            key = tmp[0].strip()
            if key == "processor":
                ret['num'] += 1
            if key == "model name":
                ret['cpu'] = tmp[1].strip()
    return ret

def get_disk_info():
    cmd = """ lsblk |egrep '^sd[a-z]+' """
    disk_data = subprocess.Popen(cmd, shell=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    patition_size = []
    for dev in disk_data.stdout.readlines():
        dev=dev.decode()
        size = dev.strip().split()[3] 
        patition_size.append(size)
    return " + ".join(patition_size)

def get_manufacturer_info():
    ret = {}
    cmd = """/usr/sbin/dmidecode | grep -A6 'System Information'"""
    manufacturer_data = subprocess.Popen(cmd, shell = True, stdout = subprocess.PIPE, stderr=subprocess.STDOUT)

    for line in manufacturer_data.stdout.readlines():
        line=line.decode()
        if 'Manufacturer' in line:
            ret['manufacturers'] = line.split(':')[1].strip()
        elif 'Product Name' in line:
            ret['server_type'] = line.split(':')[1].strip()
        elif 'Serial Number' in line:
            ret['sn'] = line.split(':')[1].strip()
        elif 'UUID' in line:
            ret['uuid'] = line.split(':')[1].strip()
    return ret

def get_real_date():
    cmd = """/usr/sbin/dmidecode | grep -i release"""
    date_data = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    real_date = date_data.stdout.readline().decode().split(':')[1].strip()
    return time.strftime('%Y-%m-%d', time.strptime(real_date, "%m/%d/%Y"))

def get_os_version():
    return ' '.join(platform.linux_distribution())


def send(data):
     url = 'http://host/test/api/'
     r = requests.post(url, data=data)
     print(r.status_code,r.content)

def run():
    data = {}
    data['name'] = get_hostname()
    data['ip'],data['mac'] = get_device_info()

    cpu_info = get_cpu_info()
    data['cpu'] = "{cpu} {num}".format(**cpu_info)
    data['disk'] = get_disk_info()
    data['memory'] = get_meminfo()
    data.update(get_manufacturer_info())
    data['manufacture_date'] = get_real_date()
    data['os'] = get_os_version()
    if 'virtualbox' == data['server_type']:
        data['vm_status'] = 0
    else:
        data['vm_status'] = 1
    #print(data)
    send(data)


if __name__ == "__main__":
    run()
