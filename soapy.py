#! /usr/bin/python3 -u
#
# NEW: /home/joea/.venv/bin/python -u
# OLD: /usr/bin/python3 -u 

# Basic SoapySDR/Python example from https://github.com/pothosware/SoapySDR/wiki/PythonSupport

import SoapySDR
from SoapySDR import * #SOAPY_SDR_ constants
import numpy #use numpy for buffers

#enumerate devices
results = SoapySDR.Device.enumerate()
for result in results: print(result)

#create device instance
#args can be user defined or from the enumeration result
args = dict(driver="rtlsdr")
sdr = SoapySDR.Device(args)

#query device info
print(sdr.listAntennas(SOAPY_SDR_RX, 0))
print(sdr.listGains(SOAPY_SDR_RX, 0))
freqs = sdr.getFrequencyRange(SOAPY_SDR_RX, 0)
for freqRange in freqs: print(freqRange)

#apply settings
sdr.setSampleRate(SOAPY_SDR_RX, 0, 1e6)
sdr.setFrequency(SOAPY_SDR_RX, 0, 912.3e6)

#setup a stream (complex floats)
rxStream = sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32)
sdr.activateStream(rxStream) #start streaming

#create a re-usable buffer for rx samples
buff = numpy.array([0]*1024, numpy.complex64)

#receive some samples
for i in range(10):
    sr = sdr.readStream(rxStream, [buff], len(buff))
    print(sr.ret) #num samples or error code
    print(sr.flags) #flags set by receive operation
    print(sr.timeNs) #timestamp for receive buffer

#shutdown the stream
sdr.deactivateStream(rxStream) #stop streaming
sdr.closeStream(rxStream)
