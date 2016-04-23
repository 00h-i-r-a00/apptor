from __future__ import division
import pdb
import sys
from csv import reader
from collections import defaultdict
import math
import numpy as np
import os
import matplotlib.pyplot as plt
import pickle
import pdb

def cdf_plot(a, bandwidth):

	
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
  plt.title('Circuit Performance Ordered by Limiting Bandwidth', y=1.08)
  plt.ylabel('CDF')
  plt.xlabel('Response Times')
  plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.05),
          ncol=3, fancybox=True, shadow=True)
  plt.grid(True,color='k')
  lab_el = 'Limiting Bandwidth ' + str(bandwidth)
  plt.plot(x,cum2, linewidth = 2, label = lab_el)
  #plt.show()


def get_times():
	
	times = [[0]*10 for i in xrange(10)]
	bandwidths = [0*10]
	fp_bandwidths = {}
	####getting bandwidths
	with open('bandwidth_2.pickle', 'rb') as f:
		fp_bandwidths = bandwidths = pickle.load(f)
		
	with open('lim_bands.pickle', 'rb') as f:
		times = pickle.load(f)
		
	
	bandwidths = [fp_bandwidths[i][0] for i in xrange(10)]
	
	for i in xrange(10):
		cdf_plot(times[i], bandwidths[i])	
	plt.show()
	
	
def main():
  #filename = sys.argv[1]
  #country = sys.argv[2]
  get_times()

if __name__ == "__main__":
  main()
