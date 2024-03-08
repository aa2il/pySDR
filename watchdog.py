############################################################################
#
# watchdog.py - Rev 1.0
# Copyright (C) 2021-4 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Watchdog monitor for pySDR
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

from pyqtgraph.Qt import QtCore
import time
import numpy as np
import sys
from rig_io import find_fldigi_port
from Tables import BANDS
from utilities import freq2band, error_trap
from udp import *
import threading

############################################################################

BANDMAP_UPDATE_INTERVAL=30

############################################################################

# Logger
class Logger:
    def __init__(self,P):

        if True:
            P.LOG1 = open('/tmp/LOG1.TXT','w')
            P.LOG2 = open('/tmp/LOG2.TXT','w')
            P.LOG2.write('%d,%d,0,0\n' % (P.RB_SIZE,P.FS_OUT) )
        else:
            P.LOG1 = None
            P.LOG2 = None
            
        self.P = P

        
# Watch Dog Timer - Called every 2-sec to monitor health of app
class WatchDog:
    def __init__(self,P,msec):
        print('Watch Dog Starting ....')

        self.count=0
        self.P = P
        self.quiet=False
        self.in_and_out=0

        # Record start-time
        self.Start_Time = time.time()
        self.Last_Time  = self.Start_Time

        # Ring buffer diagnostics
        self.nin_prev=0
        self.nout_prev=0
        self.avg_latency = [0]*P.MAX_RX
        self.zz = np.zeros(P.OUT_CHUNK_SIZE, np.complex64)

        # UDP stuff
        self.P.udp_client  = None
        self.P.udp_ntries  = 0
        self.P.udp_client2 = None
        self.P.udp_ntries2 = 0

    # Function to monitor udp connections
    def check_udp_clients(self):

        if self.P.UDP_CLIENT != None:

            # Client to keyer
            if not self.P.udp_client:
                self.P.udp_ntries+=1
                if self.P.udp_ntries<=1000:
                    self.P.udp_client=open_udp_client(self.P,KEYER_UDP_PORT,
                                                      udp_msg_handler)
                    if self.P.udp_client:
                        print('WATCHDOG->CHECK UDP CLIENTS: Opened connection to KEYER.')
                        self.P.udp_ntries=0
                else:
                    print('Unable to open UDP client - too many attempts',self.P.udp_ntries)

            # Client to bandmap
            if self.P.BANDMAP and not self.P.udp_client2:
                self.P.udp_ntries2+=1
                if self.P.udp_ntries2<=1000:
                    self.P.udp_client2=open_udp_client(self.P,BANDMAP_UDP_PORT,
                                                       udp_msg_handler,BUFFER_SIZE=32*1024)
                    if self.P.udp_client2:
                        print('WATCHDOG->CHECK UDP CLIENTS: Opened connection to BANDMAP.')
                        self.P.udp_ntries2=0
                        self.Last_BM_Check=time.time() - BANDMAP_UPDATE_INTERVAL+2     # Force first update in 2-seconds
                else:
                    print('Unable to open 2nd UDP client - too many attempts',self.P.udp_ntries2)

        # Query spot data to populate bandmap
        if self.P.BANDMAP and self.P.udp_client2:
            t = time.time()
            dt = t - self.Last_BM_Check
            band=self.P.BAND
            #print('WATCHDOG->CHECK_UDP_CLIENTS: t=',t,self.Last_BM_Check,
            #dt,'\tband=',band)
            if dt>BANDMAP_UPDATE_INTERVAL:
                msg='SpotList:'+band+':?\n'
                self.P.udp_client2.Send(msg)
                self.Last_BM_Check=t
                print('WATCHDOG->CHECK_UDP_CLIENTS: Spot List Query sent ..,',msg)
                
        
    # Function to monitor audio ring buffers
    def check_ringbuff(self,t,irx,verbosity):

        P = self.P
        if P.MP_SCHEME==2 or P.MP_SCHEME==3:
            msg        = P.gui.mp_comm('rbStatus',irx,rx=irx)
            tag        = msg[0]
            nsamps     = msg[1]
            size       = msg[2]
            Start_Time = msg[3]
            fs         = msg[4]
        elif P.MP_SCHEME==1:
            player     = P.players[irx]
            if player and player.active:
                tag        = player.rb.tag
                nsamps     = player.rb.nsamps 
                size       = player.rb.size
                Start_Time = player.Start_Time
                fs         = player.fs
            else:
                return
        else:
            print('WATCHDOG - Unknown MP SCHEME',P.MP_SCHEME)
            sys.exit(0)

        latency = float( nsamps ) / float(P.FS_OUT)
        if self.count==1:
            self.avg_latency[irx] = latency
        else:
            if self.count<100:
                alpha = 1./float( self.count )
            else:
                alpha=.01
            self.avg_latency[irx] = (1.-alpha)*self.avg_latency[irx] + alpha*latency

        if not self.quiet:
            #print('Watch Dog:',tag,'Latency =',nsamps,'samps =',latency,' sec')
            print('Watch Dog: %s Latency = %5d samp = %4.2f sec\t%d' % \
                  (tag,nsamps,latency,size),end='',flush=True)
        if self.P.LOG2:
            self.P.LOG2.write('%f,%d,%f,%f\n' % (t,nsamps,latency,self.avg_latency[irx]) )
            self.P.LOG2.flush()

        dt = t - Start_Time
        fs_diff = int( float( nsamps - size/2 ) / dt )
        pct = float(100*nsamps)/float(size)
        if verbosity>=0:
            print('   Ring Buffer: ',pct," %   dfs=",fs_diff,"   fs_out=",fs)

        if dt>2 and nsamps > 3*size/4:
            print(' *** High Water Mark ***')
            player.rb.pull(int(nsamps - size/2))                 # Try to stay in the middles of the buffer
            if self.P.LOG1:
                self.P.LOG1.write("t=%f - %s Ring Buffer High Water Mark Hit - nsamps = %d / %d\n" % \
                                  (t,tag, nsamps, size) )

        elif dt>2 and nsamps < size/4:
            print(' *** Low Water Mark ***')
            player.rb.push_zeros(int(size/2 - nsamps))            # Try to stay in the middles of the buffer
            if self.P.LOG1:
                self.P.LOG1.write("t=%f - %s Ring Buffer Low Water Mark Hit - nsamps = %d / %d\n" % \
                                  (t,tag, nsamps, size) )
                self.P.LOG1.flush()

        else:
            print(' ...')

        # Check on plotting ring buffs
        if False:
            if self.P.SHOW_RF_PSD:
                nsamps = self.P.rb_rf.nsamps
                tag    = self.P.rb_rf.tag
                size   = self.P.rb_rf.size
                print('Watch Dog:',tag,'nsamps =',nsamps,size)
            
            if self.P.SHOW_BASEBAND_PSD:
                nsamps = self.P.rb_baseband.nsamps
                tag    = self.P.rb_baseband.tag
                size   = self.P.rb_baseband.size
                print('Watch Dog:',tag,'nsamps =',nsamps,size)

            if self.P.SHOW_AF_PSD:
                nsamps = self.P.rb_af.nsamps
                tag    = self.P.rb_af.tag
                size   = self.P.rb_af.size
                print('Watch Dog:',tag,'nsamps =',nsamps,size)


    def ItsAlive(self):
        if self.in_and_out==0:
            #print('Its Alive!',self.in_and_out)
            pass
        else:
            print('It appears to be dead!',self.in_and_out)
            self.in_and_out+=1

            if self.in_and_out>10 and False:
                P=self.P
                P.SHUT_DOWN = True
                P.Stopper.set()
                #P.gui.closeEvent()
            
            self.P.Timer2 = threading.Timer(2.0, self.ItsAlive)
            self.P.Timer2.daemon=True
            self.P.Timer2.start()
        
            
    # Check health of app in here
    def Monitor(self):
        P=self.P
        self.in_and_out+=1
        #print('Monitor: in...',self.in_and_out)

        #QTimer.singleShot(250, self.alive)
        #self.timer2.start(self.msec2)
        P.Timer2 = threading.Timer(2.0, self.ItsAlive)
        P.Timer2.daemon=True
        P.Timer2.start()
        
        #vfo=P.sock.get_vfo()
        #print('WATCHDOG->MONITOR: vfo=',vfo)
        
        t=time.time()
        if not self.quiet and False:
            print('Watch Dog: FC,FOFFSET=',P.FC,P.FOFFSET)

        if P.SHUT_DOWN:
            #quit_rx(self.P)
            #print "\nThat's all Folks!"
            #P.gui.QuitApp()
            print('WatchDog Monitor: Shutting down...')
            #P.gui.closeEvent()
            sys.exit(0)

        verbosity = -1
        if verbosity>=0:
            print('\nWatch Dog:',int( t-self.Start_Time ))
        self.count+=1

        # Monitor audio ring buffer i/o
        for i in range(P.NUM_PLAYERS):
            self.check_ringbuff(t,i,verbosity)
            #time.sleep(0.1)
        
        # Monitor AGC
        if verbosity>=0:
            agc=P.rx[0].agc
            slider  = P.AF_GAIN
            af_gain = pow(10.,P.AF_GAIN)-1 
            print('   AGC=',agc.agc,'\tGAIN=',agc.gain,'\tMAX=',agc.maxbuf,'\tREF=',agc.ref,'\tERR=',agc.err, \
                  '\tSLIDER=',slider,'\tAF_GAIN=',af_gain,'\tGAIN*MAX=',af_gain*agc.maxbuf*agc.gain)

        # Check rig mode
        if P.sock and P.sock.fldigi_active and P.gui.follow_freq_cb.isChecked():
            mode = P.sock.get_fldigi_mode()
            rig_mode = P.sock.get_mode()
            #print 'mode=',mode,rig_mode,P.MODE
            if mode=='CW' and rig_mode!='CW':
                print('WATCHDOG: Setting rig to match FLDIGI decoder',mode,rig_mode,P.MODE,'...')
                P.sock.set_mode(mode)
            elif mode=='RTTY' and rig_mode!='PKT-U':
                print('WATCHDOG: Setting rig to match FLDIGI decoder',mode,rig_mode,P.MODE,'...')
                P.sock.set_mode(mode)

        # Check UDP client
        if P.UDP_CLIENT:
            self.check_udp_clients()

        if False:
            P.NEW_SPOT_LIST=['HeLlO',1,'white']

        # Check rig band
        if P.sock and P.FOLLOW_BAND and P.sock.active:
            freq = P.sock.get_freq()*1e-3
            mode = P.sock.get_mode()
            band = freq2band(freq*1e-3)
            #print BANDS
            #print "Rig    :\tFreq =",freq,"\tBand =",band,"\tMode =",mode
            bands2=[]
            for i in range(P.NUM_RX):
                fc=P.FC[i]*1e-3
                #bands2.append( convert_freq2band(fc,True) )
                bands2.append( freq2band(fc*1e-3) )
                idx = BANDS.index(bands2[i])
                print('RX',i,':\tFreq =',fc,"\tBand =",bands2[i],"\tMode =",P.MODE,'\tidx=',idx)

            if P.NUM_RX==3 and band != bands2[1]:
                idx = BANDS.index(band)
                print(BANDS)
                print(band,bands2,idx)
                idx1=idx-1
                if BANDS[idx1]=='60m':
                    idx1-=1
                idx2=idx+1
                if BANDS[idx2]=='60m':
                    idx2+=1
                frq1=bands[BANDS[idx1]]['FT8']*1e3
                frq2=bands[BANDS[idx ]]['FT8']*1e3
                frq3=bands[BANDS[idx2]]['FT8']*1e3
                frq4=0
                #print idx,frq1,frq2,frq3,frq4
                if mode=='RTTY':
                    mode='USB'
                    P.NEW_MODE=mode
                    P.MODE_CHANGE=True

                P.NEW_FREQ=[frq1,frq2,frq3,frq4]
                fc=[frq1,frq2,frq3]
                fo = 0.5*( max(fc)+min(fc) )
                P.FOFFSET = fo-max(fc)
                P.FREQ_CHANGE=True
                print('New FOFFSET=',P.FOFFSET)
                #P.gui.FreqSelect(frq1,False,frq2,frq3,frq4)

        # Sync serial counters
        if len(P.XLMRPC_LIST)>1:
            try:
                self.sync_counters()
            except: 
                error_trap('WATCH DOG: Unable to sync counters')

        # That's a wrap for this time around ...
        self.Last_Time  = t
        self.in_and_out = 0
        #self.timer2.stop()
        #print('Monitor: ...out')

        self.P.Timer = threading.Timer(2.0, self.Monitor)
        self.P.Timer.daemon=True
        self.P.Timer.start()
        
                
    # Routine to sync serial counters over multiple instances of FLDIGI
    def sync_counters(self):
        P=self.P
        
        # Try to open xlmrpc ports if they aren't yet
        # If they are, make sure serial counters stay in sync
        #print('WatchDog: XLMRPC_LIST=',P.XLMRPC_LIST)
        max_cntr=0
        for i in range(len(P.XLMRPC_LIST)):
            port = P.XLMRPC_LIST[i]
            if P.XLMRPC_SOCKS[i]:
                
                print('WatchDog: xlmrpc port',port,' is open ...')
                cntr=P.XLMRPC_SOCKS[i].get_counter()
                P.XLMRPC_CNTRS[i]=cntr
                if cntr>max_cntr:
                    max_cntr=cntr
                print('WatchDog: cntr=',cntr,'\tmax=',max_cntr)
                
            else:
                
                print('WatchDog: Attempting to open xlmrpc port',port,' ...')
                P.XLMRPC_SOCKS[i] = find_fldigi_port(0,port,port,'A: ',False)
                if P.XLMRPC_SOCKS[i]:
                    print('Got it!!!')
                    #if i==0:
                    #    P.gui.rig.sock1=P.XLMRPC_SOCKS[i]

        for i in range(len(P.XLMRPC_LIST)):
            if P.XLMRPC_SOCKS[i]:
                port = P.XLMRPC_LIST[i]
                if P.XLMRPC_CNTRS[i]<max_cntr:
                    print('WatchDog: Updating counter on port',port,'to',max_cntr)
                    P.XLMRPC_SOCKS[i].set_counter(max_cntr)
                
                    

