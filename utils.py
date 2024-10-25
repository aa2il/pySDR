############################################################################
#
# utils.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Support routines for pySDR.
#
############################################################################
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
############################################################################

import sys
try:
    import SoapySDR
    from SoapySDR import *                # SOAPY_SDR_ constants
except ImportError:
    print('UTIL: Unable to import SoapySDR - be sure to use -FAKE flag')
    SOAPY_SDR_RX=1
    from sig_proc import ring_buffer2,ring_buffer3

import numpy as np
import time
from Tables import MODES,SDRplaysrates,RTLsrates
import io
from threading import enumerate
from rig_io import bands,CONNECTIONS,RIGS
from multiprocessing import active_children
try:
    if True:
        from PyQt6.QtWidgets import QMessageBox,QApplication
        from PyQt6.QtGui import QIcon, QPixmap
    else:
        from PySide6.QtWidgets import QMessageBox,QApplication
        from PySide6.QtGui import QIcon, QPixmap
except ImportError:
    from PyQt5.QtWidgets import QMessageBox,QApplication
    from PyQt5.QtGui import QIcon, QPixmap

from utilities import freq2band, error_trap, whoami
from rtlsdr import RtlSdr
from sig_proc import ring_buffer2
import asyncio
import threading

############################################################################

# This is the "fake" rtl driver, probably a bad name for it but ...
# It is an alternative to Soapy and only relies on the python rtlsdr library
# which has been seen to be quite stable and reliable.  It has not been
# completely vetted but seems to work.
#
# Most of the methods in this class are meant to mimic similar methods in
# Soapy.  The exception is readSteam where I haven't quite figured out how
# to modify function arguments - but who cares!

class RTL_SDR_DRIVER:
    def __init__(self,P):
        print('======================================================Init RTL_DRIVER ...')

        self.device = RtlSdr()
        self.direct=None
        self.ret=None
        self.key='RTLSDR'
        self.P=P

        if P.MP_SCHEME==1: 
            self.rb  = ring_buffer2('IO',256*1024,PREVENT_OVERFLOW=False)
        elif P.MP_SCHEME==2: 
            self.rb  = ring_buffer3('IO',256*1024)

        # Using an avent is probably the right way to do this but I haven't gotten it to work ?!
        #self.Enable = asyncio.Event()
        #self.Enable.clear()
        self.loop = asyncio.get_event_loop()
        self.th = threading.Thread(target=self.Streamer2, args=(),
                              name='RTL Streamer')
        self.th.daemon=True
        #self.th.start()                         # Do this here if we ever get the event-drive paradigm to work
        P.threads.append(self.th)
        
    # Routine to continuously read blocks of samples from the RTL device
    # and pump them into a ringbuffer.  
    def Streamer2(self):

        print('=====================RTL_SDR_DRIVER:',whoami(),'Starting ===================================================.')
        #loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.streaming())
        
    async def streaming(self):

        """
        print('============================ RTL_SDR_DRIVER:',whoami(),
                    ' ... Waiting ... ==========================')
        await self.Enable.wait()
        
        print('============================ RTL_SDR_DRIVER:',whoami(),
                    ' ... Streaming ... ==========================')
        """
        
        async for x in self.device.stream():
            #print(x,len(x))
            self.rb.push(x)
            
        print('============================ RTL_SDR_DRIVER:',whoami(),
                    ' ... Done ... ==========================')

    def setSampleRate(self,rx, b, fs):
        print('RTL_SDR_DRIVER:',whoami(),rx, b, fs)
        self.device.sample_rate = fs
        print(self.device.rs)
        #sys.exit(0)
        
    def getSampleRate(self,rx, b):
        print('RTL_SDR_DRIVER:',whoami(),rx, b)
        return self.device.sample_rate
        
    def setFrequency(self,rx, b, tag, f=None):
        print('RTL_SDR_DRIVER:',whoami(),rx, b, tag, f)
        if f==None:
            f=tag
            self.device.center_freq = int(f)
        elif tag=='RF':
            self.device.center_freq = int(f)
        elif tag=='CORR':
            try:
                # This causes a problem - not sure why?
                #self.device.freq_correction = f
                pass
            except: 
                error_trap('UTILS->SET FREQUENCY - Unable to set freq correction')
        else:
            print(whoami(),'I dont know what I am doing here!')
        print('fc=',self.device.fc,'\tdf=',self.device.freq_correction)
        #sys.exit(0)

    def getFrequency(self,rx, b, tag):
        print('RTL_SDR_DRIVER:',whoami(),rx, b, tag)
        return self.device.center_freq
        
    def getNumChannels(self,rx):
        print('RTL_SDR_DRIVER:',whoami(),rx)
        return 1
        
    def writeSetting(self,s1,s2):
        print('RTL_SDR_DRIVER:',whoami(),s1,s2)
        if s1=='if_mode':
            pass
        elif s1=='direct_samp':
            self.direct=int(s2)
            self.device.set_direct_sampling(int(s2))
            print(int(s2))
            #sys.exit(0)
        else:
            print('RTL_SDR_DRIVER:',whoami(),'Option not implemented yet - ignored')

    def listGains(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        return self.device.valid_gains_db

    def getGainRange(self,rx,b,stage=None):
        print('RTL_SDR_DRIVER:',whoami(),rx,b,stage)
        gains=self.device.valid_gains_db
        return [min(gains),max(gains),1]
    
    def hasGainMode(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        return True
        
    def setGainMode(self,rx,b,tf):
        print('RTL_SDR_DRIVER:',whoami(),rx,b,tf)
        self.device.gain = 'auto'
        
    def getGainMode(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        return self.device.gain
        
    def getGain(self,rx,b,stage):
        gain=self.device.gain
        print('RTL_SDR_DRIVER:',whoami(),rx,b,stage,gain)
        return gain

    def setGain(self,rx,b,stage,gain):
        if gain>49.6:
            gain=49.6
        self.device.gain = gain
        print('RTL_SDR_DRIVER:',whoami(),rx,b,stage,gain)
        #sys.exit(0)
        
    def setAntenna(self,rx,b,ant):
        print('RTL_SDR_DRIVER:',whoami(),rx,b,ant)
        
    def getAntenna(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        return 0
        
    def getSettingInfo(self):
        print('RTL_SDR_DRIVER:',whoami())
        return []
    
    def listSampleRates(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        return [1.024e6,2.048e6]
    
    def listBandwidths(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami())
        return []
    
    def getBandwidth(self,rx,b):
        print('RTL_SDR_DRIVER:',whoami(),rx,b)
        bw = self.device.bandwidth
        return bw
    
    def setupStream(self,rx,fmt):
        print('RTL_SDR_DRIVER:',whoami(),rx,fmt)
        self.fmt=fmt
        return 0

    def activateStream(self,rx):
        print('RTL_SDR_DRIVER:',whoami(),rx)
        #self.Enable.set()
        #print('============================ RTL_SDR_DRIVER:',whoami(),
        #            ' ... Enabled ... ==========================',self.Enable.is_set())
        self.th.start()                         # Do this here for now until we get the event-drive paradigm to work

    def readStreamRTL(self,rx,n):

        #print('RTL_SDR_DRIVER:',whoami(),n)
        if self.rb.ready(n):
            x=self.rb.pull(n)
            #print('RTL_SDR_DRIVER:',x,n,len(x))
        else:
            x=[]
        #print('RTL_SDR_DRIVER:',whoami(),n,len(x))
        return np.array(x, np.complex64)
    
    def deactivateStream(self,rx):
        print('RTL_SDR_DRIVER:',whoami(),rx)
        #self.Enable.clear()
        #self.device.cancel_read_async()
        self.device.stop()

    def closeStream(self,rx):
        print('RTL_SDR_DRIVER:',whoami(),rx)
        #self.device.stop()
        self.device.close()

    def getDriverKey(self):
        print('RTL_SDR_DRIVER:',whoami())
        return self.key

    def getHardwareKey(self):
        print('RTL_SDR_DRIVER:',whoami())
        return self.device.get_tuner_type()
    
    def getHardwareInfo(self):
        print('RTL_SDR_DRIVER:',whoami())
        #return self.device.init_device_values()
        return []

############################################################################

def adjust_foffset(self):
    M = round( self.RB_SIZE * self.FOFFSET / self.SRATE )
    fo = M*self.SRATE/self.RB_SIZE
    if False:
        print('\nTuning offset adjustment:')
        print('   fo=',self.FOFFSET)
        print('   fs=',self.SRATE)
        print('   N=',self.RB_SIZE)
        print('   M=',M)
        print('   new fo=',fo)
        print('   change=',fo-self.FOFFSET,'\n')
        sys.exit(0)
    self.FOFFSET=fo        

# Function to apply SDR settings
def setupSDR(P):
    sdr=P.sdr;

    print('\n>>>>>>>>>>>>>>> Setting up SDR ...',P.SDR_TYPE)
    sdr.setSampleRate(SOAPY_SDR_RX, 0, P.SRATE)
    sdr.setFrequency(SOAPY_SDR_RX, 0, 'RF', P.FC[0]-P.FOFFSET)
    sdr.setFrequency(SOAPY_SDR_RX, 0, 'CORR', P.PPM)
    if P.LNA>=0:
        s="rfgain_sel"
        sdr.writeSetting(s,str(P.LNA))

    # Convert IF freq to a string
    s1="if_mode"
    if P.IF==0:
        s2 = "Zero-IF"
    else:
        s2=str(P.IF)+"kHz"
    sdr.writeSetting(s1,s2)

    if P.IFGAIN>0:
        if P.SDR_TYPE=='sdrplay':
            stage="IFGR"
        elif P.SDR_TYPE=='rtlsdr':
            stage="TUNER"
        else:
            print("Error - unknown SDR type - aborting")
            sys.exit(0)
            
        print("Get Gain            =",sdr.getGain(SOAPY_SDR_RX, 0,stage))
        sdr.setGain(SOAPY_SDR_RX, 0,stage,P.IFGAIN)
        print("Get Gain            =",sdr.getGain(SOAPY_SDR_RX, 0,stage))


    # Select antenna
    if P.ANTENNA=='A':
        ant1 = 'Antenna A'
    elif P.ANTENNA=='B':
        ant1 = 'Antenna B'
    elif P.ANTENNA=='Z':
        ant1='Hi-Z'
    else:
        print("\n$$$$$$$$$$$$$$$$ ERROR - Unrecongized Antenna $$$$$$$$$$$$$$$",P.ANTENNA)
        print("SDR should revert to default (Antenna A)\n")
    sdr.setAntenna(SOAPY_SDR_RX, 0,ant1)

    # Do some error checking
    bw   = sdr.getBandwidth(SOAPY_SDR_RX, 0)

    if bw>0. and abs( P.FOFFSET ) > bw/2:
        print("\n*** ERROR in setupSDR: requested RF offset outside tuner bandwidth")
        print("Offset =",P.FOFFSET*1e-3, \
                        " KHz            Max = Half Bandwidth =",bw*0.5e-3, \
                        " KHz\n")
        sys.exit(1)

    if P.IF!=0 and P.SRATE>1e6:
        print('\n************************************************************************************')
        print('************ WARNING - Should use Zero-IF for high sampling rate *******************')
        print('************************************************************************************\n')

    if P.SDR_TYPE=='rtlsdr':
        P.sdr.writeSetting("direct_samp",str(P.DIRECT_SAMP))
        
############################################################################

# Routine to read & print current SDR settings
def check_sdr_settings(P):

    print("\n------------- Current SDR Settings -------------")
    if P.REPLAY_MODE:
        return

    sdr  = P.sdr;
    print('\nDriver Key:   ',sdr.getDriverKey())
    print('Hardware Key: ',sdr.getHardwareKey())
    print('Hardware Info:',sdr.getHardwareInfo())
        
    ant  = sdr.getAntenna(SOAPY_SDR_RX, 0)
    fs   = sdr.getSampleRate(SOAPY_SDR_RX, 0)
    #decM = sdr.getDecim(SOAPY_SDR_RX, 0)
    fc   = sdr.getFrequency(SOAPY_SDR_RX, 0,'RF')
    ppm  = sdr.getFrequency(SOAPY_SDR_RX, 0,'CORR')
    bw   = sdr.getBandwidth(SOAPY_SDR_RX, 0)
    if P.SDR_TYPE=='sdrplay':
        gain = sdr.getGain(SOAPY_SDR_RX, 0,"IFGR")
        decM = sdr.getGain(SOAPY_SDR_RX, 0,"DECIM")
        decEnable = sdr.getGain(SOAPY_SDR_RX, 0,"DECenable")
        srate = sdr.getGain(SOAPY_SDR_RX, 0,"SRATE")
        srate_req = sdr.getGain(SOAPY_SDR_RX, 0,"reqSRATE")
    else:
        gain = sdr.getGain(SOAPY_SDR_RX, 0,"TUNER")
        decM = 1
        decEnable = 0
        srate = fs
        srate_req = fs

    print("Antenna     =",ant) 
    print("Sample rate =",fs,' Hz =',fs*1e-3,' KHz =',fs*1e-6,' MHz')
    print("Center freq =",fc,' Hz =',fc*1e-3,' KHz =',fc*1e-6,' MHz')
    print("PPM         =",ppm)
    print("Bandwidth   =",bw,' Hz =',bw*1e-3,' KHz =',bw*1e-6,' MHz')
    print("Gain        =",gain)

    print("Decim       =",decM,decEnable)
    print("srate       =",srate,srate_req)
    
    if P.SDR_TYPE=='rtlsdr':
        #setenv SOAPY_SDR_LOG_LEVEL 9
        
        print('\nDriver Key:   ',sdr.getDriverKey())
        print('Hardware Key: ',sdr.getHardwareKey())
        print('Hardware Info:',sdr.getHardwareInfo())
        print('Num channels: ',sdr.getNumChannels(SOAPY_SDR_RX))
        print('List Gains:   ',sdr.listGains(SOAPY_SDR_RX, 0))
        print('Gain Range:   ',sdr.getGainRange(SOAPY_SDR_RX, 0))
        T=sdr.hasGainMode(SOAPY_SDR_RX, 0)
        print('Has Gain Mode:',T)
        sdr.setGainMode(SOAPY_SDR_RX, 0,True)
        print('Gain Mode:    ',sdr.getGainMode(SOAPY_SDR_RX, 0))
        print('List BWs:     ',sdr.listBandwidths(SOAPY_SDR_RX, 0))
        print(' ')
    
    info=sdr.getSettingInfo()
    idx=-1
    keys=[];
    for a in info:
        idx+=1
        keys.append(a.key);
    for s in keys:
        print("Read Setting: ",s," =",sdr.readSetting(s))
    print("\n")



# Routine to list threads
def show_threads():
    print('\nList of running threads:')
    threads = enumerate()                  # enumerate is from the threading lib
    for th in threads:
        print(th)

    print('\nList of active children:')
    threads = active_children()
    for th in threads:
        print(th)
    print(' ')

    

# Routine to return FT4 freqs on the same band as an arbitrary freq
def expand_ft4(frqs):  
    frqs2 = []
    for fc in frqs:
        #b = convert_freq2band(fc,True)
        b = freq2band(fc*1e-3)
        f = float(bands[b]['FT4'])
        #        frqs2.append(fc)
        #        frqs2.append(f)
        #    return np.array( frqs2 )
        frqs2.append(f)
    #print 'EXPAND_FT4:',frqs,frqs2,list(frqs)+frqs2
    return np.array( list(frqs)+frqs2 )
    



# Function to determine SDR type
def find_sdr_device(self,args):

    # Check to replay a data file - no SDR needed for this
    if len( args.replay )>0:
        self.REPLAY_MODE = True
        self.REPLAY      = args.replay[0]
        if len( args.replay )>1:
            self.REPLAY_START = float( args.replay[1] )
        else:
            self.REPLAY_START = 0
        self.SDR_TYPE    = 'replay'
        self.DIRECT_SAMP = 0
        return None

    Done=False
    while not Done:

        if self.USE_FAKE_RTL:
            print('Howdy Ho!')
            dev='driver=rtlsdr,rtl=0'
            dev='driver=rtlsdr,serial=00000001'
            print('dev=',dev)

            self.SDR_TYPE = 'rtlsdr'
            self.REPLAY_MODE=False
            self.DIRECT_SAMP = 2
            sdr = RTL_SDR_DRIVER(self)
            return sdr
            
            #sdr = SoapySDR.Device( dict(driver=dev) )
            #sdrkey = sdr.getDriverKey()
            #sys.exit(0)

        # Get list of devices attached to the computer
        # For some reason, the new driver sometimes fails the first time so do it twice
        for ntry in range(1,3):
            print('Looking for SDR devices ...',ntry)
            devices = SoapySDR.Device.enumerate()
            if len(devices)==0:
                time.sleep(1)
            else:
                break

        # If we use the pre-built Soapy libs, this seems to find an
        # "audio" device, at least on the RPi.
        # Sift through the list of found devices and only keep the ones
        # we can work with.
        if len(devices)>1 or False:
            print('\nFIND_SDR_DEVICE: Found',len(devices),'SDR devices ...')
            print('devices=',devices)
            print( type( devices ) )
            valid_devices=[]
            for dev in devices:
                print('\ndev=',dev)
                print('driver=',dev['driver'])
                if dev['driver'] in ['rtlsdr','sdrplay']:
                    print('*** Recognized SDR Device ***')
                    valid_devices.append(dev)
                #print( type( dev['driver'] ) )
            print('valid_devices=',valid_devices)
            devices=valid_devices
            #sys.exit(0)

        # For now, we only can handle one device
        if len(devices)==0:
            print('\n******************************************')
            print('***     -- No SDR Device Found  --     ***')
            print('***     Make sure it is plugged in     ***')
            print('***                                    ***')
            print('*** If problem persists, kill driver:  ***')
            print('***    ps -aux | fgrep sdrplay         ***')
            print('***    kill -9 <proc number>           ***')
            print('******************************************')

            if True:
                app  = QApplication(sys.argv)
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setText("Could not find SDR !!!\n\nMake sure it is plugged in and click OK to try again ...")
                msgBox.setWindowTitle("No SDR Found")
                #msgBox.setStandardButtons(QMessageBox.Ok)
                msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                #msgBox.buttonClicked.connect(msgButtonClick)
        
                returnValue = msgBox.exec()
                if returnValue == QMessageBox.Ok:
                    print('OK clicked')
                    #return False,None
                elif returnValue == QMessageBox.Cancel:
                    print('Cancel clicked')
                    #return True,None
                    sys.exit(0)
                    
        elif len(devices)>1:
            print('FIND_SDR_DEVICE: ERROR - Need some more code to handle multiple SDR devices')
            print('devices=',devices)
            sys.exit(0)

        else:
            
            # If we get here, we found the device - check what it is
            Done=True
            print('devices=',devices)
            dev=devices[0]['driver']
            print('dev=',dev)
            try:
                sdr = SoapySDR.Device( dict(driver=dev) )
                sdrkey = sdr.getDriverKey()
            except: 
                error_trap('UTILS->FIND SDR DEVICE',1)
                print('\n***************************************')
                print('Unable to open driver - dev=',dev)
                print('Perhaps you need to restart the driver?')
                print('***************************************')
                sys.exit(0)

            # Is it the SDRplay RSP?
            if sdrkey=='SDRplay':
                if not args.rtl and not args.rtlhf:
                    self.SDR_TYPE = 'sdrplay'          # Yeah, this is redundant
                    self.REPLAY_MODE=False
                    self.DIRECT_SAMP = 0
                else:
                    print('\n***************************************')
                    print('*** -- User Device Spec Conflict -- ***')
                    print('*** RTL asked for but SDRplay Found ***')
                    print('***************************************')
                    sys.exit(0)
                
            # Is it the RTL-SDR?
            elif sdrkey=='RTLSDR':
                self.SDR_TYPE = 'rtlsdr'
                self.REPLAY_MODE=False
                if not args.sdrplay:
                    if args.rtl and not args.rtlhf:
                        self.DIRECT_SAMP = 0
                    elif not args.rtl and args.rtlhf:
                        self.DIRECT_SAMP = 2
                    else:
                        print("********* Ambiguous mode for RTL - assuming HF ******")
                        self.DIRECT_SAMP = 2
                else:
                    print('\n***************************************')
                    print('*** -- User Device Spec Conflict -- ***')
                    print('*** RTL asked for but SDRplay Found ***')
                    print('***************************************')
                    sys.exit(0)
            
            return sdr

