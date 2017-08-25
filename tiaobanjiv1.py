#!/usr/bin/python
# -*- coding: UTF-8 -*-

import pexpect
import os, sys
import time
import threading
import Queue

queue = Queue.Queue()
# pingfout = file('ping.txt', "ab")
# telnetfout = file('telnet.txt', "ab")
# sshfout = file('ssh.txt', "ab")
outputs = open('jieguo.txt','w+')

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
def tracerouteCheck(ip,outputString):
	print('traceroute '+ip)
	traceroutecheck = pexpect.spawn("traceroute %s" % (ip))
	check = traceroutecheck.expect(['  \* \* \*',pexpect.EOF],timeout=None)
	if check == 0 or check == 1:
		b = traceroutecheck.before.split('\r\n')[1:-1]
		bs = ''
		for data in b:
			bs = bs + data.strip().split(' ')[2] + '-->'
		#bs = '\t'.join(b)
		outputString = outputString + bs[:-3] + '\n'
	else:
		outputString = outputString + '\t'.join(traceroutecheck.before.split('\n')[1:]) + '\n'

	return traceroutecheck,outputString
def pingCheck(name,ip):
	print('ping ' + ip)
	pingcheck = pexpect.spawn("ping -c1 %s" % (ip))

	#pingcheck.logfile = pingfout

	outputString = name[:-1] +  '\t' + ip + '\t'
	a = 0

	check = pingcheck.expect([pexpect.TIMEOUT,"1 packets transmitted, 1 received, 0% packet loss","live exceeded","time 10000ms",pexpect.EOF])
	if check == 0:
		outputString += "timeout\t-1\t-1\t"
		traceroutecheck,outputString = tracerouteCheck(ip,outputString)
		traceroutecheck.close()
	elif check == 1:
		outputString += "1\t"
		a = 1
	elif check == 2:
		outputString = outputString + "LiveExceeded\t-1\t-1\t" + pingcheck.before.split('\r\n')[1].split(' ')[1] + '\n'
	elif check == 3:
		outputString = outputString + "Time10000ms\t-1\t-1\t"
		traceroutecheck,outputString = tracerouteCheck(ip,outputString)
		traceroutecheck.close()
	else:
		outputString = outputString +  ' '.jion(pingcheck.before.split('\r\n')) + "\t-1\t-1\t"
		traceroutecheck,outputString = tracerouteCheck(ip,outputString)
		traceroutecheck.close()

	return pingcheck,outputString,a

def telnetCheck(ip,outputString):
	print('telnet '+ip)
	telnetcheck = pexpect.spawn("telnet %s" % (ip))

	#telnetcheck.logfile = telnetfout

	check = telnetcheck.expect(["sername","\*\*\*\*\*\*\*\*","ogin","refused","Connection closed","timed out",pexpect.TIMEOUT,pexpect.EOF],timeout=10)

	#print telnetcheck.before

	if check == 0 or check == 1 or check == 2:
		outputString += "1\t"
	elif check == 3:
		outputString += "refused\t"
	elif check == 4:
		outputString += "closed\t"
	elif check == 5:
		outputString += "TimedOut\t"
	elif check == 6:
		outputString += "out10s\t"
	else:
		outputString = outputString + ' '.join(telnetcheck.before.split('\n')) + '\t'

	return telnetcheck,outputString

def sshCheck(ip,outputString):
	print('ssh '+ip)
	sshcheck = pexpect.spawn("ssh -p 22 xxxxx@%s" % (ip))

	#sshcheck.logfile = sshfout

	check = sshcheck.expect(["assword","yes/no",'o route to host',"refused","timed out",pexpect.TIMEOUT,pexpect.EOF],timeout=10)

	#print sshcheck.before

	if check == 0 or check == 1:
		outputString += "1\n"
	elif check == 2:
		outputString += "noRoute\n"
	elif check == 3:
		outputString += "refused\n"
	elif check == 4:
		outputString += "TimedOut\n"
	elif check == 5:
		outputString += "out10s\n"
	else:
		outputString = outputString + ' '.join(sshcheck.before.split('\n')) + '\n'

	return sshcheck,outputString

def main():
	timestart = time.time()
	#生成四个
	for i in range(8):
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
			pingcheck,outputString,a = pingCheck(data['name'],data['ip'])
			pingcheck.close()
			if a == 1:
				telnetcheck,outputString = telnetCheck(data['ip'],outputString)
				telnetcheck.close()
				sshcheck,outputString = sshCheck(data['ip'],outputString)
				sshcheck.close()
			outputs.write(outputString)
			outputs.flush()

			#通知队列任务完成
			
			#每次从queue中get一个数据之后，当处理好相关问题，最后调用该方法，以提示queue.join()是否停止阻塞，让线程向前执行或者退出
			self.queue.task_done()

if __name__ == '__main__':
	main()
	# pingfout.close()
	# telnetfout.close()
	# sshfout.close()
	outputs.close()
