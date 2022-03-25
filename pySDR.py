#! /usr/bin/python3 -u
############################################################################
#
# pySDR.py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# A complete SDR written in Python.
#
# This is the gui version of pySDR. This is threaded version.
# Seems to work on both python 2 & 3 under linux.  Had some problems
# getting to work on RPi 400 but had to do with 1) margianal usb cable
# and 2) software conflicts w/ numpy/scipy.  The latter seems to be caused
# either using sudo for pip upgrades and/or Soapy driver.  Not sure if the
# latest version of the sdrplay api works - ended up just grabbing
# installation from AA2ILpi of old driver - should try again later with a fresh
# install but for now, this seems to work just fine!

# Notes:
#    - A non-zero IF doesn't work with the new (V13) driver so let's not use it
#      Instead, we default to -IF=0 and user a 450 Hz offset
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
# This seems to cause problems if we sudo it so don't:
# pip3 install --upgrade numpy scipy pyqtgraph
#
# TO DO:
#         - Check sample source and sink at higher fs out rate (96 & 192 KHz)
#           Seems input stream is out of sink and RB size is quite large?
#         - Why isn't filtered spectrum clean if UP!=1 ?
#         - There is already a package with this same name.  Need to think
#           of a new name.
#
################################################################################
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

# Maintain compatability with python2 for now - can probably jettision this
#from __future__ import print_function

# Suppress warnings from latest version of SciPy - not sure if we need this anymore
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

import sig_proc as dsp
import numpy as np
from params import *
from gui import *
from hopper import *
from watchdog import *
import file_io as io
import rig_io.socket_io as socket_io
import rig_io.hamlibserver as rigctl
import datetime
import threading
from profiler import *

################################################################################

import logging               

# Setup basic logging
logging.basicConfig(
    format="%(asctime)-15s [%(levelname)s] %(funcName)s:\t(message)s",
    level=logging.INFO)

################################################################################

VERSION='DEVELOPMENT 1.4'

################################################################################

# Initialization for pySDR
def init_sdr():

    # Create various objects
    print('\n****************************************************************************')
    print('\n   pySDR',VERSION,'beginning ...\n')

    # Set-up run-time params
    P=RUN_TIME_PARAMS()
    P.MP_SCHEME=1            # For now

    # Ring buffers to throttle between data capture and playback/display
    # Seems like this should use blocking???
    if P.MP_SCHEME==1: 
        P.rb_rf       = dsp.ring_buffer2('RF',8*P.IN_CHUNK_SIZE)
        P.rb_baseband = dsp.ring_buffer2('BB',8*P.IN_CHUNK_SIZE)
        P.rb_af       = dsp.ring_buffer2('AF',P.RB_SIZE)
    elif P.MP_SCHEME==2: 
        P.rb_rf       = dsp.ring_buffer3('RF',8*P.IN_CHUNK_SIZE)
        P.rb_baseband = dsp.ring_buffer3('BB',8*P.IN_CHUNK_SIZE)
        P.rb_af       = dsp.ring_buffer3('AF',P.RB_SIZE)
        P.rf_psd_Q    = P.rb_rf.buf
        P.bb_psd_Q    = P.rb_baseband.buf
        P.af_psd_Q    = P.rb_af.buf
    else:
        print('pySDR - Unknown MP SCHEME',P.MP_SCHEME)
        sys.exit(0)

    # Open writers for data we might want to save
    P.raw_iq_io      = io.sdr_fileio('raw_iq','w',P,2,'RAW_IQ')
    P.baseband_iq_io = io.sdr_fileio('baseband_iq','w',P,2,'BASEBAND_IQ')
    if P.MODE=='IQ':
        P.demod_io       = io.sdr_fileio('demod','w',P,2,P.MODE)
    else:
        P.demod_io       = io.sdr_fileio('demod','w',P,1,P.MODE)

    # Experiment with Soapy interface
    if P.TEST_MODE:
        #from sdr_playpen import *
        sdrPlayPen(P)

    return P
        
############################################################################

# Open various threads
def start_threads(P):
    
    # Instantiate servers allowing external control of each RX
    P.threads=[]
    P.Stopper = threading.Event()
    #print "P=",pprint(vars(P))
    if P.HAMLIB_SERVERS:
        # Full suite
        for i in range(P.NUM_RX+1):
            if i<P.NUM_RX:
                port = 4575 + i
            else:
                port = 4675 + i-P.NUM_RX
            th = threading.Thread(target=rigctl.HamlibServer(P,port).Run, args=(),name='Hamlib '+str(port))
            th.setDaemon(True)
            th.start()
            P.threads.append(th)
    elif not P.REPLAY_MODE:
        # Just one to communicate with SDR
        port=4533
        th = threading.Thread(target=rigctl.HamlibServer(P,port).Run, args=(),name='Hamlib '+str(port))
        th.setDaemon(True)
        th.start()
        P.threads.append(th)

    # Instantiate the receive processor
    P.evt = threading.Event()
    P.sdr=None
    #worker = threading.Thread(target=SDR_RX, args=(P,True,),name='SDR_RX')
    worker = threading.Thread(target=SDR_EXECUTIVE(P,True).Run,args=(), name='SDR_EXEC')
    worker.setDaemon(True)
    worker.start()
    P.threads.append(worker)

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
        
    logging.info('Starting ...')
    while not P.Stopper.isSet():

        # Need to reconcile this also
        if False:
            # This is how it was for SO2V
            P.frqArx = P.sock.get_freq('A')*1e-3
        else:
            # This is better for DX split ops
            print('')
            #logging.info('Calling GetInfo ...')
            frx,ftx = GetInfo(P)
            if frx>0:
                P.frqArx = frx
            if ftx>0:
                P.frqAtx = ftx
            
        #logging.info('Resetting timer '+str(P.frqArx)+' '+str(P.frqAtx))
        time.sleep(1.)

    logging.info('Exiting.')

############################################################################

# Top-level main for pySDR
def main():

    # Put up splash screen
    app = QApplication(sys.argv)
    splash=splash_screen(app)              # In util.py
    
    # Start the processing app
    P=init_sdr()
    P.app=app
    start_threads(P)

    # Construct the gui
    if P.HOPPER:
        P.gui     = None
        P.hopper  = FreqHopper(P)
    P.logger = Logger(P)
    P.gui = pySDR_GUI(app,P) 
    splash.finish(P.gui)               # Splash will close when main window of gui is open
    P.monitor = WatchDog(P,2000)

    # Timer for PSD plotting - Calls updater every 1000/PSD_RATE millisec
    PSD_RATE=20   # was 10 Hz
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

    # Clobber splash screen
    #splash.finish(P.gui)
    #splash.close()
    #splash.hide()

    return app.exec_()


# Event loop
if __name__ == '__main__':
    main()

############################################################################
