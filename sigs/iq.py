#! /usr/bin/python3

# Script to play with raw IQ data recorded from sdr

import sys
import numpy as np
from scipy import signal
from scipy.fft import fftshift
import matplotlib.pyplot as plt
from pprint import pprint
from fileio import SDR_FILEIO
from sig_proc import spectrum

##############################################################################

fname='raw_iq_20221230_011545.dat'           # RTL - looks saturated
fname='raw_iq_20221230_020045.dat'           # SDR Play - looks promising
fname='raw_iq_20240222_194033.dat'           # SDR Play - looks promising
fname='raw_iq_20240222_195828.dat'

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
    #plt.show()

##############################################################################

# Init param structure
class Empty():
    def __init__(self):
        pass
P = Empty()
P=None

# Read the data
sdr = SDR_FILEIO(fname,'r',P)
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
plt.show()
sys.exit(0)

# Waterfall - this seems quite fast - should bundle this up into a nice package.
# My matlab routine is waterfall.m but I don't think we need it
# This pretty much shows that the SDR data is contaminated bx of strength of
# own signal.  Not sure much more can be done?
print('Waterfalling ...')
f, t, Sxx = signal.spectrogram(x, fs, nperseg=N,window=('chebwin',-100))
#                               ,window=('kaiser', 8.6))
print('t=',t)
print('f=',f)
print(np.max(Sxx),np.min(Sxx))
PSD=fftshift( 10*np.log10( Sxx ) , axes=0 )
mx=np.max(PSD)
mn=max(np.min(PSD),mx-100)
f=.001*fftshift(f)              
print('PSD=',PSD)
print(np.max(PSD),np.min(PSD),mx,mn)
print('Plotting ...')
fig = plt.figure()
img=plt.imshow(PSD,aspect='auto',clim=[mn,mx],extent=[t[0],t[-1],f[0],f[-1]])
img.set_cmap('jet')
plt.colorbar()

# This is vry slow!
#plt.pcolormesh(t, fftshift(f), fftshift(Sxx, axes=0), shading='gouraud')

plt.ylabel('Frequency [KHz]')
plt.xlabel('Time [sec]')
#plt.show()

# We can get the periodogram PSD estimate very quickly from this
if False:
    X=np.mean(Sxx,axis=1) 
    print(np.shape(Sxx),np.shape(X),np.shape(f))
    print(X)
    fig = plt.figure()
    plt.plot(10*np.log10(X))

plt.show()


