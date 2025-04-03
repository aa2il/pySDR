#! /usr/bin/python -u
############################################################################
#
# mp.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Multiprocessing version of pySDR
#
# Notes:
#    - For whatever reason, we need to use -IF=0 for SRATE = 0.25 or >=2 MHz
#          Examples on how to make this work:
#
#             pySDR.py -fs 2 -IF 0 -foffset 100
#             pySDR.py -fs 4 -IF 0 -foffset 455 -sub
#
#    - -offset doesn't seem quite right
#    - need to get control of RF gain
#    - To update pyqtgraph, goto http://www.pyqtgraph.org/, download .deb file at top of page & click on it to install
#
# sudo pip install --upgrade numpy scipy pyqtgraph
#
# TO DO:
#         - Check sample source and sink at higher fs out rate (96 & 192 KHz)
#           Seems input stream is out of sink and RB size is quite large?
#         - Why isn't filtered spectrum clean if UP!=1 ?
#         - This pathway hasn't been tested/maintained in a while
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

import sig_proc as dsp
import numpy as np
from support import *
from receiver import *
from gui import *
from hopper import *
from watchdog import *
import file_io as io
from rig_io import socket_io 

from rig_io import hamlibserver as rigctl
import datetime
import threading
import multiprocessing as mp
import time
from profiler import *

VERSION='DEVELOPMENT 2.0'

################################################################################

# Create various objects
print('\n****************************************************************************')
print('\n   pySDR',VERSION,'beginning ...\n')

# Set-up run-time params
P=RUN_TIME_PARAMS()

# Select multi-processing scheme
MP_SCHEME=1                   # RX runs in separate thread --> single process
MP_SCHEME=2                   # RX runs in separate process --> mulit-process
MP_SCHEME=3                   # Each RX demod runs in separate process --> mulit-process

# Dummy up params from gui version
P.AF_FILTER_NUM  = -1
P.raw_iq_io      = None
P.baseband_iq_io = None
P.demod_io       = None
P.evt            = None
P.Stopper        = None
P.MP_SCHEME      = MP_SCHEME

# These are needed in all versions so should eventually be pushed to support.py
P.sdr            = None
P.sock           = None
P.threads        = []

# Ring buffers to throttle between data capture and playback/display
P.rb_rf       = dsp.ring_buffer3('RF',8*P.IN_CHUNK_SIZE)
P.rb_baseband = dsp.ring_buffer3('BB',8*P.IN_CHUNK_SIZE)
P.rb_af       = dsp.ring_buffer3('AF',P.RB_SIZE)
P.rf_psd_Q    = P.rb_rf.buf
P.bb_psd_Q    = P.rb_baseband.buf
P.af_psd_Q    = P.rb_af.buf

# Open writers for data we might want to save - not tested for MP!!!!
P.raw_iq_io      = io.sdr_fileio('raw_iq','w',P,2,'RAW_IQ')
P.baseband_iq_io = io.sdr_fileio('baseband_iq','w',P,2,'BASEBAND_IQ')
P.demod_io       = io.sdr_fileio('demod','w',P,1,P.MODE)

############################################################################

# Instantiate servers allowing external control of each RX
P.threads=[]
P.Stopper = threading.Event()
#print "P=",pprint(vars(P))
if P.HAMLIB_SERVERS:
    for i in range(P.NUM_RX+1):
        if i<P.NUM_RX:
            port = 4575 + i
        else:
            port = 4675 + i-P.NUM_RX
        th = threading.Thread(target=rigctl.HamlibServer(P,port).Run, args=(),name='Hamlib '+str(port))
        th.setDaemon(True)
        th.start()
        P.threads.append(th)
elif not P.REPLAY_MODE and P.HAMLIB_SERVERS:
    i=0
    port=4533
    th = threading.Thread(target=rigctl.HamlibServer(P,port).Run, args=(),name='Hamlib '+str(port))
    th.setDaemon(True)
    th.start()
    P.threads.append(th)

# Start RX stream
if P.MP_SCHEME==1:
    # This works - rx is in its own thread
    P.Stopper = threading.Event()
    #worker = threading.Thread(target=SDR_RX, args=(P,False),name='TH_SDR_RX')
    worker = threading.Thread(target=SDR_EXECUTIVE(P,False).Run,args=(), name='SDR_EXEC')
    worker.setDaemon(True)
    worker.start()
    P.threads.append(worker)
elif P.MP_SCHEME==2:
    # This works - rx is in its own process
    #P.Stopper = mp.Event()
    P.Stopper = threading.Event()
    P.parent_conn, P.child_conn = mp.Pipe()
    worker = mp.Process(target=SDR_RX, args=(P,False),name='MP_SDR_RX')
    #worker = mp.Process(target=SDR_EXECUTIVE(P,False).Run,args=(),name='MP_SDR_EXEC')
    worker.start()
    P.pipe = P.parent_conn
    P.mp_proc = worker

elif P.MP_SCHEME==3:
    # This works - each rx demod is in its own process

    # First, setup signalling between the various processes
    P.Stopper= threading.Event()
    P.parent_conn = []
    P.child_conn  = []
    P.que         = []
    P.data_ready  = []
    P.rx_ready    = []
    for irx in range(P.NUM_RX):
        parent_conn, child_conn = mp.Pipe()
        P.parent_conn.append(parent_conn)
        P.child_conn.append(child_conn)
        P.que.append( mp.Queue() )
        P.data_ready.append( mp.Event() )
        P.rx_ready.append( mp.Event() )

    # Put SDR EXECUTIVE in its own THREAD
    P.workers=[]
    worker = threading.Thread(target=SDR_EXECUTIVE(P,False).Run,args=(), name='SDR_EXEC')
    worker.setDaemon(True)
    worker.start()
    P.workers.append(worker)

    # Put each RX demod in its own PROCESS
    for irx in range(P.NUM_RX):
        worker = mp.Process(target=RX_Thread, args=(P,irx),name='RX_PROC '+str(irx))
        worker.start()
        P.workers.append(worker)
            
else:
    print('No MP_SCHEME selected')
    sys.exit(0)

# Instantiate a profiler
P.pr = Profiler(P)
    
# Open connection to rig
P.sock = socket_io.open_rig_connection(P.RIG_CONNECTION,0,P.PORT,0,'pySDR: ')
if not P.sock.active:
    print('*** No connection to rig ***')

############################################################################
        
# Put rig queries into a separate thread
# Over time, we need to move more of these things here
def RIG_Updater(P):
        
    #while 1:
    while P.Stopper and not P.Stopper.isSet():

        # Need to reconcile this also
        if False:
            # This is how it was for SO2V
            P.frqArx = P.sock.get_freq('A')*1e-3
        else:
            # This is better for DX split ops
            frx,ftx = GetInfo(P)
            if frx>0:
                P.frqArx = frx
            if ftx>0:
                P.frqAtx = ftx
            
        #print 'RIG_Updater',P.frqArx,P.frqAtx
        time.sleep(1.)

    print('Exiting RIG_Updater.')

############################################################################
    
def main():
    app = QApplication(sys.argv)
    P.app=app
    if P.HOPPER:
        P.gui    = None
        P.hopper = FreqHopper(P)
    P.logger = Logger(P)
    P.gui = pySDR_GUI(app,P) 
    P.monitor = WatchDog(P,2000)

    # Timer for PSD plotting - Calls updater every 1000/PSD_RATE millisec
    PSD_RATE=20
    msec = round( 1000./PSD_RATE )
    P.PSDtimer = QtCore.QTimer()
    P.PSDtimer.timeout.connect(P.gui.UpdatePSD)
    P.PSDtimer.start(msec)

    # Thread to communicate to radio 
    th = threading.Thread(target=RIG_Updater, args=(P,),name='Rig Updater')
    th.setDaemon(True)
    th.start()
    P.threads.append(th)
        
    # Start the RX
    P.gui.StartStopRX()

    return app.exec_()


# Event loop
if __name__ == '__main__':
    main()

############################################################################
