############################################################################
#
# utils.py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
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

# Maintain compatability with python2 for now - probably can jettison this
#from __future__ import print_function

import SoapySDR
from SoapySDR import *                # SOAPY_SDR_ constants
import sys
import numpy as np
import time
from Tables import MODES,SDRplaysrates,RTLsrates
import io
from threading import enumerate
from rig_io.util import convert_freq2band
from rig_io.ft_tables import bands,CONNECTIONS,RIGS
from multiprocessing import active_children
from PyQt5.QtWidgets import QMessageBox,QSplashScreen
from PyQt5.QtGui import QIcon, QPixmap

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
        b = convert_freq2band(fc,True)
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

        # Get list of devices attached to the computer
        # For some reason, the new driver sometimes fails the first time so do it twice
        for ntry in range(1,3):
            print('Looking for SDR devices ...',ntry)
            devices = SoapySDR.Device.enumerate()
            if len(devices)==0:
                time.sleep(1)
            else:
                break
            
        if False:
            print(devices)
            print(len(devices))
            for dev in devices:
                print('dev=',dev)
                print('driver=',dev['driver'])
                #print type( dev['driver'] )
            sys.exit(0)

        # For now, we only can handle one device
        if len(devices)==0:
            print('\n**********************************')
            print('*** -- No SDR Device Found  -- ***')
            print('*** Make sure it is plugged in ***')
            print('**********************************')

            if True:
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
            sys.exit(0)

        else:
            
            # If we get here, we found the device - check what it is
            Done=True
            dev=devices[0]['driver']
            sdr = SoapySDR.Device( dict(driver=dev) )
            sdrkey = sdr.getDriverKey()

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




# Put up splash screen until we're ready
def splash_screen(app):
    
    splash = QSplashScreen(QPixmap('splash.png'))
    splash.show()
    time.sleep(.01)
    app.processEvents()

    return splash
