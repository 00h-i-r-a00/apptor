import StringIO
import sys
import time
import pycurl
import pygeoip
import stem.control
from stem.descriptor.remote import DescriptorDownloader
from stem.descriptor.router_status_entry import RouterStatusEntryV3
import pdb
from stem.descriptor import parse_file
import stem.process
from stem.util import term

GUARD_FINGERPRINT = 'B0279A521375F3CB2AE210BDBFC645FDD2E1973A'
MIDDLE_FINGERPRINT = '7AAE87CD729464096B63D6C3D4C20E92D2545745'
SOCKS_PORT = 9050
CONNECTION_TIMEOUT = 30  # timeout before we give up on a circuit

#####Get Urls########

data = sys.stdin.read()
url_list = data.split()


####################

#####Map a Router's IP to its location#########################
def get_location(ip):
  """Maps an IP to an approximate geographical region"""

  rawdata = pygeoip.GeoIP('GeoLiteCity.dat')
  data = rawdata.record_by_name(ip)
  country = data['country_name']
  return country

def get_top_relays(country):
  """
  Gets the top (the top criteria being the router's bandwidth) relays in a Country
  """
  downloader = DescriptorDownloader(
    use_mirrors = True,
    timeout = 10,
  )

  query = downloader.get_consensus()
  router_bandwidth = {}
  router_bandwidth_sorted = {}
  i = 0

  for desc in query.run():

    router_bandwidth[i] = [desc.fingerprint, desc.exit_policy, desc.bandwidth, get_location(desc.address)]
    i=i+1

  i=0

  sorted_relays = []
 ###sort relays in descending order###
 
  for key, value in sorted(router_bandwidth.items(), key = lambda fun: fun[1][2], reverse = True):
    sorted_relays.insert(i, [value[0], value[1], value[2], value[3]]) 
    i = i+1

  
  sorted_exit_relays = []
  i = 0

  for item in sorted_relays:
    #pdb.set_trace()
    if item[1].is_exiting_allowed() == True and item[3].lower() == country.lower():
      sorted_exit_relays.insert(i, [item[0], item[3]]) ## get the fingerprint (plus location) if exiting allowed
      i = i+1
  #pdb.set_trace()
  return sorted_exit_relays 


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

def scan(controller, path, url, location):
  """
  Create a circuit as specified by the "path"
  Using the circuit created, fetch a url and get its delay i.e the delay between the HTTP Request and the HTTP Response
  """

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
      print "I M inside if"
      with open('delay_tor_nodes_' + location + '.txt', "a") as the_file:
         the_file.write(url + ' ' + str(time.time() - start_time) + ' ' + exit_node + ' ' + location + '\n')
      print "I AM HERE ++++++++++++++++++++++++"
     
    #return http_code, time.time() - start_time()

  finally:
    controller.remove_event_listener(attach_stream)
    controller.reset_conf('__LeaveStreamsUnattached')

def run_circuit(url, location):
  print "In run with location: "+location+" and Url: "+ url
  
  with stem.control.Controller.from_port() as controller:

    controller.authenticate()
    
    top_100_fingerprints = get_top_relays(location) # get fingerprints of top 100 exit nodes

    time_taken = [] 
    count = 1
    top_100_fingerprints = top_100_fingerprints[0:5] #1000 at the moment
  
    for fingerprint in top_100_fingerprints:
      location2 = fingerprint[1]
      fingerp = fingerprint[0] 
      print "location2: "+location2
      print "fingerprint: "+fingerp+"\n"

      try:
        for count in xrange(1,100):
          print "In try: "
          print "Count is " + str(count) 
          if GUARD_FINGERPRINT == fingerp or MIDDLE_FINGERPRINT == fingerp or fingerp == '4B170476D09459328438F3E68ED19516C9F75A80':
            continue

          scan(controller, [GUARD_FINGERPRINT, MIDDLE_FINGERPRINT, fingerp], url, location2) #check whether location or location2
          #print "HTTP Code" + str(http_code) + "Time Elapsed :" + str(time_e)
      except Exception as exc:
        print('%s => %s' % (fingerprint[0], exc))

def main():
  location = sys.argv[1]
  print "In main with location: "+location
  for url in url_list:
    run_circuit(url, location)
 
if __name__ == "__main__":
  main()
