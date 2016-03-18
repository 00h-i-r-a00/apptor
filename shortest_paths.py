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

rawdata = pygeoip.GeoIP('/home/hira/GeoLiteCity.dat')

def getCentroid(points):
    
    n = len(points)
    #pdb.set_trace()
    sum_lon = sum([i[1] for i in points])
    sum_lat = sum([i[2] for i in points])
    #pdb.set_trace()
    
    return [sum_lon/n, sum_lat/n]
    
def get_long_lat_ip(ip):
	data = rawdata.record_by_name(ip)
	longi = data['longitude']
	lat = data['latitude']
	
	return longi, lat
	

def get_clusters(relay_locations):
	
	"""the function contains a set of clusters for the nodes in the relay_locations"""
	df = pd.DataFrame(relay_locations)
	df = pd.DataFrame.transpose(df) ## returns fingerprints as 
	coordinates = df.as_matrix(columns=[1, 2]) #latitudes, longitudes as a matrix
	#pdb.set_trace()
	db = DBSCAN(eps=2, min_samples=1).fit(coordinates)
	labels = db.labels_
	num_clusters = len(set(labels)) - (1 if -1 in labels else 0)
	clusters = pd.Series([coordinates[labels == i] for i in xrange(num_clusters)])
	points = list(coordinates)
	lab = list(db.labels_)
	points_clusters = [[relay_locations[i][0], points[i][0], points[i][1], lab[i]] for i in xrange(len(points))]
	#pdb.set_trace()
	no_points = len(points_clusters)
	clust = [0] * len(set(labels))
	for i in xrange(len(set(labels))):
		clust[i] = [points_clusters[x] for x in xrange(no_points) if points_clusters[x][3] == i]
			
	#pdb.set_trace()
	return clust
	
def get_distance(guard_loc, mid_loc, exit_loc):
	#google_ip = socket.gethostbyname('google.com')
	#google_long, google_lat = get_long_lat_ip(google_ip)
	google_ip = '74.125.68.113'
	total_dis = great_circle(guard_loc, mid_loc).miles + great_circle(mid_loc, exit_loc).miles + great_circle(exit_loc, get_long_lat_ip(google_ip)).miles
	return total_dis

def get_relay_long_lat(relay_type):
  """

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
	
	middle_node_locations = get_relay_long_lat('M')
	exit_node_locations = get_relay_long_lat('E')
	##whats the form of the middle_relay_clusters; cluster[0] contains a nested list of all the clusters?
	middle_relay_clusters = get_clusters(middle_node_locations)
	exit_relay_clusters = get_clusters(exit_node_locations)
    
	middle_centroids = [getCentroid(middle_relay_clusters[i]) for i in xrange(len(middle_relay_clusters))] # [[0, long, lat],[1, long, lat],[2, long, lat]]
	exit_centroids = [getCentroid(exit_relay_clusters[i]) for i in xrange(len(exit_relay_clusters))]
    
	distances = [0]*len(middle_centroids)*len(exit_centroids)
	l=0
	for i in xrange(len(middle_centroids)):
		for j in xrange(len(exit_centroids)):
			#pdb.set_trace()
			
			mi_lat = middle_centroids[i][1]
			mi_long = middle_centroids[i][0]
				
			ex_lat = exit_centroids[j][1]
			ex_long = exit_centroids[j][0]
			
			
			distances[l] = [get_distance((gu_lat, gu_long), (mi_lat, mi_long), (mi_lat, mi_long)), i, j]
			l+=1
	#distances = [[distance, middle_cent_in, exit_centroid_index],[]]
	#pdb.set_trace()
     # once you get the centroid-ids which are closest you could then index into the middle_relay clusters and pick random
     # nodes and create a cluster out of them 
	return distances, middle_relay_clusters, exit_relay_clusters

def get_closest_middle_exit_nodes(distances, mid_clusters, ex_clusters):
	min_distance = min(distances)
	m = min_distance[1]
	e = min_distance[2]
	#pdb.set_trace()
	#print mid_clusters[m], ex_clusters[e]
	ind_m = random.randint(0,len(mid_clusters[m]))
	ind_e = random.randint(0, len(ex_clusters[e]))
	pdb.set_trace()
	mid_fingerp, ex_fingerp = mid_clusters[m][ind_m][0], ex_clusters[e][ind_e][0]
	#x = [distances[i] for i in xrange(len(distances))]
	#min_distance_index = x.index(min(x))
	#pdb.set_trace()
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
			return http_code, time.time() - start_time()

	finally:
		controller.remove_event_listener(attach_stream)
		controller.reset_conf('__LeaveStreamsUnattached')


def run_circuit(distances, mid_clusters, ex_clusters):
	guard_fp = 'BC924D50078666A0208F9D75F29CA73645FB604D'
	middle_node_fp, exit_node_fp = get_closest_middle_exit_nodes(distances, mid_clusters, ex_clusters)
	
	with stem.control.Controller.from_port() as controller:
		controller.authenticate()
		http_code, time_elapsed = scan(controller, [guard_fp, middle_node_fp, exit_node_fp])
			#pdb.set_trace() 
	#except Exception as exc:
	#	 print('%s => %s' % (fingerprint, exc))
	return time_elapsed
	
def get_paths(middle_node_clusters, exit_node_clusters):
	pass
	
def get_random_nodes(cluster):
	pass

def main():
	#relay_loc = get_relay_long_lat()
	#get_clusters(relay_loc)
	distances, mid_clusters, ex_clusters = measure_path_latencies()
	#get_closest_middle_exit_nodes(distances, mid_clusters, ex_clusters)
	time = run_circuit(distances, mid_clusters, ex_clusters)
	#middle_node_locations = get_relay_long_lat('M')
	#pdb.set_trace()
	print time

if __name__ == "__main__":
	main()
##More stuff to do : Once we get the latency one shortest path, select the 10 shortest paths and select the time for it.
