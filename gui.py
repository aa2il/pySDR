############################################################################
#
# gui.py - Rev 1.0
# Copyright (C) 2021-3 by Joseph B. Attili, aa2il AT arrl DOT net
#
# GUI-related functions for pySDR
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
import functools
import time
import inspect
import types
from pprint import pprint
from Tables import *
from rig_control import *
from Plotting import *
from receiver import *
from rig_io.ft_tables import *
from rig_io.presets import *
from rtty import *
from widgets import *
import collections
from utils import  show_threads
from utilities import freq2band
from PyQt5.QtCore import QTimer

################################################################################

# Structure to hold a bandmap spot
class SPOT:
    def __init__(self,call,freq,color):
        self.call=call
        self.freq=freq
        self.color=color
        

# The GUI 
class pySDR_GUI(QMainWindow):

    # Routine to draw the GUI
    def __init__(self,app,P,parent=None):
        super(pySDR_GUI, self).__init__(parent)
        self.gui_closed=False
        self.prev_group=''

        # Wait for SDR to start up
        print('\npySDR_GUI: Init GUI ...\n')
        if P.MP_SCHEME==1:
            while not P.sdr:
                print('pySDR_GUI: Waiting for SDR to startup ...')
                time.sleep(1)
        elif P.MP_SCHEME==2:
            msg = P.pipe.recv()
            print('msg1=',msg)
        elif P.MP_SCHEME==3:
            print('pySDR_GUI: Waiting for SDR to startup ...')
            while P.nchunks<2:
                time.sleep(1)
        else:
            print('GUI - Unknown MP SCHEME',P.MP_SCHEME)
            sys.exit(0)

        # Init
        self.P=P
        self.last_psd_update = time.time()
        print('pySDR_GUI: ShowParams...')
        self.ShowParams()
        self.SHOW_RF_IQ=False
        self.SHOW_BASEBAND_PLOTS=False
        self.itune_cnt=0
        self.P.AF_FILTER_NUM = None

        # Start by putting up the root window
        self.win  = QWidget()
        self.setCentralWidget(self.win)
        self.setWindowTitle('pySDR by AA2IL')

        # We use a simple grid to layout controls
        self.grid = QGridLayout()
        self.win.setLayout(self.grid)
        nrows=15
        ncols=11

        # Create wideband RTTY window
        if self.P.ENABLE_RTTY:
            self.rtty=RTTY_GUI(P)
            
        ################################################################################

        # Add top row buttons
        # Start & stop rx processing - don't use this much so its disabled
        col=-1
        if False:
            col+=1
            self.btn1 = QPushButton('Start RX')
            self.btn1.setToolTip('Start/stop receiver')
            self.btn1.setCheckable(True)
            self.btn1.clicked.connect(self.StartStopRX)
            self.grid.addWidget(self.btn1,0,col)
        else:
            self.btn1 = None
        self.btn1state=True

        # Start & stop RF PSD
        col+=1
        self.btn2 = QPushButton('Start RF PSD')
        self.btn2.setToolTip('Start/stop RF PSD')
        self.btn2.setCheckable(True)
        self.btn2.clicked.connect(self.StartStopRF_PSD)
        self.grid.addWidget(self.btn2,0,col)

        # Start & stop Baseband PSD
        col+=1
        self.btn4 = QPushButton('Start IQ PSD')
        self.btn4.setToolTip('Start/stop Baseband IQ PSD')
        self.btn4.setCheckable(True)
        self.btn4.clicked.connect(self.StartStopBaseband_PSD)
        self.grid.addWidget(self.btn4,0,col)

        # Start & stop AF PSD
        col+=1
        self.btn3 = QPushButton('Start AF PSD')
        self.btn3.setToolTip('Start/stop AF PSD')
        self.btn3.setCheckable(True)
        self.btn3.clicked.connect(self.StartStopAF_PSD)
        self.grid.addWidget(self.btn3,0,col)

        # Select Sub RX to control
        col+=1
        self.sub_rx_ctrl = QComboBox()
        for i in range(P.NUM_RX):
            self.sub_rx_ctrl.addItem('RX '+str(i))
        self.grid.addWidget(self.sub_rx_ctrl,0,col)
        self.sub_rx_ctrl.currentIndexChanged.connect(self.SelectPlotRX)
        
        # Start & stop saving raw IQ data
        col+=1
        self.btn5 = QPushButton('Save Raw IQ')
        self.btn5.setToolTip('Start/stop saving data')
        self.btn5.setCheckable(True)
        self.btn5.clicked.connect(self.StartStopSave_RawIQ)
        self.grid.addWidget(self.btn5,0,col)

        # Start & stop saving baseband IQ data
        col+=1
        self.btn6 = QPushButton('Save BB IQ')
        self.btn6.setToolTip('Start/stop saving data')
        self.btn6.setCheckable(True)
        self.btn6.clicked.connect(self.StartStopSave_BasebandIQ)
        self.grid.addWidget(self.btn6,0,col)

        # Start & stop saving demod data
        col+=1
        self.btn7 = QPushButton('Save Demod')
        self.btn7.setToolTip('Start/stop saving data')
        self.btn7.setCheckable(True)
        self.btn7.clicked.connect(self.StartStopSave_Demod)
        self.grid.addWidget(self.btn7,0,col)

        # Debug - show settings
        b = QPushButton('Params')
        b.setToolTip('Show params')
        b.clicked.connect(self.ShowParams)
        self.grid.addWidget(b,0,ncols-1)

        # Exit app
        b = QPushButton('Quit')
        b.setToolTip('Click to quit!')
        b.clicked.connect( self.closeEvent )        
        self.grid.addWidget(b,0,ncols)

        ################################################################################

        # Left side relates to the SDRplay
        row=1

        # Add Antenna Selector
        if self.P.SDR_TYPE=='sdrplay':
            self.Antennas=['Ant A','Ant B','Hi-Z']
            lb=QLabel("Antenna:")
            self.Ant_cb = QComboBox()
            self.Ant_cb.addItems(self.Antennas)
            self.Ant_cb.currentIndexChanged.connect(self.AntSelect)
            #self.AntSelect(-1)
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.Ant_cb,row,1)

        # Add control for BCB band notch
        if self.P.SDR_TYPE=='sdrplay':
            lb=QLabel("BCD Notch:")
            self.BCB_btn = QPushButton('Enable')
            self.BCB_btn.setToolTip('Enable/disable AM/FM BCB notch filter')
            self.BCB_btn.clicked.connect(self.EnableBCBnotch)
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.BCB_btn,row,1)

        # Add front-end gain control (aka LNA)
        if self.P.SDR_TYPE=='sdrplay':
            self.RFgains=[str(i) for i in range(8)]
            #print 'Available RF gains=',self.RFgains
            lb=QLabel("RF Gain:")
            self.RFgain_cb = QComboBox()
            self.RFgain_cb.addItems(self.RFgains)
            self.RFgain_cb.currentIndexChanged.connect(self.LNASelect)
            #self.LNASelect(-1)
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.RFgain_cb,row,1)
        
        # Add front-end gain control (aka LNA)
        if self.P.SDR_TYPE=='rtlsdr':
            self.direct=[str(i) for i in range(3)]
            lb=QLabel("Direct Sampling:")
            self.direct_cb = QComboBox()
            self.direct_cb.addItems(self.direct)
            self.direct_cb.currentIndexChanged.connect(self.DirectSelect)
            self.DirectSelect(self.P.DIRECT_SAMP)
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.direct_cb,row,1)
        
        # Add IF sampling rate control
        if not self.P.REPLAY_MODE:
            if self.P.MP_SCHEME==2:
                RATEs = self.mp_comm('listSampleRates')
            else:
                RATEs = self.P.sdr.listSampleRates(SOAPY_SDR_RX, 0)
        else:
            RATEs = [self.P.SRATE]
        self.srates=[]
        for rate in RATEs:
            if rate>=1e6:
                rate2 = rate/1e6
                tag=' MHz'
            else:
                rate2 = rate/1e3
                tag=' KHz'
            if rate2==int(rate2):
                rate2=int(rate2)
            self.srates.append( str(rate2) + tag )
        print('SAMPLING RATEs=',RATEs)
        print('SAMPLING RATEs=',self.srates)
        lb=QLabel("Sampling Rate:")
        self.srate_cb = QComboBox()
        self.srate_cb.addItems(self.srates)
        self.srate_cb.currentIndexChanged.connect(self.SrateSelect)
        #self.SrateSelect(-1)
        row+=1
        self.grid.addWidget(lb,row,0)
        self.grid.addWidget(self.srate_cb,row,1)

        # Add IF bandwidth selection - this is tightly coupled to sample rate
        # selection so is not of much use
        if self.P.SDR_TYPE=='sdrplay':
            if self.P.MP_SCHEME==2:
                BWs=self.mp_comm('listBandwidths')
            else:
                BWs=self.P.sdr.listBandwidths(SOAPY_SDR_RX, 0)
            # print "Available Bandwidths=",self.BWs
            self.bws=[]
            for bw in BWs:
                if bw>=1e6:
                    bw2 = bw/1e6
                    tag=' MHz'
                else:
                    bw2 = bw/1e3
                    tag=' KHz'
                if bw2==int(bw2):
                    bw2=int(bw2)
                self.bws.append( str(bw2) + tag )

            lb=QLabel("IF Bandwidth:")
            self.BW_cb = QComboBox()
            self.BW_cb.addItems(self.bws)
            self.BW_cb.currentIndexChanged.connect(self.IF_BWSelect)
            #self.IF_BWSelect(-1)
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.BW_cb,row,1)

        # Add IF freq control
        self.IFs=['0 KHz','450 KHz','1620 KHz','2048 KHz']
        lb=QLabel("IF:")
        self.IF_cb = QComboBox()
        self.IF_cb.addItems(self.IFs)
        self.IF_cb.currentIndexChanged.connect(self.IFSelect)
        #self.IFSelect(-1)
        row+=1
        self.grid.addWidget(lb,row,0)
        self.grid.addWidget(self.IF_cb,row,1)

        # Add IF Gain control
        if P.REPLAY_MODE:
            self.IFgains=['1']
        else:
            if self.P.SDR_TYPE=='sdrplay':
                stage='IFGR'
            elif self.P.SDR_TYPE=='rtlsdr':
                stage='TUNER'
            if self.P.MP_SCHEME==2:
                rr = self.mp_comm('getGainRange',stage)
            else:
                r = self.P.sdr.getGainRange(SOAPY_SDR_RX, 0,stage)
                if type(r)==list:
                    rr=r
                else:
                    print("\nr=",r,type(r),r.minimum(),r.maximum(),r.step())
                    rr = [r.minimum(),r.maximum(),r.step()]
            self.dgain = rr[2]
            if self.dgain==0:
                self.dgain = rr[1]/10.
            
            if self.P.SDR_TYPE=='sdrplay':
                self.IFgains=[str(i) for i in range(int(rr[0]),int(rr[1]+0.5))]
            else:
                self.IFgains=[str(i) for i in np.arange(rr[0],rr[1]+self.dgain/2.,self.dgain)]
        print(self.IFgains)
        
        lb=QLabel("IF Gain:")
        self.IFgain_cb = QComboBox()
        self.IFgain_cb.addItems(self.IFgains)
        self.IFgain_cb.currentIndexChanged.connect(self.IFGainSelect)
        #self.IFGainSelect(-1)
        row+=1
        self.grid.addWidget(lb,row,0)
        self.grid.addWidget(self.IFgain_cb,row,1)

        # Add text boxes to show freq of each rx
        self.rx_frq_box = []
        for i in range(P.NUM_RX):
            lb=QLabel("RX"+str(i)+":")
            self.rx_frq_box.append( QLineEdit() )
            row+=1
            self.grid.addWidget(lb,row,0)
            self.grid.addWidget(self.rx_frq_box[i],row,1)
            self.rx_frq_box[i].setText( "{0:,.1f} KHz".format(P.FC[i]/1000.) )

        # Add button to force a hop
        row+=1
        self.Hop_btn = QPushButton('Force a Hop')
        self.Hop_btn.setToolTip('Force a Hop')
        self.grid.addWidget(self.Hop_btn,row,0,1,2)
        if P.HOPPER:
            self.Hop_btn.clicked.connect(self.P.hopper.Hopper)
        else:
            self.Hop_btn.setEnabled(False)
            
        ################################################################################

        # The middle relates to tuning - start by adding freq readout        
        self.lcd = MyLCDNumber(None,7,1,ival=.001*P.FC[0],wheelCB=self.FreqSelect)
        self.grid.addWidget(self.lcd,1,2,5,ncols-3)
        self.SelectPlotRX(0)

        # Add tabs to hold buttons for presets
        self.tabs = QTabWidget()
        self.grid.addWidget(self.tabs,6,2,nrows-6,ncols-3)

        # Add tab for rig control
        if P.sock and P.sock.connection!='NONE' and P.RIG_CONTROL_MENU:
            self.rig = RIG_CONTROL(self.tabs,P)

        # Add presets
        ncols2=6
        presets = read_presets2(None,'Presets')
        for line in presets:
            grp=line['Group']
            if grp=='Sats':
                continue     # Skip this group
            elif grp=='HAM':
                for b in ['160m','80m','40m','20m','15m','10m']:
                    ham_band=make_ham_presets2(b,bands,P.PAN_BW,P.RIG_IF)
                    for sub_band in ham_band:
                        self.create_presets2('Ham 1',sub_band,ncols2)
                for b in ['60m','30m','17m','12m','6m','2m','1.25m','70cm','33cm','23cm']:
                    ham_band=make_ham_presets2(b,bands,P.PAN_BW,P.RIG_IF)
                    for sub_band in ham_band:
                        self.create_presets2('Ham 2',sub_band,ncols2)
            else:
                self.create_presets2(grp,line,ncols2)

        # Volume control
        lb=QLabel("AF Gain:")
        self.grid.addWidget(lb,nrows,1)
        self.afgain = QSlider(Qt.Horizontal)
        # sld.setFocusPolicy(Qt.NoFocus)
        self.afgain.setMinimum(0)
        self.afgain.setMaximum(100)
        self.afgain.setValue(int(P.VOL))
        self.afgain.valueChanged.connect(self.VolumeControl)
        self.afgain.setTickPosition(QSlider.TicksBelow)
        self.afgain.setTickInterval(10)
        self.grid.addWidget(self.afgain,nrows,2,1,ncols-3)
        self.VolumeControl()

        # Mute Buttons
        self.Mute_btns = [None]*P.MAX_RX
        irow=nrows-2
        icol=ncols-1
        for i in range(P.MAX_RX):
            self.Mute_btns[i] = QPushButton('Mute RX'+str(i+1))
            self.Mute_btns[i].setToolTip('Click to Mute/Unmute Audio')
            self.Mute_btns[i].clicked.connect( functools.partial( self.MuteCB,i,False ))
            self.Mute_btns[i].setCheckable(True)
            if i>=P.NUM_RX:
                self.Mute_btns[i].setEnabled(False)
            self.MuteCB(i,True)

            self.grid.addWidget(self.Mute_btns[i],irow,icol)
            icol=icol+1
            if icol>ncols:
                irow+=1
                icol=ncols-1

        ################################################################################

        # Right side (mostly) relates to demodulation/info extraction
        # Add Tuning step
        row=2
        self.steps=["10 Hz","100 Hz","1 KHz","5 KHz","10 KHz","25 KHz","50 KHz",\
                    "100 KHz","200 KHz","1 MHz","10 MHz","100 MHz","1 GHz"]
        lb=QLabel("Tuning Step:")
        self.grid.addWidget(lb,row,ncols-1)
        self.step_cb = QComboBox()
        self.step_cb.addItems(self.steps)
        self.step_cb.currentIndexChanged.connect(self.StepSelect)
        self.step_cb.setCurrentIndex(4)
        self.grid.addWidget(self.step_cb,row,ncols)

        # Add Mode selector
        row+=1
        self.modes = MODES
        lb=QLabel("Demodulator:")
        self.grid.addWidget(lb,row,ncols-1)
        self.mode_cb = QComboBox()
        self.mode_cb.addItems(self.modes)
        self.mode_cb.currentIndexChanged.connect(self.ModeSelect)
        self.grid.addWidget(self.mode_cb,row,ncols)
        #self.ModeSelect(-1)

        # Add vidio bandwidth selector
        row+=1
        self.video_bws = VIDEO_BWs
        lb=QLabel("Video Bandwidth:")
        self.grid.addWidget(lb,row,ncols-1)
        self.vidbw_cb = QComboBox()
        self.vidbw_cb.addItems(self.video_bws)
        self.vidbw_cb.currentIndexChanged.connect(self.Video_BWSelect)
        self.grid.addWidget(self.vidbw_cb,row,ncols)
        #self.Video_BWSelect(-1)

        # Add audio bandwidth selector
        row+=1
        self.af_bws = AF_BWs
        lb=QLabel("AF Bandwidth:")
        self.grid.addWidget(lb,row,ncols-1)
        self.afbw_cb = QComboBox()
        self.afbw_cb.addItems(self.af_bws)
        self.afbw_cb.currentIndexChanged.connect(self.AF_BWSelect)
        self.grid.addWidget(self.afbw_cb,row,ncols)
        #self.AF_BWSelect(-1)

        ################################################################################

        # Add buttons to control pan-adaptor
        # Checkbox to turn it on and off
        row+=1
        self.pan_cb = QCheckBox("Pan-adaptor Mode")
        self.pan_cb.setChecked(True)
        self.grid.addWidget(self.pan_cb,row,ncols-1)

        # Scroll box to control direction of Pan adaptor
        self.PanDirs=['Up/Down','Up','Down']
        self.PanDir_cb = QComboBox()
        self.PanDir_cb.addItems(self.PanDirs)
        self.PanDir_cb.currentIndexChanged.connect(self.PanDirSelect)
        self.PanDirSelect(0)
        self.grid.addWidget(self.PanDir_cb,row,ncols)
       
        # Scroll box to select display bandwidth
        row+=1
        self.PanBWs=PAN_BWs
        lb=QLabel("Pan BW:")
        self.PanBW_cb = QComboBox()
        self.PanBW_cb.addItems(self.PanBWs)
        self.PanBW_cb.currentIndexChanged.connect(self.PanBWSelect)
        print('----------------- PAN BW=',P.PAN_BW)
        #self.PanBWSelect(-1)
        self.grid.addWidget(lb,row,ncols-1)
        self.grid.addWidget(self.PanBW_cb,row,ncols)

        # Scroll box to select dynamic range
        row+=1
        self.PanDRs=[str(i) for i in range(10,100,10)]
        lb=QLabel("Dynamic Range:")
        self.PanDR_cb = QComboBox()
        self.PanDR_cb.addItems(self.PanDRs)
        self.PanDR_cb.currentIndexChanged.connect(self.PanDRSelect)
        #self.PanDRSelect(-1)
        self.grid.addWidget(lb,row,ncols-1)
        self.grid.addWidget(self.PanDR_cb,row,ncols)

        # Scroll box to select min peak distance
        row+=1
        self.PeakDists=['100 Hz','1 KHz','10 KHz']
        lb=QLabel("Min Peak Distance:")
        self.PeakDist_cb = QComboBox()
        self.PeakDist_cb.addItems(self.PeakDists)
        self.PeakDist_cb.currentIndexChanged.connect(self.PeakDistSelect)
        #self.PeakDistSelect(-1)
        self.grid.addWidget(lb,row,ncols-1)
        self.grid.addWidget(self.PeakDist_cb,row,ncols)

        # Check box to use peaks for tuning
        row+=1
        self.Use_Peaks_cb = QCheckBox("Use Peaks for Tuning")
        self.Use_Peaks_cb.setChecked(False)
        self.grid.addWidget(self.Use_Peaks_cb,row,ncols-1)

        # Check box to add offset for digi modes
        self.DIGI_OFFSET=1000*1e-3
        self.digi_cb = QCheckBox("Add Digi Offset")
        self.digi_cb.setChecked(self.P.DIGI_OFFSET)
        self.grid.addWidget(self.digi_cb,row,ncols)

        # Check boxes to follow center freq of transceiver
        row+=1
        self.follow_freq_cb = QCheckBox("Follow RIG Freq")
        self.follow_freq_cb.setChecked(self.P.FOLLOW_FREQ)
        self.grid.addWidget(self.follow_freq_cb,row,ncols-1)

        self.follow_band_cb = QCheckBox("Follow RIG Band")
        self.follow_band_cb.setChecked(self.P.FOLLOW_BAND) 
        self.grid.addWidget(self.follow_band_cb,row,ncols)

        row+=1
        self.split_cb = QCheckBox("CLAR Follows SDR Freq")
        self.split_cb.setChecked(False)
        self.grid.addWidget(self.split_cb,row,ncols-1)

        self.so2v_cb = QCheckBox("VFO-B Follows SDR Freq")
        self.so2v_cb.setChecked(self.P.SO2V)
        self.grid.addWidget(self.so2v_cb,row,ncols)

        ################################################################################

        # Setup timer to make sure we don't hang
        self.timer1 = QTimer()
        self.timer1.timeout.connect(self.TicToc)
        self.timer1.start(5000)

        ################################################################################

        # Open plotting windows
        #title="pySDR by AA2IL"
        self.plots_rf=three_box_plot(P,"RF - AA2IL","RF Time Series","RF PSD", \
                                     P.SRATE/1000.,P.FOFFSET/1000.,P.IN_CHUNK_SIZE,
                                     2*P.IN_CHUNK_SIZE,0.,self.MouseClickRF,P.TRANSPOSE)
        self.plots_rf.hide()
        OVERLAP = 0.5   # 0.75
        self.plots_af=three_box_plot(P,"Demod Audio - AA2IL","AF Time Series","AF PSD", \
                                     P.FS_OUT/1000.,0,4*P.OUT_CHUNK_SIZE,
                                     8*P.OUT_CHUNK_SIZE,OVERLAP,self.MouseClickRF,P.TRANSPOSE)
        self.plots_af.hide()
        self.plots_bb=three_box_plot(P,"Baseband IQ - AA2IL","Baseband Time Series", \
                                     "Baseband PSD", P.FS_OUT/1000.,0,P.IN_CHUNK_SIZE,
                                     2*P.IN_CHUNK_SIZE,0.,self.MouseClickRF,P.TRANSPOSE)
        self.plots_bb.hide()

        # Finally, we're ready to show the gui
        print('------------------------- And Away We Go !!!!!!!!!!!!!!!!!!!!!!')
        self.show()

        # Move to lower left corner of screen
        screen_resolution = app.desktop().screenGeometry()
        self.screen_width  = screen_resolution.width()
        self.screen_height = screen_resolution.height()
        if P.GEO==None:
            widget = self.geometry()
            print("Screen Res:",screen_resolution,self.screen_width, self.screen_height)
            self.move(0, self.screen_height - widget.height() )
        else:
            # WWWxHHH+XXX+YYY
            # pySDR.py -geo 1100x530+5+540
            print('geo=',P.GEO)
            geo2=P.GEO.split('+')
            print('geo2=',geo2)
            geo3=geo2[0].split('x')
            print('geo3=',geo3)
            w=int( geo3[0] )
            h=int( geo3[1] )
            x=int( geo2[1] )
            y=int( geo2[2] )
            print('geo=',P.GEO,'\tx=',x,'\ty=',y,'\tw=',w,'\th=',h)
            self.setGeometry(x,y,w,h)
            
        if P.DESKTOP!=None:
            cmd1='wmctrl -r "'+self.windowTitle()+'" -t '+str(P.DESKTOP)
            print('cmd1=',cmd1)
            os.system(cmd1)

            """
            cmd2='wmctrl -r "'+self.plots_rf.pwin.windowTitle()+'" -t '+str(P.DESKTOP)
            print('cmd2=',cmd2)
            os.system(cmd2)
            
            cmd3='wmctrl -r "'+self.plots_af.pwin.windowTitle()+'" -t '+str(P.DESKTOP)
            print('cmd3=',cmd3)
            os.system(cmd3)
            
            cmd4='wmctrl -r "'+self.plots_bb.pwin.windowTitle()+'" -t '+str(P.DESKTOP)
            print('cmd4=',cmd4)
            os.system(cmd4)
            """
        

    ################################################################################

    def TicToc(self):
        #print('Tic Toc ...')
        if self.P.Stopper.is_set():
            print('Tic Toc - Triggering closeEvent ...')
            self.closeEvent()
        
    ################################################################################

    # Routine to start the GUI
    def StartGUI(self):

        P=self.P

        # Set various gui checkboxes, etc.
        self.SrateSelect(-1)
        self.IFSelect(-1)
        self.IFGainSelect(-1)
        self.ModeSelect(-1)
        self.Video_BWSelect(-1)
        self.AF_BWSelect(-1)
        self.PanBWSelect(-1)
        self.PanDRSelect(-1)
        self.PeakDistSelect(-1)
        if self.P.SDR_TYPE=='sdrplay':
            self.AntSelect(-1)
            self.LNASelect(-1)
            self.IF_BWSelect(-1)
        
        # Activate various options
        if P.PANADAPTOR:
            self.StartStopAF_PSD()
            
        if P.FOLLOW_FREQ:
            self.follow_freq_cb.setChecked(True)
            
        # Make sure rig settings are reasonable
        P.sock.set_vfo('A','A')
        P.sock.set_vfo(op='A->B')
        P.sock.set_sub_dial(func='CLAR')
        self.rig_retune()
        if False:
            # Not sure why I thought we needed to do this
            # It sets all the rx's to the same freq 
            fc = self.lcd.get()
            print('BURP1: FC=',fc,P.FC)
            for i in range(1,P.NUM_RX):
                P.FC[i]=1000*fc
            print('BURP2: FC=',fc,P.FC)
            self.FreqSelect(fc,False)
        
        if P.ENABLE_RTTY:
            if self.rtty.active:
                self.rtty.raise_()
        print('pySDR: GUI ready ... ')
        if P.MP_SCHEME==2:
            self.mp_comm('GUIready')
      
    ################################################################################

    # Routine to close down gracefully
    def closeEvent(self, event=None):
        print('CloseEvent ...')

        # This seems to get called twice so trap second call
        if self.gui_closed:
            return
        else:
            self.gui_closed=True

        # Close plotting windows
        if self.P.SHOW_RF_PSD:
        #    self.plots_rf.pwin.close()
            self.StartStopRF_PSD()
        if self.P.SHOW_AF_PSD:
            self.StartStopAF_PSD()
        if self.P.SHOW_BASEBAND_PSD:
            self.StartStopBaseband_PSD()

        print('\n--------------------------------------------------------------------------')
        print('closeEvent: Stopping timers...')
        self.P.PSDtimer.stop()
        print("--- PSD timer stopped")
        #self.P.monitor.timer.stop()
        print("--- WatchDog timer stopped")
        time.sleep(1)
        
        if self.P.MP_SCHEME==2:
            print('closeEvent: Closing down RX ...')
            self.mp_comm('Shutdown')
            print('--- Waiting for RX to join...')
            self.P.mp_proc.terminate()
            self.P.mp_proc.join()
            self.P.pipe=None
            print('--- RX joined.')

        if self.P.MP_SCHEME==3:
            print('closeEvent: Closing down RX ...')
            self.mp_comm('Shutdown')
            
        if self.P.ENABLE_RTTY:
            if self.rtty.active:
                self.rtty.wrap_up()
                print('Waiting for RTTY to exit...')
                while self.rtty.active and True:
                    time.sleep(1)
                    self.P.app.processEvents() 

        if self.P.UDP_CLIENT and self.P.udp_client:
            #self.P.udp_client.Close()
            self.P.udp_client.Stopper.set()
                    
        # Loop through all the threads and close (join) them
        print("Waiting for threads to quit...")
        show_threads()
        for th in self.P.threads:
            print('\tWaiting for thread to quit -',th.getName(),' ...')
            if self.P.Stopper:
                self.P.Stopper.set()
            th.join(5.0)
            print('\t... Thread quit -',th.getName())
            
        print("Closing down gui ...")
        
        #if self.P.SHOW_RF_PSD:
        #    self.plots_rf.pwin.close()
        #    print "Closing down gui - RF PSD closed"
        #self.plots_af.close()
        app = QApplication.instance()
        app.quitOnLastWindowClosed=False
        print("Closing down gui - Closing all windows ...")
        app.closeAllWindows()
        print("Closing down gui - All windows closed")
        time.sleep(1)
        self.win.destroy()
        print("Closing down gui - Main window closed")
        print("\nThat's all folks!\n")
        show_threads()
        sys.exit(0)

    # Function to create preset push buttons
    def create_presets(self,tag,station_list,ncols):

        #print 'CREATE_PRESETS:',tag,station_list

        # Add a tab
        tab1 = QWidget()
        self.tabs.addTab(tab1,tag)
        grid = QGridLayout()
        tab1.setLayout(grid)

        # Add a grid of buttons
        i=0
        j=0
        for s in station_list:
            #print 'CREATE PRESETS:',s,'\n',station_list[s]
            b = QPushButton(s)
            
            f1=station_list[s][0]              # Freq 1
            m=station_list[s][1]               # Mode
            if len(station_list[s])>2:
                f2=station_list[s][2]          # Freq 2
            else:
                f2=f1
            f=(f1+f2)/2                        # Tune to center of band

            # Set tool tip to show freq(s)
            fthresh=30e3             # Above 30 MHz, show MHz instead of KHz
            if f1!=f2:
                if f>fthresh:
                    tip="{:,} - {:,} MHz".format(.001*f1,.001*f2)
                else:
                    tip="{:,d} - {:,d} KHz".format(int(f1),int(f2))
            else:
                if f>=fthresh:
                    tip="{:,} MHz".format(.001*f)
                else:
                    tip="{:,d} KHz".format(int(f))
            b.setToolTip(tip)

            if len(station_list[s])>4:
                vidbw = station_list[s][4]     # Video bw
                afbw  = station_list[s][5]     # Audio bw
            else:
                vidbw = preset_prefs[m][0]     # Default video bw for this mode
                afbw  = preset_prefs[m][1]     # Default audio bw for this mode

            #print 'CREATE_PRESETS:',f,m,vidbw,afbw
            #print s,station_list[s]
            #print m,preset_prefs[m]
            
            b.clicked.connect(functools.partial(self.PresetSelect,f,m,vidbw,afbw))
            i=i+1
            if i>ncols:
                i=1
                j=j+1
            #            print s,f,m,j,i
            grid.addWidget(b,j,i)

        #sys.exit(0)
        
    # Function to create preset a push button
    def create_presets2(self,grp,station,ncols):

        #print 'CREATE_PRESETS2:',tag,station

        # Add a tab
        if grp!=self.prev_group:
            tab1 = QWidget()
            self.tabs.addTab(tab1,grp)
            self.preset_grid = QGridLayout()
            tab1.setLayout(self.preset_grid)
            self.prev_group=grp
            self.ipreset=0
            self.jpreset=0

        # Add a button
        #print 'CREATE PRESETS:',s,'\n',station_list[s]
        b = QPushButton(station['Tag'])
            
        f1=station['Freq1 (KHz)']              # Freq 1
        m=station['Mode']                      # Mode
        if m=='AM-N':
            m='AM'
        f2=station['Freq2 (KHz)']              # Freq 2
        if f2==0:
            f2=f1
        f=(f1+f2)/2                            # Tune to center of band

        # Set tool tip to show freq(s)
        fthresh=30e3             # Above 30 MHz, show MHz instead of KHz
        if f1!=f2:
            if f>fthresh:
                tip="{:,} - {:,} MHz".format(.001*f1,.001*f2)
            else:
                tip="{:,d} - {:,d} KHz".format(int(f1),int(f2))
        else:
            if f>=fthresh:
                tip="{:,} MHz".format(.001*f)
            else:
                tip="{:,d} KHz".format(int(f))
        b.setToolTip(tip)

        vidbw = station['Video BW (KHz)']     # Video bw
        if vidbw==0:
            vidbw = preset_prefs[m][0]        # Default video bw for this mode
        afbw = station['Audio BW (KHz)']      # Video bw
        if afbw==0:
            afbw = preset_prefs[m][1]         # Default video bw for this mode

        #print 'CREATE_PRESETS:',f,m,vidbw,afbw
        #print s,station_list[s]
        #print m,preset_prefs[m]
            
        b.clicked.connect(functools.partial(self.PresetSelect,f,m,vidbw,afbw))
        self.ipreset+=1
        if self.ipreset>ncols:
            self.ipreset=1
            self.jpreset+=1
            #            print s,f,m,j,i
        self.preset_grid.addWidget(b,self.jpreset,self.ipreset)

    #sys.exit(0)
    
        
    # Callback to handle pan-adaptor check box - not used but keep as a model
    def PanAdaptorCB(self):
        if self.pan_cb.isChecked():
            print("Hey - checked")
        else:
            print("Hey - un-checked")

    # Callback to show current params
    def ShowParams(self):
        #print self.P
        print("P=",pprint(vars(self.P)))

        if False:
            members = [attr for attr in dir(self.P) if not isinstance(getattr(self.P, attr), collections.Callable) and not attr.startswith("__")]
            print('members=',members)   
            #temp = vars( self.P )
            #for attr in members:
            #    if not isinstance(attr,self.P):
            #        print attr, ' : ' , temp[attr]
            
            #return
            
            for i in inspect.getmembers(self.P):
                # Ignores anything starting with underscore 
                # (that is, private and protected attributes)
                if not i[0].startswith('_'):
                    # Ignores methods
                    if not inspect.ismethod(i[1]) and not type(i[1]) is types.InstanceType:
                        print(i[0],type(i))
                        print(i[1])
                        #                    print(i)
                        
            return

        #print dir( self.P )
        #print vars( self.P )
        #print self.P.__dict__

        if self.P.MP_SCHEME==2:
            self.mp_comm('CheckSdrSettings')
        else:
            check_sdr_settings(self.P)

    # Callback for Volume control slider
    def VolumeControl(self):
        self.P.VOL = self.afgain.value()
        self.P.AF_GAIN=2*self.afgain.value()/100.
        #print('VOLUME CONTROL out: gain=',self.P.AF_GAIN,'\tslider=',self.P.VOL)

    # Callback for RX Start/Stop button
    def StartStopRX(self):
        if self.btn1state:
            if self.btn1:
                self.btn1.setText('Stop RX')
            if self.P.MP_SCHEME==1:
                print("Starting receiver ...")
                self.P.SDR_EXEC.start_rx()
                print("... Receiver started ...")
        else:
            if self.btn1:
                self.btn1.setText('Start RX')
            if self.P.MP_SCHEME==1:
                print("Stopping receiver ...")
                self.P.SDR_EXEC.stop_rx()
                print("... Receiver stopped ...")

        self.btn1state = not self.btn1state

    # Callback to select which RX is plotted
    def SelectPlotRX(self,irx):
        self.P.PLOT_RX=irx
        print('SelectPlotRX: RX to plot set to',self.P.PLOT_RX)
        if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
            self.mp_comm('setPlotRX',self.P.PLOT_RX )

        self.P.MAIN_RX=irx
        frq=.001*self.P.FC[irx]
        self.lcd.set(frq)
        self.P.BAND = freq2band(1e-3*frq)
    
    # Callback for RF PSD Start/Stop button
    def StartStopRF_PSD(self):
        if not self.P.SHOW_RF_PSD:
            self.btn2.setText('Stop RF PSD')
            self.plots_rf.pwin.show()

            if self.P.DESKTOP!=None and self.plots_rf.first_time:
                cmd2='wmctrl -r "'+self.plots_rf.pwin.windowTitle()+'" -t '+str(self.P.DESKTOP)
                print('cmd2=',cmd2)
                os.system(cmd2)
                self.plots_rf.first_time=False
            
        else:
            self.btn2.setText('Start RF PSD')
            self.plots_rf.pwin.hide()

        self.P.SHOW_RF_PSD = not self.P.SHOW_RF_PSD
        if self.P.MP_SCHEME==2:
            self.mp_comm('showRFpsd',self.P.SHOW_RF_PSD )
        
    # Callback for Baseband PSD Start/Stop button
    def StartStopBaseband_PSD(self):
        if not self.P.SHOW_BASEBAND_PSD:
            self.btn4.setText('Stop BB IQ PSD')
            self.plots_bb.pwin.show()
            if self.P.TRANSPOSE:
                w=int(self.screen_width/5)
                h=self.screen_height-1
                x=4*w
                y=0
            else:
                x=0
                y=0
                w=self.screen_width-1
                h=int(self.screen_height/5)
            self.plots_bb.pwin.setGeometry( QRect(x,y,w,h) )

            if self.P.DESKTOP!=None and self.plots_bb.first_time:
                cmd4='wmctrl -r "'+self.plots_bb.pwin.windowTitle()+'" -t '+str(self.P.DESKTOP)
                print('cmd4=',cmd4)
                os.system(cmd4)
                self.plots_bb.first_time=False
            
        else:
            self.btn4.setText('Start BB IQ PSD')
            self.plots_bb.pwin.hide()

        self.P.SHOW_BASEBAND_PSD = not self.P.SHOW_BASEBAND_PSD
        if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
            self.mp_comm('showBBpsd',self.P.SHOW_BASEBAND_PSD )

    # Callback for AF PSD Start/Stop button
    def StartStopAF_PSD(self):
        self.P.SHOW_AF_PSD = not self.P.SHOW_AF_PSD
        if self.P.SHOW_AF_PSD:
            print('STARTing AF PSD ...')
            self.btn3.setText('Stop AF PSD')
            self.plots_af.pwin.show()
            if self.P.TRANSPOSE:
                w=int(self.screen_width/5)
                h=self.screen_height-1
                x=4*w
                y=0
            else:
                x=0
                y=0
                w=self.screen_width-1
                h=int(self.screen_height/5)
            self.plots_af.pwin.setGeometry( QRect(x,y,w,h) )
            self.btn3.setChecked(True)

            if self.P.DESKTOP!=None and self.plots_af.first_time:
                cmd3='wmctrl -r "'+self.plots_af.pwin.windowTitle()+'" -t '+str(self.P.DESKTOP)
                print('cmd3=',cmd3)
                os.system(cmd3)
                self.plots_af.first_time=False
                
        else:
            self.btn3.setText('Start AF PSD')
            self.plots_af.pwin.hide()
            self.btn3.setChecked(False)

        if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
            self.mp_comm('showAFpsd',self.P.SHOW_AF_PSD )
        
    # Callback for Start/Stop Raw IQ Save button
    def StartStopSave_RawIQ(self):
        if not self.P.SAVE_IQ:
            self.btn5.setText('Stop IQ Save')
        else:
            #self.btn5.setText('Resume IQ Save')
            self.btn5.setText('Start IQ Save')
            self.P.raw_iq_io.close()

        self.P.SAVE_IQ = not self.P.SAVE_IQ
        
    # Callback for Start/Stop Baseband Save button
    def StartStopSave_BasebandIQ(self):
        if not self.P.SAVE_BASEBAND:
            self.btn6.setText('Stop BB IQ Save')
        else:
            #self.btn6.setText('Resume BB IQ Save')
            self.btn6.setText('Start BB IQ Save')
            self.P.baseband_iq_io.close()

        self.P.SAVE_BASEBAND = not self.P.SAVE_BASEBAND
        
    # Callback for Start/Stop Demod Save button
    def StartStopSave_Demod(self,iopt=None):
        if (iopt==None and not self.P.SAVE_DEMOD) or iopt==1:
            if not self.P.SAVE_DEMOD:
                self.btn7.setText('Stop Demod Save')
                self.P.SAVE_DEMOD = True
                print('Saving demod started ...')
                self.btn7.setChecked(self.P.SAVE_DEMOD)
        else:
            if self.P.SAVE_DEMOD:
                self.btn7.setText('Start Demod Save')
                self.P.demod_io.close()
                self.P.SAVE_DEMOD = False
                print('Saving demod stopped ...')
                self.btn7.setChecked(self.P.SAVE_DEMOD)
        
    # Function to update PSD display
    def UpdatePSD(self):

        # Update other params
        #print('UpdatePSD in...')
        P=self.P
        P.SO2V = self.so2v_cb.isChecked()

        # Get tuner freq
        if P.RIG_IF==0 and True:
            fc = self.lcd.get()
        else:
            fc = P.frqArx
        #print('UpdatePSD:',P.SO2V,fc)

        # Determine what plots to show
        if self.pan_cb.isChecked():
            show_time_series = False
            show_psd = False
            P.PSD_BB_FC3=fc
            if self.P.PANADAPTOR:
                P.PSD_AF_FC2 = fc
            else:
                P.PSD_AF_FC2 = 0
            #if P.MODE=='WFM' or self.P.MODE=='WFM2': 
            #    P.PSD_AF_FC2 = 0
            #else:
            #    P.PSD_AF_FC2 = fc

            #print '\nPlotting ...',fc,P.RIG_IF,P.frqArx
            
        else:
            show_time_series = True
            show_psd = True
            P.PSD_AF_FC2 = 0
            P.PSD_BB_FC3 = 0
        
        if P.SHOW_RF_PSD:
            n=self.plots_rf.psd.chunk_size
            fc1 = 1*fc - 0*0.001*P.FOFFSET
            #print 'fc1=',fc1,fc, P.FOFFSET, P.BFO
            if P.MP_SCHEME==1:
                # Should eventually be able to eliminate this path
                if P.rb_rf.ready(2*n):
                    x = list(range(n))
                    y = P.rb_rf.pull(n,True)
                    self.plots_rf.plot(x,y,fc1,self.SHOW_RF_IQ,True)

                    if False:
                        x = [fc, fc]
                        y=[min(PSD),max(PSD)]
                        self.curve1d.setData(x,y)

            else:
                y = P.rb_rf.pull(n,True)
                if len(y)>0:
                    x = list(range(n))
                    self.plots_rf.plot(x,y,fc1,self.SHOW_RF_IQ,True)
                    
        if P.SHOW_AF_PSD:

            # Shift offset of waterfall to effect 1-KHz offset for digi programs
            if self.digi_cb.isChecked():
                self.plots_af.foff = self.DIGI_OFFSET
            else:
                self.plots_af.foff = 0
            #print('AF foff=',self.plots_af.foff)
            
            N=self.plots_af.psd.chunk_size
            new_samps=self.plots_af.psd.new_samps
            if P.MP_SCHEME==1:
                # Should eventually be able to eliminate this path
                nsamp = P.rb_af.nsamps
                npsds = int(nsamp/new_samps)
                x = list(range(new_samps))
                for i in range(npsds):
                    y = P.rb_af.pull(new_samps,True)
                    self.plots_af.plot(x,y,P.PSD_AF_FC2,show_time_series,show_psd)
            else:
                x = list(range(new_samps))
                while True:
                    y = P.rb_af.pull(new_samps)
                    if len(y)>0:
                        self.plots_af.plot(x,y,P.PSD_AF_FC2,show_time_series,show_psd)
                    else:
                        break

            if P.NEW_SPOT_LIST:
                print('UPDATEPSD: New Spot List:',P.NEW_SPOT_LIST)
                self.plots_af.removeAllSpots()
                self.Spots=[]
                for n in range(0,len(P.NEW_SPOT_LIST),3):
                    call=P.NEW_SPOT_LIST[n]
                    freq=P.NEW_SPOT_LIST[n+1]

                    # Decode spot color - single letters were used to shorten messages
                    c=P.NEW_SPOT_LIST[n+2]
                    if c=='r':
                        c="red"
                    elif c=='m':
                        c="magenta"
                    elif c=='v':
                        c="violet"
                    elif c=='p':
                        c="pink"
                    elif c=='lb':
                        c="lightskyblue" 
                    elif c=='t':
                        c="turquoise"
                    elif c=='b':
                        #c="deepskyblue"
                        c="blue"
                    elif c=='d':
                        c="gold"
                    elif c=='o':
                        c='orange'
                    elif c=='y':
                        c='yellow'
                    elif c=='g':
                        c='lightgreen'
                    elif len(c)==1:
                        # Catch all so program doesn't crash & burn
                        c='w'
                        
                    self.plots_af.addSpot(freq,100,call,c)
                    self.Spots.append(SPOT(call,freq,c))
                P.NEW_SPOT_LIST=None
                

        if P.SHOW_BASEBAND_PSD:
            P.PSD_BB_FC3 += 0*0.001*P.FOFFSET
            n=self.plots_bb.psd.chunk_size

            # Shift offset of waterfall to effect 1-KHz offset for digi programs
            #print('BB foff=',self.plots_bb.foff)
            #if self.digi_cb.isChecked():
            #    self.plots_bb.foff = self.DIGI_OFFSET
                        
            if P.MP_SCHEME==1:
                # Should eventually be able to eliminate this path
                if P.rb_baseband.ready(2*n):
                    x = list(range(n))
                    y = P.rb_baseband.pull(n,True)
                    self.plots_bb.plot(x,y,P.PSD_BB_FC3,show_time_series,show_psd)
            else:
                y = P.rb_baseband.pull(n)
                if len(y)>0:
                    x = list(range(n))
                    self.plots_bb.plot(x,y,P.PSD_BB_FC3,show_time_series,show_psd)

        # Get transciever center freq & retune if necessary
        # We don't do it each time to help improve gui response
        self.itune_cnt+=1
        if self.itune_cnt==20:
            self.itune_cnt=0
            self.rig_retune()

        t_old = self.last_psd_update 
        self.last_psd_update = time.time()
        #        print "PSD update time=",self.last_psd_update-t_old
        #print('UpdatePSD ...out')


    # Function to retune rig if necessary
    def rig_retune(self):
        #vfo_in= self.P.sock.get_vfo()
        #print('RIG RETUNE ... vfo_in=',vfo_in)

        if not self.P.sock:
            print('&&&&&&&&&&&&&&&& RIG_RETUNE: WARNING - No socket to rig &&&&&&&&&&&&&&&&&')
            return
        
        if self.follow_freq_cb.isChecked() or self.so2v_cb.isChecked():
            #print('RIG RETUNE - following rig freq or so2v ...')
            if not self.P.sock.active:
                print('RIG_RETUNE 1: *** No connection to rig *** ')
                self.follow_freq_cb.setChecked(False)
                return

            fc = self.lcd.get()
            vfo='A'
            if self.so2v_cb.isChecked():
                vfo='B'
                self.P.sock.set_sub_dial(func='VFO-B')

            if self.split_cb.isChecked():
                df_rx,df_tx=self.P.sock.read_clarifier()
                self.P.sock.set_sub_dial(func='CLAR')
                if df_tx!=0:
                    df=df_tx
                else:
                    df=df_rx
                #print('SPLIT - Clarifier df=',df_rx,df_tx,df)
            else:
                df=0

            frq=(self.P.sock.get_freq(vfo) + df)*1e-3
                
            if frq>0 and np.abs(frq-fc)>=1e-3:
                print("\n%%%%%%%%% RIG_RETUNE: RIG Center Frq=",frq,'\tSDR frq=',fc,'\tVFO=',vfo)
                #print self.P.sock.freq,self.P.sock.mode,self.P.sock.connection
                self.FreqSelect(frq,False,vfo)
                
                mode = self.P.sock.get_fldigi_mode()
                rig_mode = self.P.sock.get_mode()
                if mode=='SSB' and (self.P.MODE=='LSB' or self.P.MODE=='USB'):
                    mode=self.P.MODE
                if len(mode)>0 and rig_mode!=mode:
                    self.P.sock.set_mode(mode)
                print('RIG_RETUNE: mode=',mode,'rig_mode=',rig_mode,'sdr_mode=',self.P.MODE)

        if self.follow_band_cb.isChecked():
            #print('RIG RETUNE - following rig band ...')
            if not self.P.sock.active:
                print('RIG_RETUNE 2: *** No connection to rig *** ')
                self.follow_band_cb.setChecked(False)
                return
            
            fc = self.lcd.get()
            f = self.P.sock.get_freq()*1e-3
            band = freq2band(1e-3*f)
            band2 = freq2band(1e-3*fc)
            if f>0 and band!=band2:
                mode = self.P.sock.get_fldigi_mode()
                if True:
                    frq=f
                elif self.P.PAN_BW == 0:
                    frq = (bands[b]["CW1"] + bands[b]["CW2"])/2
                else:
                    frq = bands[b]["CW1"] + self.P.PAN_BW/2000.
                    
                print('RIG_RETUNE: Follow band - rig band=',band,'\tSDR band=',band2,\
                      '\trig freq=',f,'\rnew SDR frq=',frq,'\trig mode=',mode)
                if self.so2v_cb.isChecked():
                    self.FreqSelect(frq,True,'B')             # Tune VFO B on rig also
                    self.P.sock.set_mode(mode,'B')
                else:
                    self.FreqSelect(frq,False)                # Only tune the SDR frq
                
                self.P.sock.set_mode(mode)
                print('mode=',mode,self.P.MODE)

        #vfo_out= self.P.sock.get_vfo()
        #print('RIG RETUNE out ... vfo_out=',vfo_out)
 
    # Function to set RF sampling rate
    def SrateSelect(self,i):
        a=self.srates[i].split(" ")
#        print '\n----------------- Srate Select -----------------',i,a,self.P.SRATE
        if i<0:

            # Set combo box according to current param setting
            if self.P.SRATE<1e6:
                #rate = int( self.P.SRATE/1e3 )
                rate = self.P.SRATE/1e3 
                if rate==int(rate):
                    rate=int(rate)
                s=str(rate)+" KHz"
            else:
                #rate = int( self.P.SRATE/1e6 )
                rate =  self.P.SRATE/1e6 
                if rate==int(rate):
                    rate=int(rate)
                s=str(rate)+" MHz"
            #print s
            idx=self.srates.index(s)
            self.srate_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            if a[1]=="KHz":
                #rate=int(a[0])*1e3
                rate = float(a[0])*1e3
            elif a[1]=="MHz":
                #rate=int(a[0])*1e6
                rate = float(a[0])*1e6
            self.P.SRATE=rate
#            print 'SRATE set to',rate,'\n'

            
    # Function to set IF Bandwidth
    def IF_BWSelect(self,i):
        print('\n----------------- IF BW Select -----------------',i,'\n')
        if i<0:

            # Set SDR BW according to input params
            if self.P.IF_BW>0:
                print('>>>>>>>>>>>>>> Changing SDR Bandwidth to',self.P.IF_BW) 
                self.P.sdr.setBandwidth(SOAPY_SDR_RX, 0,self.P.IF_BW)

            # Set combo box according to current SDR setting
            if self.P.MP_SCHEME==2:
                bw = self.mp_comm('getBandwidth')
            else:
                bw = self.P.sdr.getBandwidth(SOAPY_SDR_RX, 0)
            print('bw=',bw)
            if bw>=1e6:
                bw2 = bw/1e6
                tag=' MHz'
            else:
                bw2 = bw/1e3
                tag=' KHz'
            if bw2==int(bw2):
                bw2=int(bw2)
            s = str(bw2) + tag
            idx=self.bws.index(s)
            print(s)
            print(self.bws)
            print(idx)
            self.BW_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            a=self.bws[i].split(" ")
            if a[1]=="KHz":
                bw=float(a[0])*1e3
            elif a[1]=="MHz":
                bw=float(a[0])*1e6
            self.P.IF_BW = int(bw)
            print('<<<<<<<<<<<< Changing SDR Bandwidth to',bw)
            self.P.sdr.setBandwidth(SOAPY_SDR_RX, 0,self.P.IF_BW)
            
    # Function to set IF 
    def IFSelect(self,i):
        # print '\n----------------- hey -----------------',i,a,self.P.IF,'\n'
        if i<0:

            # Set combo box according to current param setting
            s=str(self.P.IF)+" KHz"
            # print s
            idx=self.IFs.index(s)
            self.IF_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            a=self.IFs[i].split(" ")
            self.P.IF = int(a[0])*1e3

            
    # Function to set Pan adaptor BW
    def PanBWSelect(self,i):
        print('\n----------------- Pan BW Select -----------------',i,'\n')
        if i<0:
            try:
                bw = int( self.P.PAN_BW*1e-3 ) 
                idx=self.PanBWs.index(str(bw)+' KHz')
                bw = int( self.P.PAN_BW ) 
            except ValueError:
                bw = int( self.P.PAN_BW ) 
                #print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! PanBW Select - special",i,bw,'\n')
                idx = len(self.PanBWs)-1
                #idx = 0
        else:
            a=self.PanBWs[i].split(" ")
            try:
                bw = int(a[0])
                if a[1]=="KHz":
                    bw *= 1e3 
                elif a[1]=="MHz":
                    bw *= 1e6
            except:
                bw = self.P.AF_BW
            idx=i
            
        self.PanBW_cb.setCurrentIndex(idx)
        self.P.PAN_BW = bw
            
        print("Pan BW select:",i,idx,bw, self.P.PAN_BW)
            
    # Function to set min peak distance
    def PeakDistSelect(self,i):
        print('\n----------------- Peak Distance Select -----------------',i,'\n')
        if i<0:
            try:
                bw = int( self.P.PEAK_DIST*1E-3 ) 
                idx=self.PeakDists.index(str(bw)+' KHz')
                bw = int( self.P.PEAK_DIST ) 
            except ValueError:
                idx = len(self.PeakDists)-1
                #idx = 0
        else:
            a=self.PeakDists[i].split(" ")
            bw = int(a[0])
            if a[1]=="KHz":
                bw *= 1e3 
            elif a[1]=="MHz":
                bw *= 1e6
            idx=i
            
        self.PeakDist_cb.setCurrentIndex(idx)
        self.P.PEAK_DIST = bw
        print("Peak Dist select:",i,idx,bw, self.P.PEAK_DIST)
            
    # Function to set Pan adaptor Direction
    def PanDirSelect(self,i):
        #print '\n----------------- hey -----------------',i,'\n'
        self.P.PAN_DIR = self.PanDirs[i]
        print(self.P.PAN_DIR)
            
    # Function to set Pan adaptor Dyn Range
    def PanDRSelect(self,i):
        #print '\n----------------- hey -----------------',i,'\n'
        if i<0:
            #self.P.PAN_DR = 50
            idx=self.PanDRs.index( str(self.P.PAN_DR) )
            self.PanDR_cb.setCurrentIndex(idx)
        else:
            self.P.PAN_DR = int( self.PanDRs[i] )
            #print idx,self.P.PAN_DR
            
    # Function to set tuning step
    def StepSelect(self,i):
        if isinstance(i, str):
            a = i.split(" ")
            idx = self.steps.index( i )
            self.step_cb.setCurrentIndex(idx)
        else:
            a=self.steps[i].split(" ")
        step = int(a[0])
        print("Step select:",i,step)
        if a[1]=="Hz":
            step=step*1e-3
        elif a[1]=="MHz":
            step=step*1e3
        elif a[1]=="GHz":
            step=step*1e6
        print('GUI STEP SELECT - Need some help!')

    # Function to select Vidio Bandwidth
    def Video_BWSelect(self,i):
        print("\n%%%%%%%%%%%%%%%% Video_BW Select:",i,self.P.VIDEO_BW)

        if i<0:
            try:
                if self.P.VIDEO_BW>1e6-1:
                    bw = int( self.P.VIDEO_BW*1e-6 )
                    idx=self.video_bws.index(str(bw)+' MHz')
                else:
                    bw = int( self.P.VIDEO_BW*1e-3 )
                    idx=self.video_bws.index(str(bw)+' KHz')
            except ValueError:
                print("special")
                idx = len(self.video_bws)-1
                
        elif i==0 and self.P.NEW_MODE=='IQ':

            # Max - find highest supported by sampling rate
            best_bw = find_filter( self.P.FS_OUT , VIDEO_BWs )
            idx=self.video_bws.index(best_bw)
            
        else:
            idx = i
                
        print("Video BW select:",i,idx,self.video_bws[idx],self.P.MODE,self.P.NEW_MODE)
        self.vidbw_cb.setCurrentIndex(idx)
        self.P.VIDEO_FILTER_NUM = idx

        if (not self.P.MODE_CHANGE and (self.P.MODE=='WFM' or self.P.MODE=='WFM2')) or \
            (self.P.MODE_CHANGE and (self.P.NEW_MODE=='WFM' or self.P.NEW_MODE=='WFM2')):

            # BCB FM is wideband so we need to demodulate first before resampling
            self.P.rx[0].demod.wfm_video.h = self.P.rx[0].demod.wfm_filter_bank[idx]
            #print idx,i,self.P.VIDEO_BW

        else:

            # For narrowband modes, resampling is applied to SDR data
            if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
                self.mp_comm('setVideoFilter',idx)
            else:
                self.P.rx[0].dec.h = self.P.rx[0].dec.filter_bank[idx]


    # Function to select Audio Bandwidth
    def AF_BWSelect(self,i):
        print("\n%%%%%%%%%%%%%%%% AF_BW Select:",i,self.P.AF_BW)

        if i<0:
            try:
                if self.P.AF_BW<1e3:
                    bw = int( self.P.AF_BW ) 
                    idx=self.af_bws.index(str(bw)+' Hz')
                else:
                    bw = int( self.P.AF_BW*1e-3 ) 
                    idx=self.af_bws.index(str(bw)+' KHz')
            except ValueError:
                print("special")
                #idx = len(self.af_bws)-1
                idx = 0
                
        elif i==0 and self.P.NEW_MODE=='IQ':

            # Max - find highest supported by sampling rate
            best_bw = find_filter( self.P.FS_OUT , AF_BWs )
            idx=self.af_bws.index(best_bw)
            a=self.af_bws[idx].split(" ")
            bw = int(a[0])
            
        else:
            a=self.af_bws[i].split(" ")
            if a[0]=='Max':
                bw=0
                idx=0
            else:
                bw = int(a[0])
                if a[1]=="KHz":
                    bw *= 1e3 
                elif a[1]=="MHz":
                    bw *= 1e6
                idx=i
                
        print("AF BW select:",i,idx,bw)
        self.afbw_cb.setCurrentIndex(idx)
        self.P.AF_BW = bw
        self.P.AF_FILTER_NUM = idx

        # For BCB FM, the audio filtering is done in the resampler
        if (not self.P.MODE_CHANGE and (self.P.MODE=='WFM' or self.P.MODE=='WFM2')) or \
            (self.P.MODE_CHANGE and (self.P.NEW_MODE=='WFM' or self.P.NEW_MODE=='WFM2')):
            self.P.rx[0].dec.h = self.P.rx[0].dec.filter_bank[i]

        if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
            self.mp_comm('setAudioFilter',bw,idx)
            

    # Callback to change center freq when clicked 
    def MouseClickRF(self,button,frq,y,fc):
        print('MouseClickRF in:',button,frq,y,self.P.PSD_AF_FC2,fc)
        if self.P.TRANSPOSE:
            frq,y = y,frq
        
        # Make sure we include center freq if it is not already part of the plot
        #if self.P.PSD_AF_FC2==0:
        if fc==0:
            frq += .001*self.P.FC[self.P.PLOT_RX]
        print('MouseClickRF:',button,frq)
        vfo='A'        # Make sure this is set

        # Check if we've clicked on a spot
        fields=None
        if self.P.BANDMAP:
            if y>100:
                dfbest=1e9
                ibest=-1
                idx=0
                for spot in self.Spots:
                    df=abs( spot.freq-frq )
                    if df<dfbest:
                        dfbest=df
                        ibest=idx
                    idx=idx+1
                spot=self.Spots[ibest]
                print('MouseClickRF: Looks like a spot click -',spot.call,spot.freq,spot.color)
                frq=spot.freq
                call=spot.call
                fields = {'Call':call}
            else:
                call=''
            
        if button==1:

            # Left click - What we do depends on how SDR is being used
            if self.P.RIG_IF==0 or True:
                
                # Left click as an SDR - shift SDR & Rig center freq
                print("\tLeft button - Setting SDR freq to",frq)
                vfo='A'                           # VFO A always follows left click
                self.FreqSelect(frq,True,vfo)
                
            else:
                
                # Left click with SDR listening to a rig's IF - shift rig freq
                print("\tLeft button - Setting Rig Freq",frq)
                vfo='A'
                self.P.sock.set_freq(float(frq),vfo)
            
        elif button==2:

            # Right click with 2 RX's - shift freq of VFO B
            if self.P.NUM_RX==2:

                new_frq=[0,0]
                irx=self.P.MAIN_RX
                new_frq[irx]   = .001*self.P.FC[irx]
                new_frq[1-irx] = frq
                print('MouseClickRF: Right click - irx/frq/new_frq=',irx,frq,new_frq)
                self.FreqSelect(new_frq,True)
                
            # Right click and using SO2V - set rig center freq for VFO A
            # Let's see how this works - it might be more intuitive to swap roles of L & R buttons for SO2V
            # since l & R ears will be listening to rig & sdr respectively
            # If we decide to change this, also change 'B' to 'A' above under button 1
            elif self.so2v_cb.isChecked():

                # SO2V - Set rig VFO B
                #vfo='A'
                vfo='B'
                print("MouseClickRF: Right click - Setting Rig Freq",\
                      frq,'\tVFO=',vfo)
                self.P.sock.set_freq(float(frq),vfo)

            elif self.split_cb.isChecked():
                
                # DX split - Adjust Clarifier
                frq1 = self.P.sock.get_freq()*1e-3
                df = frq-frq1
                print("Right button - Setting Split",frq,frq1,df)
                SetTXSplit(self.P,df)

                # Also tune SDR to pile-up so we can listen to it
                #vfo='A'
                vfo='B'
                #print("Right button - Freq Select ...",frq,True,vfo)
                self.FreqSelect(frq,True,vfo)
                
        elif button==4:

            # Middle button with 2 RXs or SO2V - swap rig VFOs
            if self.P.NUM_RX==2 or self.so2v_cb.isChecked():
                rig_vfo = self.P.sock.get_vfo()
                if rig_vfo[0]=='A':
                    new_vfo='B'
                elif rig_vfo[0]=='B':
                    new_vfo='A'
                elif rig_vfo[0]=='M':
                    new_vfo='S'
                elif rig_vfo[0]=='S':
                    new_vfo='M'
                else:
                    print('MouseClickRF: Middle button - unknown rig vfo????',rig_vfo)
                    return
                
                print('MouseClickRF: Middle button - changing vfo from',\
                      rig_vfo,' to ',new_vfo)
                self.P.sock.set_vfo(new_vfo)

                # Debug only
                if False:
                    new_vfo = self.P.sock.get_vfo()
                    print('MouseClickRF: Old vfo=',rig_vfo,'\tNew vfo=',new_vfo)
                
            else:
                print("MouseClickRF: Middle button - TBD")

        # Send spot info to keyer
        if self.P.BANDMAP and self.P.udp_client:
            print('Sending CALL to UDP Client...',call)
            self.P.udp_client.Send('Call:'+call+':'+vfo)

        # Send spot to FLDIGI also - RTTY op
        if fields and self.P.sock.fldigi_active:
            print('Sending info to FLDIGI ...',fields)
            self.P.sock.set_log_fields(fields)
            
                
    # Callback to change center freq
    def FreqSelect(self,new_frq,tune_rig=True,VFO=[]):
        P = self.P
        print('&&&&&&&&&&&&&&&&&& RX UPDATE FREQ &&&&&&&&&&&&&&&&',P.FC,new_frq,VFO,tune_rig)

        # If SO2V and VFO A or SDR is listening to rig's IF, only change rig freq
        if P.RIG_IF!=0 or (self.so2v_cb.isChecked() and VFO=='A'):
            #print 'Howdy Ho!'
            vfo='A'
            if new_frq>0:
                print('@@@@@@@@@@@@ Tuning rig only',new_frq,vfo)
                P.sock.set_freq(float(new_frq),vfo)
                P.frqArx = new_frq
                self.itune_cnt=0
            return
        
        # Tuning offset
        foff = -P.FOFFSET

        # Manage Main RX
        irx=P.MAIN_RX
        if np.isscalar(new_frq):
            f2 = new_frq*1000.
        else:
            f2 = new_frq[irx]*1000.
        if f2>0:
            if P.REPLAY_MODE:
                print('Changing',P.REPLAY_FC,f2,P.FOFFSET)
                P.FOFFSET = P.lo.change_freq( P.REPLAY_FC-f2 + 0*P.BFO )
                print('Replay mode:',P.FOFFSET)
            else:
                if P.MP_SCHEME==2:
                    #f1 = self.mp_comm('getFrequency') + P.FOFFSET
                    self.mp_comm('setFrequency',0,foff,f2-P.FOFFSET)
                elif P.MP_SCHEME==3:
                    self.mp_comm('setFrequency',foff,rx=0)
                    P.sdr.setFrequency(SOAPY_SDR_RX, 0, f2-P.FOFFSET)
                else:
                    #f1 = P.sdr.getFrequency(SOAPY_SDR_RX, 0) + P.FOFFSET
                    P.rx[irx].lo.change_freq( foff )
                    P.sdr.setFrequency(SOAPY_SDR_RX, 0, f2-P.FOFFSET)
                print('\tChanging Main-RX',irx,' freq from',P.FC[irx],' to ',f2)
            P.FC[irx]  = f2

            # Re-tune rig also - NEW!!!
            # Need to make into a function!!!
            if tune_rig and (self.follow_freq_cb.isChecked() or
                             self.so2v_cb.isChecked() ):
                # Keep track of current rig vfo
                rig_vfo = P.sock.get_vfo()
                print('Current rig vfo=',rig_vfo)

                # Tune the rig
                if len(VFO)==0:
                    vfo='A'
                    if self.so2v_cb.isChecked():
                        vfo='B'
                else:
                    vfo=VFO
                print('&&&&&&&&&&&& Tuning rig',f2,vfo)
                P.sock.set_freq(.001*f2,vfo)
                self.itune_cnt=0

                mode = P.MODE
                rig_mode = P.sock.get_mode(vfo)
                #if mode=='SSB' and (self.P.MODE=='LSB' or self.P.MODE=='USB'):
                #    mode=self.P.MODE
                print('SDR & RIG MODES:',mode,rig_mode,vfo)
                if rig_mode!=mode and mode!='IQ':
                    P.sock.set_mode(mode,vfo)

                # Restore vfo
                if rig_vfo[0]!=vfo:
                    P.sock.set_vfo(rig_vfo[0])

        # NOT SURE WHY THIS IS STILL HERE? Perhaps for FT8 hopper?
        #if P.FT8 and new_frq[0]>0:
        #    band = convert_freq2band(new_frq[0],True)
        #    new_frq[1] = bands[band]['FT8']
        #    print('band=',band,new_frq[0],new_frq[1])

        # Manage sub-RX(s)
        for i in range(0,P.NUM_RX):
            if i==P.MAIN_RX:
                # Main RX has already been taken care of
                continue
            #elif P.MAIN_RX==0 and not np.isscalar(new_frq):
            elif not np.isscalar(new_frq):
                # New freq for this rx
                f3=1000*new_frq[i]
            else:
                # Keep same freq on this rx - still need to do this bx offset is changed when tuning main rx
                f3=P.FC[i]
            if f3>0:
                if P.SOURCE[i]>=0:
                    frq = P.FC[P.SOURCE[i]] - f3
                else:
                    frq = foff + f2 - f3
                if P.MP_SCHEME==2 or P.MP_SCHEME==3:
                    self.mp_comm('setFrequency', i,frq,rx=i)
                else:
                    P.rx[i].lo.change_freq( frq )
                    print('\tChanging Sub-RX',i,' freq from',P.FC[i],' to ',f3)
                P.FC[i] = f3

                # Re-tune rig also - NEW!!!
                if tune_rig and self.follow_freq_cb.isChecked():
                    vfo='B'
                    print('\n&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& Tuning rig to frq/vfo=',f3,vfo,'\n')
                    P.sock.set_freq(.001*f3,vfo)
                    self.itune_cnt=0

                    mode = P.MODE
                    rig_mode = P.sock.get_mode(vfo)
                    #if mode=='SSB' and (self.P.MODE=='LSB' or self.P.MODE=='USB'):
                    #    print('SDR & RIG MODES:',mode,rig_mode,vfo)
                    if rig_mode!=mode:
                        P.sock.set_mode(mode,vfo)

                    # Restore vfo
                    if rig_vfo[0]!=vfo:
                        P.sock.set_vfo(rig_vfo[0])

                    

        # Manage GUI LCD display
        if f2>0:
            self.lcd.set(.001*f2)
            P.BAND = freq2band(1e-6*f2)
            for i in range(P.NUM_RX):
                self.rx_frq_box[i].setText( "{0:,.1f} KHz".format(.001*P.FC[i]) )

    # Function to set demod mode
    def ModeSelect(self,idx):
        # If SDR is listening to rig's IF, only change rig freq
        if self.P.RIG_IF!=0 and idx>=0 and False:
            vfo='A'
            txt=self.modes[idx]
            print('@@@@@@@@@@@@ Changing rig mode',txt,vfo,idx)
            self.P.sock.set_mode(txt)
            #self.itune_cnt=0
            return

        # Some modes require the SDR to be set to something else
        if self.P.MODE=='RTTY2' or self.P.MODE=='PKTUSB':
            self.P.MODE='IQ'
        elif self.P.MODE=='FM':
            self.P.MODE='NFM'
            
        if idx<0:
            idx=self.modes.index(self.P.MODE)
        txt=self.modes[idx]

        self.P.NEW_MODE=txt
        self.P.MODE_CHANGE = (self.P.MODE != txt)
        print("Mode select:",idx,txt,self.P.MODE_CHANGE) 
        self.mode_cb.setCurrentIndex(idx)

        if self.P.ENABLE_RTTY:
            if self.P.NEW_MODE == 'RTTY' and not self.rtty.active:
                # Show
                self.rtty.start()
            elif self.P.NEW_MODE != 'RTTY' and self.rtty.active:
                # Hide
                self.rtty.stop()

        if self.P.MP_SCHEME==2 or self.P.MP_SCHEME==3:
            self.mp_comm('setMode',self.P.NEW_MODE)
            self.P.MODE        = self.P.NEW_MODE
            self.P.MODE_CHANGE = False

        
    # Set presets
    def PresetSelect(self,frq,mode,vidbw,afbw):
        print("\n@@@@ Preset:",frq,mode,vidbw,afbw)
        print('modes=',self.modes)
        if mode in ['PKTUSB','PKT-U']:
            mode='USB'
        
        #new_frq=np.zeros(self.P.NUM_RX)
        new_frq=self.P.FC*1e-3
        new_frq[0]=frq
        self.FreqSelect(new_frq)
        if self.P.RIG_IF==0:
            idx=self.modes.index(mode)
            self.ModeSelect(idx)
            idx=self.video_bws.index(vidbw)
            self.Video_BWSelect(idx)
            idx=self.af_bws.index(afbw)
            self.AF_BWSelect(idx)
            self.rig_retune()
        else:
            vfo='A'
            print('@@@@@@@@@@@@ Changing rig mode',mode,vfo)
            self.P.sock.set_mode(mode)
            #self.itune_cnt=0
            return

        # Check if we need to change RTL direct sampling mode
        if self.P.SDR_TYPE=='rtlsdr' and False:
            thresh=30e3
            if frq>=thresh and self.P.DIRECT_SAMP!=0:
                self.DirectSelect(0)
            elif frq<thresh and self.P.DIRECT_SAMP!=2:
                self.DirectSelect(2)


    # Callback to enable/disable AM/FM BCB Notch
    def EnableBCBnotch(self):

        # Check how the SDR says its set
        s="rfnotch_ctrl"
        if self.P.MP_SCHEME==2:
            notch = self.mp_comm('readSetting',s)
        else:
            notch = self.P.sdr.readSetting(s)
        print('Current notch=',notch)

        if notch=='true':
            self.BCB_btn.setText('Enable')
            self.P.sdr.writeSetting(s,"false")
        else:
            self.BCB_btn.setText('Disable')
            self.P.sdr.writeSetting(s,"true")


    # Callback to Mute/Unmute Audio
    def MuteCB(self,irx,Reset=False):

        print('MUTE CB: irx=',irx,'\tReset=',Reset,'\tMUTED=',self.P.MUTED[irx])
        #print irx,self.Mute_btns[irx].text()
        #print irx,self.Mute_btns[irx].isChecked()

        if Reset:
            self.Mute_btns[irx].setChecked(self.P.MUTED[irx])
        else:
            self.P.MUTED[irx] = not self.P.MUTED[irx]
            
        if self.P.MUTED[irx]:
            self.Mute_btns[irx].setText('Un-Mute RX'+str(irx+1))
        else:
            self.Mute_btns[irx].setText('Mute RX'+str(irx+1))

    # Select Antenna
    def AntSelect(self,i):
        print("\nAntenna Select:",i)

        s1="ant_sel"
        s2="amport_ctrl"
        if i<0:

            # Set combo box according to current param setting
            if not self.P.REPLAY_MODE:
                if self.P.MP_SCHEME==2:
                    ant1 = self.mp_comm('getAntenna')
                else:
                    ant1 = self.P.sdr.getAntenna(SOAPY_SDR_RX, 0)
                print('Current ant=',ant1)
                if ant1=='Antenna A':
                    ant = 'Ant A'
                else:
                    ant = 'Ant B'
                idx=self.Antennas.index(ant)
                print(idx)
            else:
                idx=0
            self.Ant_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            ant = self.Antennas[i] 
            print('>>>>>>>>>>>>>> Changing SDR Antenna to',ant)
            if not self.P.REPLAY_MODE:
                if ant=='Ant A':
                    ant1='Antenna A'
                elif ant=='Ant B':
                    ant1='Antenna B'
                else:
                    ant1='Hi-Z'
                if self.P.MP_SCHEME==2:
                    self.mp_comm('setAntenna',ant1)
                else:
                    self.P.sdr.setAntenna(SOAPY_SDR_RX, 0,ant1)
                    
        #print(' ')
                    

    # Set LNA (aka RF gain)
    def LNASelect(self,i):
        print("\nLNASelect:",i)

        s="rfgain_sel"
        if i<0:

            # Set combo box according to current param setting
            if not self.P.REPLAY_MODE:
                if self.P.MP_SCHEME==2:
                    gain = self.mp_comm('readSetting',s)
                else:
                    gain = self.P.sdr.readSetting(s)
                print('Current gain=',gain)
                print(self.RFgains)
                idx=self.RFgains.index(str(gain))
            else:
                idx=0
                
            self.RFgain_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            if not self.P.REPLAY_MODE:
                gain = int( self.RFgains[i] )
                print('>>>>>>>>>>>>>> Changing SDR LNA to',gain)
                if self.P.MP_SCHEME==2:
                    self.mp_comm('writeSetting',s,str(i))
                else:
                    self.P.sdr.writeSetting(s,str(i))
        


    # Set direct sampling mode
    def DirectSelect(self,i):
        print("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ DirectSelect:",i)

        s="direct_samp"
        if i<0:

            # Set combo box according to current param setting
            direct = self.P.sdr.readSetting(s)
            print('Current direct samp =',direct)
            print(self.direct)
                
        else:
                
            # Set current param setting according to combo box 
            direct = int( self.direct[i] )
            print('>>>>>>>>>>>>>> Changing direct samp to',direct,i,self.P.DIRECT_SAMP)
            if self.P.MP_SCHEME==2:
                self.mp_comm('writeSetting',s,str(i))
            else:
                self.P.sdr.writeSetting(s,str(i))
            self.P.DIRECT_SAMP=direct

        idx=self.direct.index(str(direct))
        self.direct_cb.setCurrentIndex(idx)

    # Set IF gain
    def IFGainSelect(self,i):
        #print "\nIFGainSelect:",i

        if self.P.REPLAY_MODE:
            gain=1
            self.IFgain_cb.setCurrentIndex(0)
        
        elif i<0:

            # Set combo box according to current param setting
            if self.P.SDR_TYPE=='sdrplay':
                stage='IFGR'
            elif self.P.SDR_TYPE=='rtlsdr':
                stage='TUNER'
            print('Reading SDRPlay IF gain...',stage)
            if self.P.MP_SCHEME==2:
                gain = self.mp_comm('getGain',stage)
            else:
                gain = self.P.sdr.getGain(SOAPY_SDR_RX, 0,stage)
            print('gain=',gain)
            if self.P.SDR_TYPE=='sdrplay':
                if gain==0:
                    gain=float(self.IFgains[0])
                print('gain=',gain)
                s=str( int(gain+0.5) )
            elif self.P.SDR_TYPE=='rtlsdr':
                if gain>49.6:
                    gain=49.6
                elif gain<0.:
                    gain=0.
                s=str( int(gain/self.dgain)*self.dgain )
            else:
                gain=1
                s='1'
                
            print('gain=',s)
            print('Current gain=',gain,s)
            print('Available gains:',self.IFgains)
            try:
                idx=self.IFgains.index(s)
            except:
                idx=0
            self.IFgain_cb.setCurrentIndex(idx)
                
        else:
                
            # Set current param setting according to combo box 
            if self.P.SDR_TYPE=='sdrplay':
                stage='IFGR'
                gain = int( self.IFgains[i] )
            elif self.P.SDR_TYPE=='rtlsdr':
                stage='TUNER'
                gain = float( self.IFgains[i] )
            else:
                gain=1
                
            if self.P.MP_SCHEME==2:
                self.mp_comm('setGain',stage,gain)
            else:
                self.P.sdr.setGain(SOAPY_SDR_RX, 0,stage,gain)
            print('>>>>>>>>>>>>>> Changing SDR IF Gain to',gain)
        
    def mp_comm(self,cmd,arg1='',arg2='',arg3='',rx=None):
        if self.P.MP_SCHEME==2:
            self.P.pipe.send(('CMD',cmd,arg1,arg2,arg3))
            msg = self.P.pipe.recv()
            return msg[1]
        
        elif self.P.MP_SCHEME==3:
            if not rx:
                rxs = list(range(self.P.NUM_RX))
            else:
                rxs = [rx]
            print('MP_COMM:',rx,rxs)
            for irx in rxs:
                print('MP_COMM: Sending',irx,('CMD',cmd,arg1,arg2,arg3),rx)
                self.P.pipe[irx].send(('CMD',cmd,arg1,arg2,arg3))
                print('MP_COMM: Waiting for response',irx)
                msg = self.P.pipe[irx].recv()
                print('MP_COMM: Got',msg)
                if rx!=None:
                    return msg[1]
                
            return None
        

