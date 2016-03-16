import pygeoip
import stem.control
import pdb
from stem.descriptor.remote import DescriptorDownloader
from stem.descriptor.router_status_entry import RouterStatusEntryV3
from stem.descriptor import parse_file

rawdata = pygeoip.GeoIP('GeoLiteCity.dat')

def get_long_lat_ip(ip):
    data = rawdata.record_by_name(ip)
    country = data['country_name']
    city = data['city']
    longi = data['longitude']
    lat = data['latitude']
   # print '[x] '+str(city)+',' +str(country)
    print '[x] Latitude: '+str(lat)+ ', Longitude: '+ str(longi)
    return str(longi)+" "+str(lat)
def get_top_relay_long_lat():
  """
  Gets the top (the top criteria being the router's bandwidth) relays in a Country
  """
  relay_locations={}
  downloader = DescriptorDownloader(
    use_mirrors = True,
    timeout = 10,
  )
  query = downloader.get_consensus()
  i=0
  for desc in query.run():
    #pdb.set_trace()
    relay_locations[i] = [desc.fingerprint, get_long_lat_ip(desc.address)]
    with open('Longitude_Latitude_tor_nodes.txt', "a") as the_file:
      the_file.write(desc.fingerprint+' '+get_long_lat_ip(desc.address)+'\n')

    i=i+1

  
  return relay_locations

print get_top_relay_long_lat()
