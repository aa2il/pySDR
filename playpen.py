#! /home/joea/miniconda3/envs/aa2il/bin/python -u
#
# NEW: /home/joea/miniconda3/envs/aa2il/bin/python -u
# OLD: /usr/bin/python3 -u 
#######################################################################################
#
# SDRP Play Pen - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Test routines for SDR Play / RTL / Soapy SDR drivers.
#
#######################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
#######################################################################################

import SoapySDR
from SoapySDR import *                # SOAPY_SDR_ constants
import sys
from params import *
from sig_proc import up_dn

#######################################################################################

# Function to print elements of a list returned by soapy interface
def print_elements(els):
    for e in els:
        print(e)
    
# Playpen to see how soapy sdr interface works
# See ~/Dev/SoapySDRPlay/Settings.cpp to see what is available
def sdrPlayPen(P):

    # Look for SDR devices
    print("\n**************** SOAPY PLAYPEN ***********************\n")
    print(P.SDR_TYPE)
    print("--- SDR Devices ---")
    results = SoapySDR.Device.enumerate()
    for result in results: print(result)

    # Create device instance
    # args can be user defined or from the enumeration result
    args = dict(driver=P.SDR_TYPE)
    sdr = SoapySDR.Device(args)
    
    # Query device info
    print("\n--- Device Info ---")
    print("HW info=",sdr.getHardwareInfo())
    print("Antennas=",sdr.listAntennas(SOAPY_SDR_RX, 0))
    print("Bandwidths=",sdr.listBandwidths(SOAPY_SDR_RX, 0))
    print("Clocks=",sdr.listClockSources())
    print("Freqs=",sdr.listFrequencies(SOAPY_SDR_RX, 0))
    print("Gains=",sdr.listGains(SOAPY_SDR_RX, 0))
    print("Sample rates=",sdr.listSampleRates(SOAPY_SDR_RX, 0))
    print("Regs=",sdr.listRegisterInterfaces())
    print("Sensors=",sdr.listSensors(SOAPY_SDR_RX, 0))
    print("GPIOs=",sdr.listGPIOBanks())
    print("UARTs=",sdr.listUARTs())
    #print("Native Format =",sdr.GetNativeStreamFormat(SOAPY_SDR_RX, 0,rmax))
    #print("max=",rmax)
    #sys.exit(0)
    
    freqs = sdr.getFrequencyRange(SOAPY_SDR_RX, 0)
    print("Freq range:")
    for f in freqs: print(f)
    
    bws = sdr.getBandwidthRange(SOAPY_SDR_RX, 0)
    print("Available bandwidths=")
    for bw in bws: print(bw)
    
    # THis doesn't work 
    #srates = sdr.getSampleRateRange(SOAPY_SDR_RX, 0)
    #print("Available Sample Rates=")
    #for f in srates: print(f)
    
    # See SoapySDRPlay/Settings.cpp to see what is available
    print("\n--- More Device Info ---")
    print("Driver key          =",sdr.getDriverKey())
    print("HW key              =",sdr.getHardwareKey())
    print("HW info             =",sdr.getHardwareInfo())
    print("Num Channels        =",sdr.getNumChannels(SOAPY_SDR_RX))
    print("Antennas            =",sdr.listAntennas(SOAPY_SDR_RX, 0))
    # setAntenna is a no-op - maybe we can hack this later to select A/B/HiZ
    print("Antenna             =",sdr.getAntenna(SOAPY_SDR_RX, 0))
    print("Has DC Offset Mode  =",sdr.hasDCOffsetMode(SOAPY_SDR_RX, 0))
    # there is a setDCOffsetMode
    print("Get DC Offset Mode  =",sdr.getDCOffsetMode(SOAPY_SDR_RX, 0))
    print("Has DC Offset       =",sdr.hasDCOffset(SOAPY_SDR_RX, 0))

    # Not sure why RFGR is disabled in soapy driver?
    Gains=sdr.listGains(SOAPY_SDR_RX, 0)
    print("Gains               =",Gains)
    print("Has Gain Mode       =",sdr.hasGainMode(SOAPY_SDR_RX, 0))
    # there is a setGainMode
    print("Get Gain Mode       =",sdr.getGainMode(SOAPY_SDR_RX, 0))
    # there is a setGain
    for g in Gains:
        print("Get Gain            =",g,sdr.getGain(SOAPY_SDR_RX, 0,g))
        print("Get Gain Range      =",g,sdr.getGainRange(SOAPY_SDR_RX, 0,g))
    
    # Freq interface
    print("\nGet Frequency       =", sdr.getFrequency(SOAPY_SDR_RX, 0))
    print("Get Frequency RF    =", sdr.getFrequency(SOAPY_SDR_RX, 0,"RF"))
    print("Get Frequency CORR  =", sdr.getFrequency(SOAPY_SDR_RX, 0,"CORR"))
    print("Freqs               =",sdr.listFrequencies(SOAPY_SDR_RX, 0))
    print("Freq Range          =")
    print_elements( sdr.getFrequencyRange(SOAPY_SDR_RX, 0,"RF") )
    print("Freq Args Info      =",sdr.getFrequencyArgsInfo(SOAPY_SDR_RX, 0))

    # Clock
    print("\nClock Sourcess=",sdr.listClockSources())
    print("\tGet Clock Source =", sdr.getClockSource())
    print("\tGet Master Clock Rate =", sdr.getMasterClockRate())
    print("\tGet Reference Clock Rate =", sdr.getReferenceClockRate())

    # Time
    print("\nTime Sources=",sdr.listTimeSources())

    # Sensors
    print("\nSensors=",sdr.listSensors(SOAPY_SDR_RX, 0))
    #print("Sensor info=",sdr.getSensorInfo(SOAPY_SDR_RX))   # Doesnt work

    # Settings - see below
    #settings = sdr.getSettingInfo()
    #print("\nAvailable settings=")
    #for s in settings:
    #    print(s)
    #sys.exit(0)
    
    # This is in C interface but apparently not in python ...
    # print("Has Freq Offset     =",sdr.hasFrequencyCorrection(SOAPY_SDR_RX, 0)
    # ...but, it appears we can set the freq correction using this:
    frq=5000
    sdr.setFrequency(SOAPY_SDR_RX, 0, 'RF',frq)
    ppm=4
    sdr.setFrequency(SOAPY_SDR_RX, 0, 'CORR',ppm)
    print("\nGet Frequency RF    =", sdr.getFrequency(SOAPY_SDR_RX, 0,"RF"))
    print("Get Frequency CORR  =", sdr.getFrequency(SOAPY_SDR_RX, 0,"CORR"))
#    sys.exit(0)
    
    # There is a setSamplingRate
    print("Sample Rate         =", sdr.getSampleRate(SOAPY_SDR_RX, 0))
    print("Sample rates        =",sdr.listSampleRates(SOAPY_SDR_RX, 0))
    # Need to take closer look how to use this one - seems to check srates & decim rates
    #print("Sample Rate and Dec =", sdr.getInputSampleRateAndDecimation(SOAPY_SDR_RX, 0))
    
    # There is a setBandwidth
    print("Bandwidth            =", sdr.getBandwidth(SOAPY_SDR_RX, 0))
    print("Bandwidths           =",sdr.listBandwidths(SOAPY_SDR_RX, 0))
    print("Bandwidth Range      =")
    print_elements( sdr.getBandwidthRange(SOAPY_SDR_RX, 0) )
    # There is a getBwEnumForRate which converts a defined symbol to a bw
    # There is a getRateForBwEnum which converts a defined symbol to a bw
    
    # These don't seem to work but not improtant:
    #a=sdr.mirGetBwMhzEnum(200000.)
    #print("mirGetBwMhzEnum      =",a
    
    #a=sdr.stringToIF("Zero-IF")
    #print("stringToIF=",a
    
    # Expanding this one is a pain but it tells us a lot of what we can do
    print('\n++++++++++++++++++++++++++++++++++++++++++++++++++++++\n')
    info=sdr.getSettingInfo()
    print("getSettingInfo        =")
    print_elements(info)
    print('info=',info)
    idx=-1
    keys=[];
    for a in info:
        idx+=1
        print('\n idx=',idx,':')
        print('\t',a.key,a.name,a.value,a.description)
        keys.append(a.key);
        print_elements( a.options)
    sys.exit()
    
    # There is a writeSetting
    print('Keys=',keys)
    for s in keys:
        print("Read Setting ",s," =",sdr.readSetting(s))
    
    info = sdr.getChannelInfo(SOAPY_SDR_RX, 0)
    print("  Channel Info =",info)

    sys.exit(0)


#######################################################################################

if False:
    f1=1e6
    f2=48e3

    f1=48000
    f2=48000-100
    
    UP,DOWN = up_dn(f1,f2)
    print(UP,DOWN)
    sys.exit(0)

#
# Experiment with Soapy interface
if True:
    P=RUN_TIME_PARAMS()
    sdrPlayPen(P)
    sys.exit(0)

# Plotting examples - this is in the demos area now
if False:
    import pyqtgraph.examples
    pyqtgraph.examples.run()
    sys.exit(0)
    
