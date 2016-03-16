import pygeoip
import stem.control
import pdb
from stem.descriptor.remote import DescriptorDownloader
from stem.descriptor.router_status_entry import RouterStatusEntryV3
from stem.descriptor import parse_file

rawdata = pygeoip.GeoIP('GeoLiteCity.dat')

def get_long_ip(ip):
    data = rawdata.record_by_name(ip)
    country = data['country_name']
    city = data['city']
    longi = data['longitude']
    lat = data['latitude']
    return str(longi)

def get_lat_ip(ip):
    data = rawdata.record_by_name(ip)
    country = data['country_name']
    city = data['city']
    longi = data['longitude']
    lat = data['latitude']
    return str(lat)


def get_relay_long_lat(relay_type):
  """
  Gets the top (the top criteria being the router's bandwidth) relays in a Country
  """
  relay_locations={}

  downloader = DescriptorDownloader(
    use_mirrors = True,
    timeout = 10,
  )
  query = downloader.get_consensus()
  
  for desc in query.run():
    if relay_type == 'E':
      if desc.exit_policy.is_exiting_allowed() == True: 

        relay_locations[desc.fingerprint] = [get_long_ip(desc.address), get_lat_ip(desc.address)]

        with open('Longitude_Latitude_Exit_nodes.txt', "a") as the_file:
          the_file.write(desc.fingerprint+' '+get_long_ip(desc.address)+' '+get_lat_ip(desc.address)+'\n')
        continue

    else:
      if 'Guard' in desc._entries[u's'][0][0] and desc.exit_policy.is_exiting_allowed() != True:

        relay_locations[desc.fingerprint] = [get_long_ip(desc.address), get_lat_ip(desc.address)]

        with open('Longitude_Latitude_Middle_nodes.txt', "a") as the_file:
          the_file.write(desc.fingerprint+' '+get_long_ip(desc.address)+' '+get_lat_ip(desc.address)+'\n')
        continue
    
  return relay_locations

## 'M' for middle and 'E' for exit

print get_relay_long_lat('M')