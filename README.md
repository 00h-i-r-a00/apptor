# Tor Relay Measurements

1) get_delay.py: Reference code for taking delay.


2) get_latencies.py=>
Command: awk "FNR >= 2 && FNR <=8"  topsites.txt | python get_latencies.py Germany

3) plot_cdfs: Plot latencies by taking.
