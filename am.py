#! /usr/bin/python3 -u
############################################################################
#
# am.py - Rev 1.0
# Copyright (C) 2017-25 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# A simple AM tuner for sdrplay using soapy lib and python
# This is a stripped down version of pySDR without all the baggage.
# May be useful for module development.  This version was used to
# begin transition to multiprocessing.
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
if True:
    import threading
    MP_SCHEME=1
elif True:
    import threading
    import multiprocessing as mp
    MP_SCHEME=3
else:
    import multiprocessing as mp
    MP_SCHEME=2
import time

from params import *
from receiver import *

############################################################################

VERSION='1.0'

############################################################################

# Create various objects
print('\n****************************************************************************')
print('\nSimple SDR v',VERSION,'beginning ...\n')

# Set-up run-time params
P=RUN_TIME_PARAMS()

# Dummy up params from gui version
P.AF_FILTER_NUM  = -1
P.raw_iq_io      = None
P.baseband_iq_io = None
P.demod_io       = None
P.evt            = None
P.Stopper        = None
P.MP_SCHEME      = MP_SCHEME
P.gui            = None
P.audio_playback = True

############################################################################

# Start RX stream
if P.MP_SCHEME==1:
    # This works - rx is in its own thread
    #worker = threading.Thread(target=SDR_RX, args=(P,False),name='TH_SDR_RX')
    worker = threading.Thread(target=SDR_EXECUTIVE(P,False).Run,args=(), name='SDR_EXEC')
    worker.daemon=True
    worker.start()
    #print('RB_SIZE1:',P.RB_SIZE)
    #P.RB_SIZE        = 4*P.OUT_CHUNK_SIZE
    #print('RB_SIZE2:',P.RB_SIZE)
    
elif P.MP_SCHEME==2:
    # This works - entire rx is in its own process
    P.parent_conn, P.child_conn = mp.Pipe()
    worker = mp.Process(target=SDR_RX, args=(P,False),name='MP_SDR_RX')
    worker.start()
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
    print('AM - Unknown MP SCHEME',P.MP_SCHEME)
    sys.exit(0)
    
    # This works but user hits contrl-C to quit - not graceful
    # Single thread only
    # SDR_RX(P,False)
    
    # This works and allows user to contrl-C out to stop gracefully
    # Single thread only
    try:
        SDR_RX(P,False)
    except (KeyboardInterrupt, SystemExit):
        print('Exception detected and being handled ...')
        P.SDR_EXEC.quit_rx()
        sys.exit(0)
        raise

############################################################################

# Playing with how to read a single char
#ch = sys.stdin.read(1)    # Requires user to press <CR>
#import getch              # This should do the trick but can't seem to install it - ugh
#ch = getch.getche()
#print 'ch=',ch

if P.MP_SCHEME==1:
    while not P.rx[0]:
        print('AM: Waiting for RX to start ...')
        time.sleep(1)
elif P.MP_SCHEME==2:
    P.pipe = P.parent_conn
    print('AM: Waiting for RX to start ...')
    msg = P.pipe.recv()
    print('msg=',msg)
    P.pipe.send(('CMD','CheckSdrSettings'))
elif P.MP_SCHEME==3:
    print('\nAM: Waiting for RX to start ...')
    while P.nchunks<2:
        time.sleep(1)
else:
    print('AM - Unknown MP SCHEME',P.MP_SCHEME)
    sys.exit(0)
    

print('Press control-C to exit ...')
Done=False
while not Done:
    try:
        time.sleep(1)
        if P.MP_SCHEME==2:
            if P.pipe.poll():
                msg = P.pipe.recv()
                print('msg=',msg)
            P.pipe.send(('MSG','Hello from Main'))
        elif P.MP_SCHEME==3:
            pass
        else:
            N=P.players[0].rb.nsamps
            DT=float(N)/float(P.FS_OUT)
            print("Ring Buffer - nsamps=",N,'\tlatency=',DT)
        
    except (KeyboardInterrupt, SystemExit):
        print('Exception detected and being handled ...')
        if P.MP_SCHEME==2:
            print('Sending shutdown to child process ...')
            P.pipe.send(('MSG','Shutdown'))
            print('Waiting for child process to end ...')
            try:
                worker.join(10)
                print('... child joined ...')
            except:
                print('JOIN timed out - sending TERM signal ...')
                worker.terminate()
        else:
            P.SDR_EXEC.quit_rx()

        print('Badaleep badaleep - Thats all folks!\n')
        Done=True
        sys.exit(0)
        #raise

