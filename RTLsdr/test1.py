#! /usr/bin/python3 -u

# Simple esample taken from librtlsdr website.
# Open RTL device and read some samples.

from rtlsdr import RtlSdr

sdr = RtlSdr()

# configure device
sdr.sample_rate = 2.048e6  # Hz
sdr.center_freq = 70e6     # Hz
sdr.freq_correction = 60   # PPM
sdr.gain = 'auto'

x=sdr.read_samples(512)
print(x,len(x))
