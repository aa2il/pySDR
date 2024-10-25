#! /usr/bin/python3 -u

# Simple esample taken from librtlsdr website.
# Open RTL device, read some samples and plot a PSD

from pylab import *
from rtlsdr import *
from pprint import pprint
import inspect

sdr = RtlSdr()

# configure device
if False:
    sdr.sample_rate = 2.048e6
    sdr.center_freq = 15.5e6
    sdr.gain = 4
else:
    sdr.sample_rate = 2.4e6
    sdr.center_freq = 94.9e6
    sdr.gain = 4

print('fc=',sdr.fc)
if sdr.fc < 30e6:
    sdr.set_direct_sampling(2)
else:
    sdr.set_direct_sampling(0)
    
#print('\nsdr=')
#print(pprint(vars(sdr)))
#print('gain=',sdr.gain)

samples = sdr.read_samples(16*1024)
#samples = sdr.read_samples(256*1024)
sdr.close()
print('samples=',samples,len(samples))

# List of all attributes (including internal ones)
attributes = dir(sdr)
print(attributes)
for attr in attributes:
    if not attr.startswith('__'):
        value = getattr(sdr, attr)
        if not str(value).startswith('<bound'):
            print(f'{attr}: {value}')

# use matplotlib to estimate and plot the PSD
psd(samples, NFFT=1024, Fs=sdr.sample_rate/1e6, Fc=sdr.center_freq/1e6)
xlabel('Frequency (MHz)')
ylabel('Relative power (dB)')

show()
