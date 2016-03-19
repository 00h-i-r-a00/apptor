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
#import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from geopy.distance import great_circle
import random
import socket
import pickle

rawdata = pygeoip.GeoIP('GeoLiteCity.dat')
SOCKS_PORT = 9050
CONNECTION_TIMEOUT = 300

def getCentroid(points):
	"""Returns the centroid of a set of points in a cluster"""
	n = len(points)
	
	sum_lon = sum([i[1] for i in points])
	sum_lat = sum([i[2] for i in points])
	
	return [sum_lon/n, sum_lat/n]
	
def get_long_lat_ip(ip):
	"""Returns Latitude, Longitude given an IP"""
	data = rawdata.record_by_name(ip)
	longi = data['longitude']
	lat = data['latitude']
	
	return longi, lat
	

def get_clusters(relay_locations):
	
	"""Returns a set of clusters for the nodes in the relay_locations list"""
	##relay locations = long, lat
	df = pd.DataFrame(relay_locations)
	#pdb.set_trace()
	df = pd.DataFrame.transpose(df) ## returns fingerprints as keys, and lat, longs as columns
	coordinates = df.as_matrix(columns=[1, 2]) #latitudes, longitudes as a matrix
	#pdb.set_trace()
	db = DBSCAN(eps=2, min_samples=1).fit(coordinates)
	labels = db.labels_
	num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
	clusters = pd.Series([coordinates[labels == i] for i in xrange(num_clusters)])
	points = list(coordinates)
	lab = list(db.labels_)
	points_clusters = [[relay_locations[i][0], points[i][0], points[i][1], lab[i]] for i in xrange(len(points))] #relay_loc, long,lat
	#pdb.set_trace()
	###points clusters is an array of the form: points_clusters[0] contains fingerprint,  
	no_points = len(points_clusters)
	clust = [0] * len(set(labels))
	
	for i in xrange(len(set(labels))):
		clust[i] = [points_clusters[x] for x in xrange(no_points) if points_clusters[x][3] == i]
			
	
	return clust
	
def get_distance(guard_loc, mid_loc, exit_loc):
	"""Get distance of the path"""
	
	google_ip = '74.125.68.113'
	total_dis = great_circle(guard_loc, mid_loc).miles + great_circle(mid_loc, exit_loc).miles + great_circle(exit_loc, get_long_lat_ip(google_ip)).miles
	return total_dis

def get_relay_long_lat(relay_type):
  """
  Returns the nodes of the given relay_type (in the argument)

  """
  relay_locations = {}

  downloader = DescriptorDownloader(
	use_mirrors = True,
	timeout = 10,
  )
  query = downloader.get_consensus()
  
  i=0
  
  
  if relay_type == 'E':
	  
	  for desc in query.run():
		  if desc.exit_policy.is_exiting_allowed() == True:
			  longi, lat = get_long_lat_ip(desc.address)
			  relay_locations[i] = [desc.fingerprint, longi, lat]
			  i+=1
			  
  elif relay_type == 'M':
	  
	  for desc in query.run():
		  if 'Guard' in desc._entries[u's'][0][0] and desc.exit_policy.is_exiting_allowed() != True:
			  longi, lat = get_long_lat_ip(desc.address)
			  relay_locations[i] = [desc.fingerprint, longi, lat]
			  i+=1
 
  return relay_locations

def measure_path_latencies():
	
	Guard_Node_fingerprint = 'BC924D50078666A0208F9D75F29CA73645FB604D'
	Guard_Node_ip = '50.116.4.107'
	gu_long, gu_lat = get_long_lat_ip(Guard_Node_ip)
	
	middle_node_locations = get_relay_long_lat('M') ## each location = [fingerprint, longitude, latitude]
	exit_node_locations = get_relay_long_lat('E')
	
	middle_relay_clusters = get_clusters(middle_node_locations)# clust[0] contains a nested list containing all nodes with label = 0
	exit_relay_clusters = get_clusters(exit_node_locations)
	
	middle_centroids = [getCentroid(middle_relay_clusters[i]) for i in xrange(len(middle_relay_clusters))] # [[0, long, lat],[1, long, lat],[2, long, lat]]
	exit_centroids = [getCentroid(exit_relay_clusters[i]) for i in xrange(len(exit_relay_clusters))]
	
	distances = [0]*len(middle_centroids)*len(exit_centroids)
	l=0
	for i in xrange(len(middle_centroids)):
		for j in xrange(len(exit_centroids)):
		
			
			mi_lat = middle_centroids[i][1] #switch long,lat => lat,long
			mi_long = middle_centroids[i][0]
				
			ex_lat = exit_centroids[j][1]
			ex_long = exit_centroids[j][0]
			
			
			distances[l] = [get_distance((gu_lat, gu_long), (mi_lat, mi_long), (mi_lat, mi_long)), i, j]
			l+=1
	
	return distances, middle_relay_clusters, exit_relay_clusters

def get_closest_middle_exit_nodes(distances, mid_clusters, ex_clusters):
	
	"""Returns the fingerprints of random mid and exit nodes from the clusters
	that give the shortest paths to the final destination:google.com"""
	
	min_distance = min(distances)
	m = min_distance[1]
	e = min_distance[2]
	
	ind_m = random.randint(0,len(mid_clusters[m]) - 1)
	ind_e = random.randint(0, len(ex_clusters[e]) - 1)
	pdb.set_trace()
	mid_fingerp, ex_fingerp = mid_clusters[m][ind_m][0], ex_clusters[e][ind_e][0]
	
	return mid_fingerp, ex_fingerp
	
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
	url = 'google.com'
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


def run_circuit(distances, mid_clusters, ex_clusters):
	
	guard_fp = 'BC924D50078666A0208F9D75F29CA73645FB604D'
	middle_node_fp, exit_node_fp = get_closest_middle_exit_nodes(distances, mid_clusters, ex_clusters)
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
	

def main():
	
	distances, mid_clusters, ex_clusters = measure_path_latencies()
	time = run_circuit(distances, mid_clusters, ex_clusters)
	#pdb.set_trace()
	
	with open('times.pickle', 'wb') as f:
		pickle.dump(time, f)
		

if __name__ == "__main__":
	main()

