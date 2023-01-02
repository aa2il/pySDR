#! /usr/bin/python3

# Script to play with raw IQ data recorded from sdr

import sys
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt
from pprint import pprint
import file_io
from sig_proc import spectrum

##############################################################################

fname='raw_iq_20221230_011545.dat';           # RTL - looks saturated
fname='raw_iq_20221230_020045.dat';           # SDR Play - looks promising

##############################################################################

def two_box_plot(x,X,fs,fname,f):

    # Plot signal
    fig = plt.figure()
    plt.subplot(211)
    t = np.linspace(0, len(x)/fs, len(x))
    plt.plot(t, np.real(x), color='b', linewidth=2)
    plt.plot(t, np.imag(x), color='r', linewidth=2)
    plt.xlabel('Time (sec)')
    plt.ylabel('x')
    plt.title(fname)
    plt.grid()
    plt.xlim(t[0],t[-1])

    # Plot sptectrum
    plt.subplot(212)
    plt.plot(f,X)
    plt.xlabel('Freq (KHz)')
    plt.ylabel('PSD (dB)')
    #plt.title('Periodogram', fontsize=20)
    #plt.subplots_adjust(hspace=0.5)
    plt.xlim(f[0],f[-1])
    plt.grid()
    fig.tight_layout()
    plt.show()

##############################################################################
    
# Init param structure
class Empty():
    def __init__(self):
        pass
P = Empty()
P=None

# Read the data
sdr = file_io.sdr_fileio(fname,'r',P)
x = sdr.read_data()
print('x=',x[0:10],' ... ',x[-1],len(x))

#P.IN_CHUNK_SIZE = int( P.OUT_CHUNK_SIZE*P.DOWN/float(P.UP) + 0*0.5 )
#P.lo = dsp.signal_generator(0*P.BFO,P.IN_CHUNK_SIZE,P.SRATE,True)

if P:
    print("P=")
    pprint(vars(P))

# Compute periodogram 
fs=sdr.srate
N=1024
NFFT=N*2
OVERLAP=0.5
psd  = spectrum(fs,N,NFFT,OVERLAP)
X = psd.psd_est(x,True)

frq=1e-3*psd.frq2
two_box_plot(x,X,fs,fname,frq)

    
    
