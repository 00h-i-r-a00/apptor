import pdb
import StringIO
import sys
import time
import pycurl
import pygeoip
import stem.control
from stem.descriptor.remote import DescriptorDownloader
import pandas as pd
import pandas as pd
import numpy as np 
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
import random
import socket
import pickle
from numpy.random import choice
from datetime import datetime, timedelta


rawdata = pygeoip.GeoIP('/home/hira/tor-project/GeoLiteCity.dat')
SOCKS_PORT = 9050
CONNECTION_TIMEOUT = 300

##create circuits
##get times in a nested list
## plot those 


###################33
def query(url):
	"""
	Uses pycurl to fetch a site using the proxy on the SOCKS_PORT. Returns the http code corresponding to an HTTP Request
	"""

	output = StringIO.StringIO()

	query = pycurl.Curl()
	query.setopt(pycurl.URL, url)
	query.setopt(pycurl.PROXY, '127.0.0.1')
	query.setopt(pycurl.PROXYPORT, SOCKS_PORT)
	query.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS5_HOSTNAME)
	query.setopt(pycurl.CONNECTTIMEOUT, CONNECTION_TIMEOUT)
	query.setopt(pycurl.WRITEFUNCTION, output.write)
	query.setopt(pycurl.VERBOSE, True)
	query.setopt(pycurl.FOLLOWLOCATION, 1)  
	query.perform()

  #time_elapsed = query.getinfo(query.TOTAL_TIME)
	http_code = query.getinfo(query.HTTP_CODE)
  
	return http_code

def scan(controller, path):
	"""
	Create a circuit as specified by the "path"
	Using the circuit created, fetch a url and get its delay i.e the delay between the HTTP Request and the HTTP Response
	"""
	url = 'https://bing.com'
	circuit_id = controller.new_circuit(path, await_build = True)

	def attach_stream(stream):
		if stream.status == 'NEW':
			controller.attach_stream(stream.id, circuit_id)

	controller.add_event_listener(attach_stream, stem.control.EventType.STREAM)

	try:
		controller.set_conf('__LeaveStreamsUnattached', '1')  # leave stream management to us
		start_time = time.time()
	#pdb.set_trace()
	
		http_code = query(url)
		exit_node = path[2]
	#pdb.set_trace()
		if str(http_code) == '200':
			return http_code, time.time() - start_time

	finally:
		controller.remove_event_listener(attach_stream)
		controller.reset_conf('__LeaveStreamsUnattached')


def run_circuit(guard_fp, middle_node_fp, exit_node_fp):
	#pdb.set_trace()
	time_ = 100*[0]
	
	for i in xrange(100):
		try:	
			with stem.control.Controller.from_port() as controller:
				controller.authenticate()
				http_code, time_elapsed = scan(controller, [guard_fp, middle_node_fp, exit_node_fp])
				time_.insert(i, time_elapsed)
			
		except Exception as exc:
			print('Exception: ' , exc)
	
	return time_
	

#######################333
def main():
	
	fp_bandwidths = {}

	with open("bandwidth_2.pickle", 'rb') as f:
		fp_bandwidths = pickle.load(f)

	#pdb.set_trace()
	times = [[0]*100 for i in xrange(10)]
	guard_fp = 'BC924D50078666A0208F9D75F29CA73645FB604D'
	
	for i in xrange(10):
		
		mid_fp = fp_bandwidths[i][1]
		ex_fp = fp_bandwidths[i][2]
		
		times[i] = run_circuit(guard_fp, mid_fp, ex_fp)
	pdb.set_trace()
	with open('lim_bands.pickle', 'wb') as f:
		pickle.dump(times, f)
		
if __name__ == "__main__":
	main()
