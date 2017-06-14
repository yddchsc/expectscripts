#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pexpect
import os, sys
import time
import threading
import Queue

queue = Queue.Queue()

# 获取路由器的ip和password
def get_hosts():
    i = 0
    ip = []
    for line in open("hostlist.txt"):
        if i%2 == 0:
            j = i/2
            ip.append({})
            ip[j]['ip'] = line
        else:
            ip[j]['password'] = line
        i += 1
    return ip

# 登录及其判断
def ssh_login(ip, password, fout, child):
    i = child.expect(['yes/no', 'Password:','No route to host', pexpect.TIMEOUT])

    if i == 0:
        child.sendline ('yes')
        child.expect ('Password: ')
        # 输入密码.
        child.sendline(password)
        ssh_enable(ip, password, fout, child)
    elif i == 1:
        child.sendline(password)
        ssh_enable(ip, password, fout, child)
    elif i == 2:
        child.sendline("No route to host:")
        return None
    else:
        child.sendline('login time out:')
        return None

#enable及登录密码错误判断
def ssh_enable(ip, password, fout, child):
    i = child.expect([pexpect.TIMEOUT, 'Password:','>'])
    if i == 0:
        child.sendline('login time out:')
        return None
    elif i == 1:
        child.sendline('error password')
        return None
    else:
        child.sendline('enable')

#进入特权模式是否成功判断
def ssh_checkenable(ip, password, fout, child):
    i = child.expect(['#','Password:',pexpect.TIMEOUT])

    if i == 0:
        child.sendline('terminal length 0')
    elif i == 1:
        child.sendline(password)
    else:
        child.sendline('time out:')
        return None

#判断进入特权模式是否成功
def ssh_length(ip, password, fout, child):
    i = child.expect(['#','Password:',pexpect.TIMEOUT])

    if i == 0:
        child.sendline('terminal length 0')
    elif i == 1:
        child.sendline('enable password error:')
        return None
    else:
        child.sendline('time out:')
        return None

# 执行show run命令
def ssh_show(ip, password, fout, child):
    i = child.expect(['#',pexpect.TIMEOUT])
    if i == 0:
        child.sendline('show run')
    else:
        child.sendline('time out')
        return None
def ssh_start(user, ip, password):
    # 只能使用file的构造函数才能在文件中得到log的内容，不能使用open()
    fout = file(ip[:-1]+'.txt', "ab")

    # 为 ssh 命令生成一个 spawn 类的子程序对象.
    child = pexpect.spawn('ssh %s@%s'%(user, ip))

    print ip
    child.logfile = fout

    ssh_login(ip, password, fout, child)
    ssh_checkenable(ip, password, fout, child)
    ssh_length(ip, password, fout, child)
    ssh_show(ip, password, fout, child)
    
    #必须使用sleep函数才能捕获到show run的输出
    time.sleep(1)

    i = child.expect(['#',pexpect.TIMEOUT])
    fout.close()
    if i == 0:
        return child
    else:
        child.sendline('time out')
        return None
def main ():
    #生成四个线程
    for i in range(4):
        t = Threadshow(queue)
        #把主线程设置为守护线程，如果主线程执行结束，则不论子线程是否完成,一并和主线程退出。
        t.setDaemon(True)
        t.start()
 
    #向队列中填充数据
    ip = get_hosts()
    for data in ip:
        queue.put(data)
    
    #阻塞，直到queue中的数据均被删除或者处理。为队列中的每一项都调用一次。
    queue.join()

class Threadshow(threading.Thread):
    def __init__(self,queue):
        threading.Thread.__init__(self)
        self.queue = queue
    def run(self):
        while True:
            #循环从队列中获取数据
            data = self.queue.get()
            child = ssh_start('yddchsc', data['ip'], data['password'])
            child.close()
            #通知队列任务完成
            #每次从queue中get一个数据之后，当处理好相关问题，最后调用该方法，以提示queue.join()是否停止阻塞，让线程向前执行或者退出
            self.queue.task_done()

if __name__ == '__main__':
    main()