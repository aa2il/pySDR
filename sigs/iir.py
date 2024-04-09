#! /usr/bin/python3

# Script to play with IIR filters

import sys
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

##############################################################################

def plot_freq_response(b,a,fs,btype):

    # Compute freq response
    w,H = signal.freqz(b,a,fs)
    f=w*fs/(2*np.pi)
    #print("w = {},h={}".format(w,h))

    # Plot it
    fig = plt.figure(figsize=(8, 6))
    plt.plot(f, 20 * np.log10(abs(H)),'r', linewidth='2')
    plt.xlabel('Frequency [Hz]', fontsize=20)
    plt.ylabel('Magnitude [dB]', fontsize=20)
    if btype=='low':
        title='Band Pass Filter'
    elif btype=='band':
        title='Band Pass Filter'
    elif btype=='stop':
        title='Band Stop Filter'
    elif btype=='notch':
        title='Notch Filter'
    else:
        title='Filter Response'
    plt.title(title, fontsize=20)
    plt.grid()
    plt.show()
    
##############################################################################
    
# Example 1 - BPF or BAND STOP 50-200 Hz
if 0:
    fs=1000
    btype='band'             # Bandpass
    #btype='stop'            # Bandstop
    b,a = signal.iirfilter(15, [50, 200], rp=3,rs=100,
                           btype=btype, analog=False, ftype='cheby2',fs=fs)
    plot_freq_response(b,a,fs,btype)
    sys.exit(0)

##############################################################################

# Example 2 - Notch 50 Hz filter
if 1:
    fs               = 1000      # Sampling freq
    notch_freq       = 50.0      # Frequency to be removed from signal (Hz)
    quality_factor   = 20.0      # Quality factor
    b, a = signal.iirnotch(notch_freq, quality_factor, fs)
    print('b=',b,'\ta=',a)
    plot_freq_response(b,a,fs,'notch')
    
    # Create test signal that is a mixture of two different frequencies + noise
    f1 = 15            # Frequency of 1st signal in Hz
    f2 = 50            # Frequency of 2nd signal in Hz
    T=2                # Generate 2-sec sample sequence 
    t = np.linspace(0, T, T*fs)
    x = np.sin(2*np.pi*f1*t) + np.sin(2*np.pi*f2*t) + \
	np.random.normal(0, .1, T*fs)*0.03

    # Plotting
    fig = plt.figure(figsize=(8, 6))
    plt.subplot(211)
    plt.plot(t, x, color='r', linewidth=2)
    plt.xlabel('Time (sec)', fontsize=20)
    plt.ylabel('x', fontsize=18)
    plt.title('Noisy Signal', fontsize=20)
    
    # Apply notch filter to the noisy signal
    #y = signal.filtfilt(b, a, x)     # Fwd & bkwd - suitable for off-line processing
    #zi = signal.lfilter_zi(b, a)     # Not worth the trouble
    #print('zi=',zi)
    y = signal.lfilter(b, a, x)      # Fwd direction only - more realistic for real-time
    
    # Now let's see if we can figure out how to do processing in chunks - LOOKING GOOD!
    # Break input sig into two chunks
    N=len(x)
    N2=int(N/2)
    print('N=',N,N2)
    x1=x[0:N2]
    x2=x[N2:]
    zi = (max(len(a), len(b)) - 1)*[0]                  # Need this so we can get z1, the state at the end
    y1,z1 = signal.lfilter(b, a, x1,zi=zi) 
    y2,z2 = signal.lfilter(b, a, x2,zi=z1 )
    yy = np.concatenate( (y1, y2) )
    #print(np.size(t),np.size(y),np.size(y1),np.size(y2),np.size(yy))

    # Break input sig into three chunks - LOOKING GOOD!
    N3=int(N/3)
    x1=x[0:N3]
    x2=x[N3:2*N3]
    x3=x[2*N3:]
    zi = (max(len(a), len(b)) - 1)*[0]
    y1,z1 = signal.lfilter(b, a, x1,zi=zi) 
    y2,z2 = signal.lfilter(b, a, x2,zi=z1 )
    y3,z3 = signal.lfilter(b, a, x3,zi=z2 )
    yyy = np.concatenate( (y1, y2, y3) )
    
    # Plot filtered signal
    plt.subplot(212)
    plt.plot(t, y)
    plt.plot(t, yy,'r:')
    plt.plot(t, yyy,'g:')
    plt.xlabel('Time (sec)', fontsize=20)
    plt.ylabel('Magnitude (dB)', fontsize=18)
    plt.title('Filtered Signal', fontsize=20)
    plt.subplots_adjust(hspace=0.5)
    fig.tight_layout()
    plt.show()

    dy=y-yy
    print('dy=',dy)
    print(max(abs(dy)))
    
    dy=y-yyy
    print('dy=',dy)
    print(max(abs(dy)))
    
    sys.exit(0)

##############################################################################

# Example 3 - LPF 200 Hz
if 0:
    fs=8000
    b, a = signal.iirfilter(7, 200, rp=3,rs=100,
                            btype='low', analog=False, ftype='ellip',fs=fs)
    plot_freq_response(b,a,fs,'low')

    # Create test signal that is a mixture of several different frequencies + noise
    frqs=[100,200,300,500]
    T=0.5                # Generate 0.5-sec sample sequence
    N=int(T*fs)
    t = np.linspace(0, T, N)
    x = np.random.normal(0, .1, N)*0.03
    for f in frqs: 
        x += np.sin(2*np.pi*f*t)

    # Plotting
    fig = plt.figure(figsize=(8, 6))
    plt.subplot(211)
    plt.plot(t, x, color='r', linewidth=2)
    plt.xlabel('Time (sec)', fontsize=20)
    plt.ylabel('Magnitude (dB)', fontsize=18)
    plt.title('Noisy Signal', fontsize=20)
    
    # Apply filter to the noisy signal
    y = signal.lfilter(b, a, x)  
    
    # Now let's see if we can figure out how to do processing in chunks - LOOKING GOOD!
    N2=int(N/2)
    print('N=',N,N2)
    x1=x[0:N2]
    x2=x[N2:]
    zi = (max(len(a), len(b)) - 1)*[0]
    y1,z1 = signal.lfilter(b, a, x1,zi=zi) 
    y2,z2 = signal.lfilter(b, a, x2,zi=z1 )
    yy = np.concatenate( (y1, y2) )
    print(np.size(t),np.size(y),np.size(y1),np.size(y2),np.size(yy))
    
    # Plot filtered signal
    plt.subplot(212)
    plt.plot(t, y)
    plt.plot(t, yy,'r:')
    plt.xlabel('Time (sec)', fontsize=20)
    plt.ylabel('Magnitude (dB)', fontsize=18)
    plt.title('Filtered Signal', fontsize=20)
    plt.subplots_adjust(hspace=0.5)
    fig.tight_layout()
    plt.show()

    dy=y-yy
    print('dy=',dy)
    print(max(abs(dy)))
    
##############################################################################

# Example 4 - From scipy manual for lfilter
if 0:

    # Generate a noisy signal to be filtered:
    rng = np.random.default_rng()
    t = np.linspace(-1, 1, 201)
    x = (np.sin(2*np.pi*0.75*t*(1-t) + 2.1) +
         0.1*np.sin(2*np.pi*1.25*t + 1) +
         0.18*np.cos(2*np.pi*3.85*t))
    xn = x + rng.standard_normal(len(t)) * 0.08
    
    # Create an order 3 lowpass butterworth filter:
    b, a = signal.butter(3, 0.05)
    
    # Apply the filter to xn. Use lfilter_zi to choose the initial condition of the filter:
    zi = signal.lfilter_zi(b, a)
    z, _ = signal.lfilter(b, a, xn, zi=zi*xn[0])
    
    # Apply the filter again, to have a result filtered at an order the same as filtfilt:
    z2, _ = signal.lfilter(b, a, z, zi=zi*z[0])
    
    # Use filtfilt to apply the filter:
    y = signal.filtfilt(b, a, xn)
    
    # Plot the original signal and the various filtered versions:
    plt.figure
    plt.plot(t, xn, 'b', alpha=0.75)
    plt.plot(t, z, 'r--', t, z2, 'r', t, y, 'k')
    plt.legend(('noisy signal', 'lfilter, once', 'lfilter, twice',
                'filtfilt'), loc='best')
    plt.grid(True)
    plt.show()
