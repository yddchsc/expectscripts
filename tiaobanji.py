#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pexpect
import os, sys
import time
import threading
import Queue

queue = Queue.Queue()
pingfout = file('ping跳板机梳理.txt', "ab")
telnetfout = file('telnet跳板机梳理.txt', "ab")
sshfout = file('ssh跳板机梳理.txt', "ab")

# 获取路由器的ip和password
def get_hosts():
	i = 0
	ip = []
	for line in open("host.txt"):
		lines = line.split('	')
		ip.append({})
		ip[i]['ip'] = lines[0]
		ip[i]['name'] = lines[1]
		i += 1
	return ip

def pingCheck(ip):
	pingcheck = pexpect.spawn("ping -c1 %s" % (ip))

	pingcheck.logfile = pingfout

	check = pingcheck.expect([pexpect.TIMEOUT,"1 packets transmitted, 1 received, 0% packet loss",pexpect.EOF])
	if check == 0:
		print("超时 %s" % (ip))
	elif check == 1:
		print ("%s 可达" % (ip))
	else:
		print("主机 %s 不可达" % (ip))
		print pingcheck.before

	return pingcheck

def telnetCheck(ip):
	telnetcheck = pexpect.spawn("telnet %s" % (ip))

	telnetcheck.logfile = telnetfout

	check = telnetcheck.expect([pexpect.TIMEOUT,"username","refused",pexpect.EOF])
	if check == 0:
		print("telnet登录超时 %s" % (ip))
	elif check == 1:
		print ("%s 可使用telnet登录" % (ip))
	elif check == 2:
		print("主机 %s 拒绝" % (ip))
	else:
		print telnetcheck.before

	return telnetcheck

def sshCheck(ip):
	sshcheck = pexpect.spawn("ssh noccheck@%s" % (ip))

	sshcheck.logfile = sshfout

	check = sshcheck.expect([pexpect.TIMEOUT,"username","refused",pexpect.EOF])
	if check == 0:
		print("ssh登录超时 %s" % (ip))
	elif check == 1:
		print ("%s 可使用ssh登录" % (ip))
	elif check == 2:
		print("主机 %s 拒绝" % (ip))
	else:
		print sshcheck.before

	return sshcheck

def main():
	timestart = time.time()
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
	print "spend time:"+str(time.time()-timestart)

class Threadshow(threading.Thread):
	def __init__(self,queue):
		threading.Thread.__init__(self)
		self.queue = queue
	def run(self):
		while True:
			#循环从队列中获取数据
			data = self.queue.get()
			pingcheck = pingCheck(data['ip'])
			pingcheck.close()
			telnetcheck = telnetCheck(data['ip'])
			telnetcheck.close()
			sshcheck = sshCheck(data['ip'])
			sshcheck.close()

			#通知队列任务完成
			
			#每次从queue中get一个数据之后，当处理好相关问题，最后调用该方法，以提示queue.join()是否停止阻塞，让线程向前执行或者退出
			self.queue.task_done()

if __name__ == '__main__':
	main()
	pingfout.close()
	telnetfout.close()
	sshfout.close()
