from __future__ import division
import pdb

#import sys

#def hello(variable):
 #   print variable.split()

#data = sys.stdin.read()
#url_list = data.split()
#hello(data)
import sys
from csv import reader
from collections import defaultdict
import math
import numpy as np
import os
import matplotlib.pyplot as plt

def cdf_plot(url, a, country):

	
  #a = np.loadtxt("tempfile.txt", usecols = [1])
  #print a 
  a = np.array(map(float, a))
 
  max_val = int(math.ceil(np.amax(a, axis = 0)))
  
  z = max_val + 1
  cum = [0]*z
  
  for i in xrange(max_val + 1):
    for j in xrange(len(a)):
      if a[j] <= i:
        cum[i] = cum[i] + 1
  max_cum = np.amax(cum, axis = 0)
  #pdb.set_trace()
  cum2 = [float(x/max_cum) for x in cum]
  x = [i for i in xrange(z)]
  
  plt.style.use('ggplot')
  plt.title('CDF for ' + url + ' on Exit Nodes in ' + country)
  plt.ylabel('Response Times')
  plt.xlabel('CDF')
  plt.legend()
  plt.grid(True,color='k')
  plt.plot(x,cum2, linewidth = 3)
  plt.show()


def get_delays(filename, country):

  d = defaultdict(list)
  cmd = "awk '{print $3,$2}' " + filename + " > tempfile.txt"
  os.system(cmd)
  #pdb.set_trace()
  with open('tempfile.txt') as f:
   
    for k, v in reader(f, delimiter =" "): 
      d[k].append(v)

  for fingerprint, delays in d.iteritems():
    print fingerprint, delays
    cdf_plot(fingerprint, delays, country)

  
def main():
  filename = sys.argv[1]
  country = sys.argv[2]
  get_delays(filename, country)

if __name__ == "__main__":
  main()
