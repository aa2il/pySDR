############################################################################
#
# receiver.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Top level receiver routines
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

import SoapySDR
from SoapySDR import *                # SOAPY_SDR_ constants
import sys
import numpy as np
import time
from sig_proc import up_dn
from Tables import MODES,VIDEO_BWs,AF_BWs
import file_io
from pprint import pprint
from utils import setupSDR,check_sdr_settings
from utilities import error_trap
import sig_proc as dsp
from scipy.io import savemat
from Tables import AF_BWs
import multiprocessing as mp
import ctypes

############################################################################

SAMPLE_FORMAT=SOAPY_SDR_CF32
#SAMPLE_FORMAT=SOAPY_SDR_CS16

def RX_Thread(P,irx):
    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ RX Thread @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',irx)
    P.pipe = P.child_conn[irx]
    
    # Create main and sub receivers
    foff = P.FOFFSET

    if P.SOURCE[irx]>=0:
        frq = P.FC[irx]-P.FC[P.SOURCE[irx]]
    else:
        frq = foff+P.FC[irx]-P.FC[0]            
    P.rx[irx] = dsp.Receiver(P,frq,irx,str(irx+1),VIDEO_BWs,AF_BWs)

    # For now, assign an audio player to each rx
    if P.LOOPBACK:
        device = irx+1
    else:
        device = None
    rb = dsp.ring_buffer2('Audio'+str(irx+1),P.RB_SIZE)
    player = dsp.AudioIO(P,P.FS_OUT+P.FS_OUT_CORR,rb,device,'B')

    # Process raw data from main
    print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ RX Thread ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^',irx)
    while not P.Stopper.isSet():
        try:
            P.data_ready[irx].wait()
        except (KeyboardInterrupt, SystemExit):
            break
            
        #msg = P.pipe.recv()
        msg = P.que[irx].get()
        if msg[0]=='DAT':
            P.nchunks=msg[1]
            x=msg[2]
            
            demodulate_data(P,x,irx)

            af_gain = pow(10.,P.AF_GAIN)-1
            player.rb.push( P.rx[irx].am * af_gain )
            if player and not player.active:
                player.start_playback(P.RB_SIZE/2,False)
            
            # Handshake with main
            P.data_ready[irx].clear()
            P.rx_ready[irx].set()

        if P.pipe.poll():
            msg = P.pipe.recv()
            #if msg[0]=='CMD':
            print('<<< RX_Thread: Got:',irx,msg)
            
            if msg[1]=='Shutdown':
                P.pipe.send(('MSG',0))
                P.rx_ready[irx].set()
                time.sleep(1)
                break
            elif msg[1]=='setFrequency':
                P.rx[irx].lo.change_freq( msg[2] )
                P.pipe.send(('MSG',0))
            elif msg[1]=='setMode':
                P.MODE = msg[2]
                P.pipe.send(('MSG',0))
            elif msg[1]=='rbStatus':
                tag        = player.rb.tag
                nsamps     = player.rb.nsamps 
                size       = player.rb.size
                Start_Time = player.Start_Time
                fs         = player.fs
                P.pipe.send(('MSG',(tag,nsamps,size,Start_Time,fs) ))
                print('<<< RX_Thread: Sent:',('MSG',(tag,nsamps,size,Start_Time,fs) ))
            elif msg[1]=='setVideoFilter':
                idx=msg[2]
                P.rx[irx].dec.h = P.rx[irx].dec.filter_bank[idx]
                P.pipe.send(('MSG',0))
            elif msg[1]=='setAudioFilter':
                P.AF_BW = msg[2]
                P.AF_FILTER_NUM = msg[3]
                P.pipe.send(('MSG',0))
            elif msg[1]=='showAFpsd':
                P.SHOW_AF_PSD=msg[2]
                P.pipe.send(('MSG',0))
            elif msg[1]=='showBBpsd':
                P.SHOW_BASEBAND_PSD=msg[2]
                P.pipe.send(('MSG',0))
            elif msg[1]=='setPlotRX':
                P.PLOT_RX = msg[2]
                P.pipe.send(('MSG',0))
            else:
                print('\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ COMM ERROR on RX @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',irx)
                print('Unknown command',msg)

            
    # When we get here, we've been told to bug out
    print('@@@ RX',irx,' exiting @@@')
    
############################################################################

# Function to send demod audio to output buffers
def audio_out(P,am=None):

    #print 'AUDIO_OUT:',P.AUDIO_SCHEME

    # In this scheme, two mono RX's are routed to one audio player
    if P.AUDIO_SCHEME==2:

        iplay=0
        N2=int( (P.NUM_RX+1)/2 )
        for irx in range(N2):
            #print "Audio routing: rx=",irx,irx+N2,"\tplayer=",iplay
            player=P.players[iplay]
            iplay+=1

            am1=P.rx[irx].am.real
            if P.MUTED[irx]:
                af_gain1 = 0.
            else:
                af_gain1 = pow(10.,P.AF_GAIN)-1          # Make the slider a dB scale

            if irx+N2<P.NUM_RX: 
                am2=P.rx[irx+N2].am.real
                if P.MUTED[irx+N2]:
                    af_gain2 = 0.
                else:
                    af_gain2 = pow(10.,P.AF_GAIN)-1          # Make the slider a dB scale
            else:
                af_gain2 = 0.
                am2=0
            
            # Need to delay start of playback until there are enough samples
            player.rb.push( am1*af_gain1 + 1j*am2*af_gain2 )
            if player and not player.active:
                player.start_playback(P.DELAY,False)

        return
            
    # Default scheme - each RX has its own player
    for irx in range(P.NUM_RX):
        rx=P.rx[irx]
        am=P.rx[irx].am
        player=P.players[irx]

        if P.MUTED[irx] or P.AUTO_MUTED:
            af_gain = 0.
        else:
            af_gain = pow(10.,P.AF_GAIN)-1          # Make the slider a dB scale

        #print 'AUDIO_OUT:',irx,af_gain,am
            
        if P.LOOPBACK:
            if P.AUX_USE_BPF and False:
                am2 = P.aux_bpf.convolve_fast( am )
                player.rb.push( am2 )
            else:
                player.rb.push( am )
        else:
            player.rb.push( am * af_gain )

        if irx==0 and P.LOOPBACK and P.AUX_AUDIO:
            if P.AUX_USE_BPF:
                am2 = P.aux_bpf.convolve_fast( am )
                P.aux_rb.push( am2*af_gain )
            else:
                P.aux_rb.push( am * af_gain )
            if not P.aux_player.active:
                P.aux_player.active = P.aux_player.start_playback(P.RB_SIZE/2,False)

        # Need to delay start of playback until there are enough samples
        if player and not player.active:
            player.start_playback(P.DELAY,False)




# Function to perform demodulation and push into output buffer
def demodulate_data(P,x,irx):

    #print 'DEMODULATE_DATA:',len(x),irx
    rx=P.rx[irx]
    am = rx.demod_data(x)

    # Automajic muting of big sigs - helps with SO2V
    if P.ENABLE_AUTO_MUTE:
        mute = rx.auto_mute(x)
        if mute and not P.AUTO_MUTED:
            P.AUTO_MUTED=True
            P.gui.btn9.setColor('red')
        elif not mute and P.AUTO_MUTED:
            P.AUTO_MUTED=False
            P.gui.btn9.setColor('lime')
        
    #if rx.sub>0:
    #    am2 = rx.demod_data(x)

    if P.MODE=='AM' or P.MODE=='USB':
        # DC Removal
        am = am - np.mean(am)
        #if rx.sub>0:
        #    am2 = am2 - np.mean(am2)

    # Save data for PSD routines
    if P.SHOW_AF_PSD and irx==P.PLOT_RX:
        if P.PANADAPTOR:
            # This allows us to see the wider specturm if we are using the SDR as a pan-adpater
            P.rb_af.push(rx.iq)
        else:
            if P.MP_SCHEME==1: 
                P.rb_af.push(am)
            elif P.MP_SCHEME==2 or P.MP_SCHEME==3:
                P.af_psd_Q.put(am)
            else:
                print('DEMODULATE_DATA - Unknown MP SCHEME',P.MP_SCHEME)
                sys.exit(0)
            #print 'RECEIVER: AF Pushed '

    if P.SHOW_BASEBAND_PSD and irx==P.PLOT_RX:
        if P.MP_SCHEME==1: 
            P.rb_baseband.push(rx.iq)
        elif P.MP_SCHEME==2 or P.MP_SCHEME==3:
            P.bb_psd_Q.put(rx.iq)
        else:
            print('DEMODULATE_DATA - Unknown MP SCHEME',P.MP_SCHEME)
            sys.exit(0)
        #print 'RECEIVER: BB Pushed ',P.bb_psd_Q.qsize()

    if P.ENABLE_RTTY:
        if P.gui.rtty.active:
            #P.gui.rtty.rb.push(rx.iq)
            #print 'Pushing...',P.gui.rtty.rb.nsamps
            P.gui.rtty.q_in.put(('IQ',rx.iq))

    # Save data to disk
    if P.SAVE_BASEBAND and irx==0:
        #print len(rx.iq), len(am)
        P.baseband_iq_io.save_data(rx.iq)
    if P.SAVE_DEMOD and irx==0:
        P.demod_io.save_data(am)

############################################################################

def service_commands(P,block=False,txt=''):

    if not block and not P.pipe.poll():
        return

    if len(txt)>0:
        print('Service Commands:',txt)
    msg = P.pipe.recv()
    print('Service Commands: msg=',msg)
    if msg[1]=='Shutdown':
        print('SDR_RX: Setting stopper ...')
        #P.Stopper.set()
        P.RX_DONE=True
        P.pipe.send(('MSG',0))
    elif msg[1]=='CheckSdrSettings':
        check_sdr_settings(P)
        P.pipe.send(('MSG',0))
    elif msg[1]=='GUIready':
        P.pipe.send(('MSG',0))
        P.GUIready=True
    elif msg[1]=='listSampleRates':
        Rates = P.sdr.listSampleRates(SOAPY_SDR_RX, 0)
        P.pipe.send(('MSG',Rates))
    elif msg[1]=='listBandwidths':
        BWs = P.sdr.listBandwidths(SOAPY_SDR_RX, 0)
        P.pipe.send(('MSG',BWs))
    elif msg[1]=='getGainRange':
        r = P.sdr.getGainRange(SOAPY_SDR_RX, 0,msg[2])
        print("r=",r,type(r),r.minimum(),r.maximum(),r.step())
        rr = [r.minimum(),r.maximum(),r.step()]
        P.pipe.send(('MSG',rr))
    elif msg[1]=='getGain':
        gain = P.sdr.getGain(SOAPY_SDR_RX, 0,msg[2])
        P.pipe.send(('MSG',gain))
    elif msg[1]=='setGain':
        P.sdr.setGain(SOAPY_SDR_RX, 0,msg[2],msg[3])
        P.pipe.send(('MSG',0))
    elif msg[1]=='getAntenna':
        ant1 = P.sdr.getAntenna(SOAPY_SDR_RX, 0)
        P.pipe.send(('MSG',ant1))
    elif msg[1]=='setAntenna':
        P.sdr.setAntenna(SOAPY_SDR_RX, 0,msg[2])
        P.pipe.send(('MSG',0))
    elif msg[1]=='getBandwidth':
        bw = P.sdr.getBandwidth(SOAPY_SDR_RX, 0)
        P.pipe.send(('MSG',bw))
    elif msg[1]=='getFrequency':
        frq = P.sdr.getFrequency(SOAPY_SDR_RX, 0)
        P.pipe.send(('MSG',frq))
    elif msg[1]=='setFrequency':
        irx = msg[2]
        P.rx[irx].lo.change_freq( msg[3] )
        if irx==0:
            P.sdr.setFrequency(SOAPY_SDR_RX, 0,msg[4])
        P.pipe.send(('MSG',0))
    elif msg[1]=='setMode':
        P.NEW_MODE = msg[2]
        P.MODE_CHANGE = (P.MODE != msg[2])
        P.pipe.send(('MSG',0))
    elif msg[1]=='readSetting':
        gain = P.sdr.readSetting(msg[2])
        P.pipe.send(('MSG',gain))
    elif msg[1]=='writeSetting':
        P.sdr.writeSetting(msg[2],msg[3])
        P.pipe.send(('MSG',0))
    elif msg[1]=='Hello from Main':
        n=P.players[0].rb.nsamps
        P.pipe.send(('MSG','Hello again from SDR_RX - nsamps='+str(n)+' fc='+str(P.FC)+' Mode='+P.MODE ))
    elif msg[1]=='setVideoFilter':
        idx=msg[2]
        P.rx[0].dec.h = P.rx[0].dec.filter_bank[idx]
        P.pipe.send(('MSG',0))
    elif msg[1]=='setAudioFilter':
        P.AF_BW = msg[2]
        P.AF_FILTER_NUM = msg[3]
        P.pipe.send(('MSG',0))
    elif msg[1]=='rbStatus':
        irx        = msg[2]
        tag        = P.players[irx].rb.tag
        nsamps     = P.players[irx].rb.nsamps 
        size       = P.players[irx].rb.size
        Start_Time = P.players[irx].Start_Time
        fs         = P.players[irx].fs
        P.pipe.send(('MSG',(tag,nsamps,size,Start_Time,fs) ))
    elif msg[1]=='showAFpsd':
        P.SHOW_AF_PSD=msg[2]
        P.pipe.send(('MSG',0))
    elif msg[1]=='showRFpsd':
        P.SHOW_RF_PSD=msg[2]
        P.pipe.send(('MSG',0))
    elif msg[1]=='showBBpsd':
        P.SHOW_BASEBAND_PSD=msg[2]
        P.pipe.send(('MSG',0))
    elif msg[1]=='setPlotRX':
        P.PLOT_RX = msg[2]
        P.pipe.send(('MSG',0))
    else:
        print('Service_commands: Unknown command - ignored for now')
        print('msg=',msg)

############################################################################
        
def SDR_RX(P,GUI=False):
    sdr_exec = SDR_EXECUTIVE(P,GUI)
    sdr_exec.Run()
    
    
class SDR_EXECUTIVE:
    def __init__(self,P,GUI=False):
        print("++++++++++++++++++++++++++++++++++++++++ Starting SDR_RX - GUI=",GUI)
        print(pprint(vars(P)))

        # Init
        P.SDR_EXEC=self
        self.P = P
        P.RX_DONE  = False
        P.nchunks=0
        self.DEBUG=False

        # Object creation needs to be in same thread if using multiprocessing
        # so create SDR device instance & apply SDR settings
        self.create_SDR()
        if P.MP_SCHEME==1 or P.MP_SCHEME==2:
            self.create_Receivers()
            self.create_Audio_Players()
        elif P.MP_SCHEME==3:
            P.pipe =[]
            for irx in range(P.NUM_RX):
                P.pipe.append( P.parent_conn[irx] )
        
        if not GUI:
            self.start_rx()
        
        # Buffers for complex rx samples
        # These are set up so we grab enough RFsamples to produce 1024 audio output samples
        self.xold=[]
        if SAMPLE_FORMAT==SOAPY_SDR_CF32:
            self.xx = np.array([0]*P.IN_CHUNK_SIZE, np.complex64)
        else:
            self.xx = np.array([0]*P.IN_CHUNK_SIZE*2, np.int16)
        if P.MP_SCHEME==399:
            self.x = RAW_DATA
        else:
            #self.x = np.zeros(P.IN_CHUNK_SIZE, np.complex64)
            self.x = np.array([0]*P.IN_CHUNK_SIZE, np.complex64)

    def start_rx(self):
        print('START_RX:')
        if self.P.evt:
            self.P.evt.set()
        #for i in range(P.NUM_PLAYERS):
        #    P.players[i].resume()

    def stop_rx(self):
        print('STOP_RX:')
        if P.evt:
            P.evt.clear()
        for i in range(P.NUM_PLAYERS):
            P.players[i].pause()

    def quit_rx(self):
        P=self.P
        print('QUIT_RX:')
        if P.evt:
            P.evt.clear()
        if P.Stopper:
            P.Stopper.set()
    
        # Stop audio playback before exiting
        if P.MP_SCHEME==1 or P.MP_SCHEME==2:
            print("\n--- Stopping Audio Player(s) ---")
            for i in range(P.NUM_PLAYERS):
                if P.players[i].active:
                    P.players[i].stop()
        elif P.MP_SCHEME==3:
            pass
        else:
            print('QUIT_RX - unknown MP SCHEME',P.MP_SCHEME)

        # Shutdown the SDR RX stream
        print("\n--- Stopping RX stream ---")
        if not P.REPLAY_MODE:
            P.sdr.deactivateStream(P.rxStream) 
            P.sdr.closeStream(P.rxStream)

        # Close down any open files
        print("\n--- Closing files ---")
        for i in range(3):
            if P.status[i]>0:
                P.fp[i].close()
                print('Closed ',P.fnames[i])

        if P.raw_iq_io:
            P.raw_iq_io.close()
        if P.baseband_iq_io:
            P.baseband_iq_io.close()
        if P.demod_io:
            P.demod_io.close()

        print('RX done.')

        
    # Routine to wait for everything to start-up
    def Startup(self):
        P=self.P
        
        # Handshake with executive
        if P.MP_SCHEME==2:
            P.GUIready=False
            print('SDR_RX: Handshake ...')
            P.pipe = P.child_conn
            P.pipe.send(('MSG','Hello from SDR_RX'))
            while not P.GUIready:
                service_commands(P,block=True,txt='Waiting for go ahead...')
                time.sleep(.1)

        # Wait for RX to start
        if P.evt:
            print('SDR_RX - Waiting for RX to start ...')
            P.evt.wait()
            print('SDR_RX - RX to started ...')

        # Connect to data source
        if P.REPLAY_MODE:
            print("\n--- Opening RX file --- ",P.REPLAY)
            self.raw = P.sdr.read_data()
            print('raw=',self.raw[0:10],' ... ',self.raw[-1],len(self.raw))
            self.praw=0
        else:
            print("\n--- Starting RX stream ---")
            P.rxStream = P.sdr.setupStream(SOAPY_SDR_RX, SAMPLE_FORMAT)
            Last_Time  = time.time()
            P.sdr.activateStream(P.rxStream)
            print("--- RX stream Started ---")

            
    # Routine to Read a chunk of RF samples
    def read_chunk(self):
        P=self.P
        
        if P.REPLAY_MODE:

            #print 'Replaying chunk starting at',self.praw,len(self.raw)
            if self.praw+P.IN_CHUNK_SIZE<len(self.raw):
                idx   = self.praw + np.arange(P.IN_CHUNK_SIZE)
                #print self.praw,P.IN_CHUNK_SIZE,self.praw+P.IN_CHUNK_SIZE,len(self.raw)
                x1    = self.raw[idx]
                self.praw += P.IN_CHUNK_SIZE
                #print 'x1=',x1

                # Shift by tuning offset
                if P.lo.fo!=0:
                    self.x = P.lo.quad_mixer(x1)
                else:
                    self.x = x1
                #print 'x=',self.x

            else:
                P.RX_DONE = True

            # Don't fill up output buffer too fast
            irx=0
            player = P.players[irx]
            if player.active and True:
                while player.rb.buf.qsize()>2:
                    pass
                
            #if P.players[1].active:
            #    while P.rx[1].rb.buf.qsize()>2:
            #        pass
            #if P.players[2].active:
            #    while P.rx[2].rb.buf.qsize()>2:
            #        pass
            #if P.players[3].active:
            #    while P.rx[3].rb.buf.qsize()>2:
            #        pass

        else:
            # Unfortunately, readStream does not block but returns whatever it has
            # Hence, we need to implement the blocking here
            if self.DEBUG:
                print('+++++++++++++++++++++++++++++++++')
            #
            # Were there any samples left over from the last go round?
            #print 'SDR RX 1c'
            nn=len(self.xold)
            if nn>0:
                self.x[0:nn] = self.xold
            n1=nn

            # Keep on reading RF samples until we fill up the buffer
            while n1<P.IN_CHUNK_SIZE and (not P.Stopper or not P.Stopper.isSet()):
                #print 'SDR RX 1c'
                try:
                    sr = P.sdr.readStream(P.rxStream, [self.xx], P.IN_CHUNK_SIZE)
                    nn = sr.ret
                    #print(self.xx[0:10],self.xx[2000:2010])
                except:
                    error_trap('RECEIVER->READ CHUNK - SDR stream error')
                    nn=0
                #print 'SDR RX 1d',nn,P.Stopper.isSet()
                if nn>0:
                    n2=min(n1+nn,P.IN_CHUNK_SIZE)
                    m = n1+nn - n2
                    if SAMPLE_FORMAT==SOAPY_SDR_CF32:
                        self.x[n1:n2]  = self.xx[0:nn-m]
                        self.xold = self.xx[nn-m:nn]
                    else:
                        sc=1./2048.
                        xxx = sc*self.xx[0::2] + 1j*sc*self.xx[1::2]
                        self.x[n1:n2] = xxx[0:nn-m]
                        self.xold = xxx[nn-m:nn]
                        
                    if self.DEBUG:
                        print('--------','nn=',nn,'n1/2=',n1,n2,'m=',m,'nn-m=',nn-m,len(self.xold))
                        print(sr)
                    n1=n2
                    #print 'nn=',nn,n1,P.IN_CHUNK_SIZE
                    #print self.xx,len(self.xx)
                    
            #print 'SDR RX 1e'
            if self.DEBUG:
                tt=time.time()
                dt2=tt-Last_Time
                Last_Time=tt
                print('SDR read:',len(x),dt,dt2,len(self.xold))

    def mode_freq_change(self):
        P=self.P
        
        #print 'SDR RX 2'
        if P.MODE_CHANGE:
            # Filter out spurious changes
            if P.NEW_MODE=='FM':
                P.NEW_MODE='NFM'
            if P.MODE!=P.NEW_MODE:
                print("@@@@@@@@@@@@@@@@@ MODE CHANGE @@@@@@@@@@@@@@@@@@@@@@")
                print('OLD:',P.MODE,'\tNEW:',P.NEW_MODE)
                P.MODE=P.NEW_MODE
                if P.MP_SCHEME==1:
                    P.gui.ModeSelect(-1)
                if P.MP_SCHEME==1 or P.MP_SCHEME==2:
                    P.rx[0].agc.reset()
                    P.rx[0].demod.am_pll.reset()
            P.MODE_CHANGE=False

        # We also add a capability to change freq at a specific time - used when under external control
        if P.FREQ_CHANGE:
            # Dont bother with tiny changes
            df = np.abs( np.array( P.NEW_FREQ ) + np.array( P.FC_OLD ))
            NEED_CHANGE=False       # Should be able to do this with any!
            for d in df:
                if d>=20:
                    NEED_CHANGE=True
            if NEED_CHANGE:
                print("@@@@@@@@@@@@@@@@@ FREQ CHANGE @@@@@@@@@@@@@@@@@@@@@@")
                print('OLD:',-P.FC_OLD,'\tNEW:',P.NEW_FREQ,'\tVFO:',P.VFO)
                frq1 = .001*np.array( P.NEW_FREQ )
                if P.MP_SCHEME==1:
                    P.gui.FreqSelect(frq1,True,P.VFO)
                print('df=',df,P.NEW_FREQ)
                P.FC_OLD = -np.array( P.NEW_FREQ )
                
            P.FREQ_CHANGE=False

        # Check if we need to change RTL direct sampling mode
        if P.SDR_TYPE=='rtlsdr':
            frq=.001*P.FC[0]
            #if frq>=29.7e3 and P.DIRECT_SAMP!=0:
            if P.gui and frq>=28.0e3 and P.DIRECT_SAMP!=0:
                P.gui.DirectSelect(0)
            elif P.gui and frq<28e3 and P.DIRECT_SAMP!=2:
                P.gui.DirectSelect(2)


            
    def Run(self):
        
        # Init
        print("\n--- Processing stream ---")
        P  = self.P
        dt = float(P.IN_CHUNK_SIZE)/P.SRATE
        t  = 0
        t2 = 0

        # Wait for RX to start
        self.Startup()
        
        # Receive samples
        while not P.RX_DONE:
            t=t+dt
            P.nchunks+=1
        
            # Hook to stall the RX
            # This doesn't quite work right so is disabled for now
            # Probably bx I'm not consistent using evt signal
            #print 'SDR RX 1a', P.Stopper.isSet()
            if not P.Stopper or not P.Stopper.isSet():
                #print 'SDR RX 1aa', P.Stopper.isSet()
                #P.evt.wait()
                pass
            else:
                P.RX_DONE=True
                break
            #print 'SDR RX 1b',P.Stopper.isSet()
            
            # Read a chunk of RF samples
            self.read_chunk()
                #print 'Chunk read ...',P.MP_SCHEME,P.NUM_RX,self.x
            
            # We need to be careful when we change modes because the ordering
            # of the sample rate reduction is different for FM
            self.mode_freq_change()
        
            # Demodulate data
            if P.MP_SCHEME==1 or P.MP_SCHEME==2:
                for irx in range(P.NUM_RX):
                    demodulate_data(P,self.x,irx)
            elif P.MP_SCHEME==3:
                #print 'TYPE:::::',self.x.dtype,self.x.shape
                for irx in range(P.NUM_RX):
                    #print '>>> SDR_RX: Putting:',irx,P.nchunks,self.x[0],len(self.x),len(self.x)*8/1024
                    #P.pipe[irx].send(('DAT',P.nchunks,self.x))
                    P.que[irx].put(('DAT',P.nchunks,self.x))
                    #print '>>> SDR_RX: Put:',irx
                    P.data_ready[irx].set()         # Tell receiver that data is ready

                # Wait for receivers to consume data
                #print '>>> SDR_RX:  data_ready set - waiting for rxs'
                for irx in range(P.NUM_RX):
                    P.rx_ready[irx].wait()
                    P.rx_ready[irx].clear()
            
            # Send audio to output buffer
            if P.MP_SCHEME==1 or P.MP_SCHEME==2:
                audio_out(P)

            # Save data for PSD routines
            #print 'SDR RX 4'
            if P.SHOW_RF_PSD:
                #print 'Pushing RF data to PSD ...',len(x)
                if P.MP_SCHEME==1: 
                    P.rb_rf.push(self.x)
                elif P.MP_SCHEME==2 or P.MP_SCHEME==3: 
                    P.rf_psd_Q.put(self.x)
                else:
                    print('SDR_RX - Unknown MP SCHEME',P.MP_SCHEME)
                    sys.exit(0)
                #print 'RECEIVER: RF Pushed ',P.rf_psd_Q.qsize()

            # Save raw data to disk
            if P.SAVE_IQ:
                #print('SDR_RX: Saving raw chunk',len(self.x))
                P.raw_iq_io.save_data(self.x,VERBOSITY=0)

            # Get ready to do it again
            P.RX_DONE = P.RX_DONE or t>=P.DURATION or (P.Stopper and P.Stopper.isSet())
            #print 'SDR RX 5',Done, P.Stopper.isSet() 

            # Check messaging to main
            if P.MP_SCHEME==2:
                service_commands(P)
            
        # When we get here, the receiver is suppose to stop
        print('SDR_RX: Shutting down ...')
        self.quit_rx()
    
        if P.REPLAY_MODE:
            P.SHUT_DOWN = True

        print("\n ----- Exiting recevier processing ----\n")
        if P.MP_SCHEME==2:
            print('SDR_RX - calling sys.exit')
            sys.exit(0)
            print('SDR_RX - called sys.exit')
            
    ############################################################################

    # Routine to connect to SDR device - might be hardware (e.g. SDRPlay) or a data file
    def create_SDR(self):
        P=self.P
        print('P.sdr=',P.sdr)

        if not P.REPLAY_MODE:
            #    print P.SDR_TYPE
            args = dict(driver=P.SDR_TYPE)
            try:
                # It should already be opened but if not, try again ...
                if not P.sdr:
                    P.sdr = SoapySDR.Device(args)
                    sys.exit(0)
            except:
                error_trap('RECEIVER->CREATE SDR')
                print('\n*****************************************************')
                print('*** Unable to instantiate SDR Device',P.SDR_TYPE,'\t  ***')
                print('***       Make sure it is plugged in              ***')
                print('*****************************************************')
                sys.exit(0)
            setupSDR(P)
        
        else:
            print("\n--- Opening RX file --- ",P.REPLAY)
            P.sdr = file_io.sdr_fileio(P.REPLAY,'r',P)
            P.SRATE     = P.sdr.srate
            P.REPLAY_FC = P.sdr.fc
            P.FC[0]     = P.sdr.fc

            if P.REPLAY.find('baseband_iq'):
                P.FS_OUT=P.SRATE

            P.UP , P.DOWN   = up_dn(P.SRATE , P.FS_OUT )
            P.FS_OUT        = int( P.SRATE * P.UP / P.DOWN   )
            P.IN_CHUNK_SIZE = int( P.OUT_CHUNK_SIZE*P.DOWN/float(P.UP) + 0*0.5 )

            P.lo = dsp.signal_generator(0*P.BFO,P.IN_CHUNK_SIZE,P.SRATE,True)

        
    # Routine to create main and sub receivers
    def create_Receivers(self):
        P=self.P

        foff = P.FOFFSET
        for irx in range(P.NUM_RX):
            if P.SOURCE[irx]>=0:
                frq = P.FC[irx]-P.FC[P.SOURCE[irx]]
            else:
                frq = foff+P.FC[irx]-P.FC[0]            
            P.rx[irx] = dsp.Receiver(P,frq,irx,str(irx+1),VIDEO_BWs,AF_BWs)

    # Routine to create audio players
    def create_Audio_Players(self):
        P=self.P

        # Audio playback 
        P.players = []
        for irx in range(P.NUM_PLAYERS):
            if P.LOOPBACK:
                device = irx+1
            else:
                device = None
            rb = dsp.ring_buffer2('Audio'+str(irx+1),P.RB_SIZE)
            print('Opening audio playback for rx',irx,' ...')
            player = dsp.AudioIO(P,P.FS_OUT+P.FS_OUT_CORR,rb,device,'B',Tag='RX '+str(irx))
            P.players.append(player)

        # Provide Audio playback on speakers also
        if P.LOOPBACK and P.AUX_AUDIO:
            print('Providing audio playback on both loopback and speakers ...')
            P.aux_rb = dsp.ring_buffer2('Audio Aux',P.RB_SIZE)
            P.aux_player = dsp.AudioIO(P,P.FS_OUT+P.FS_OUT_CORR,P.aux_rb,
                                           None,'B',Tag='LOOPBACK AUX')
            P.AUX_USE_BPF=True
            if P.AUX_USE_BPF:
                hbpf = dsp.bpf(800.,1300.,P.FS_OUT,1001)
                P.aux_bpf = dsp.convolver(hbpf,np.float32)

        # Export various internal vars for analysis in Octave
        if False:
            savemat(P.INTERNALS, mdict={'h_resamp' : P.rx[0].dec.filter_bank,        \
                                        'video_bw' : P.VIDEO_BW,                     \
                                        'up'       : P.UP,                           \
                                        'dn'       : P.DOWN,                         \
                                        'srate'    : P.SRATE,                        \
                                        'fsout'    : P.FS_OUT,                       \
                                        'AF_BWs'   : AF_BWs,                         \
                                        'h_bank_r' : P.rx[0].demod.filter_bank_real, \
                                        'h_bank_c' : P.rx[0].demod.filter_bank_cmpx  })

############################################################################
