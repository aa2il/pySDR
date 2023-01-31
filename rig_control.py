################################################################################
#
# rig_control.py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Portion of GUI related to rig controls - Qt version
#
# To Do:  There are a couple of versions of this module floating around -
#         need to combine them.
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
################################################################################

if False:
    # use Qt4 
    from PyQt4.QtCore import * 
else:
    # use Qt5
    from PyQt5.QtCore import * 
    from PyQt5.QtWidgets import *
from rig_io.socket_io import *
from utilities import freq2band

################################################################################

class RIG_CONTROL():
    def __init__(self,parent,P,new_tab=True):
        self.P    = P
        self.sock = P.sock
        self.sock1 = P.sock1
        if self.sock.connection == 'NONE':
            return None

        # Create a new tab or window
        self.tab1 = QWidget()
        if new_tab:
            parent.addTab(self.tab1,'Rig Ctrl')
            self.visible = True
        else:
            self.tab1.hide()
            self.visible = False
            #self.tab1.resize( 1000,1000 )
            self.tab1.setWindowTitle("Rig Control")
        grid = QGridLayout()
        self.tab1.setLayout(grid)
            
        # Create buttons to select operating band
        row=0
        col=1
        band_group=QButtonGroup(self.tab1)
        lab = QLabel("Band:")
        grid.addWidget(lab,row,0)
        self.band_buttons={};
        #bb = str( self.sock.get_band() )+'m'
        f = self.P.sock.get_freq()*1e-6
        bb = freq2band(f)
        print('bb=',bb)

        ALL_BANDS=CONTEST_BANDS + NON_CONTEST_BANDS
        if self.P.sock.rig_type2=='FT991a':
            ALL_BANDS.append('2m')
            ALL_BANDS.append('70cm')
        
        for b in ALL_BANDS:
            if b=='60m':
                row+=1
                col =1
            self.band_buttons[b] = QRadioButton(b)
            if b==bb:
                self.band_buttons[bb].setChecked(True)
            self.band_buttons[b].toggled.connect(self.bandCB)
            band_group.addButton(self.band_buttons[b])
            grid.addWidget(self.band_buttons[b] ,row,col)
            col += 1

        # Create buttons to select mode
        row += 1
        col  = 1
        mode_group=QButtonGroup(self.tab1)
        lab = QLabel("Mode:")
        grid.addWidget(lab,row,0)
        self.mode_buttons={};
        for m in FTDX_MODES2:
            self.mode_buttons[m] = QRadioButton(m)
            self.mode_buttons[m].toggled.connect(self.modeCB)
            mode_group.addButton(self.mode_buttons[m])
            grid.addWidget(self.mode_buttons[m] ,row,col)
            col += 1

        # Create buttons to select antenna
        if self.P.sock.rig_type2=='FTdx3000':
            row += 1
            col  = 1
            lab = QLabel("Antenna:")
            grid.addWidget(lab,row,0)
            self.ant_buttons={};
            for a in FTDX_ANTENNAS:
                self.ant_buttons[a] = QRadioButton(a)
                self.ant_buttons[a].toggled.connect(self.antCB)
                grid.addWidget(self.ant_buttons[a] ,row,col)
                col += 1

        # Slider to adjust output power
        row += 1
        col  = 0
        ncol=5
        lab = QLabel("TX Power:")
        grid.addWidget(lab,row,0)
        self.pwr_slider = QSlider(Qt.Horizontal)
        self.pwr_slider.setMinimum(5)
        self.pwr_slider.setMaximum(100)
        self.pwr_slider.setTickPosition(QSlider.TicksBelow)
        self.pwr_slider.setTickInterval(25)
        self.pwr_slider.valueChanged.connect(self.powerCB)
        grid.addWidget(self.pwr_slider,row,1,1,ncol-1)
        self.pwr_txt = QLineEdit()
        grid.addWidget(self.pwr_txt,row,ncol)
        
        # Slider to adjust mic gain
        row += 1
        col  = 0
        lab = QLabel("Mic Gain:")
        grid.addWidget(lab,row,0)
        self.mic_slider = QSlider(Qt.Horizontal)
        self.mic_slider.setMinimum(0)
        self.mic_slider.setMaximum(100)
        self.mic_slider.setValue(20)
        self.mic_slider.setTickPosition(QSlider.TicksBelow)
        self.mic_slider.setTickInterval(25)
        self.mic_slider.valueChanged.connect(self.gainCB)
        grid.addWidget(self.mic_slider,row,1,1,ncol-1)
        self.mic_txt = QLineEdit()
        grid.addWidget(self.mic_txt,row,ncol)

        # Slider to adjust monitor level
        row += 1
        col  = 0
        lab = QLabel("Monitor:")
        grid.addWidget(lab,row,0)
        self.mon_slider = QSlider(Qt.Horizontal)
        self.mon_slider.setMinimum(0)
        self.mon_slider.setMaximum(100)
        self.mon_slider.setValue(30)
        self.mon_slider.setTickPosition(QSlider.TicksBelow)
        self.mon_slider.setTickInterval(25)
        self.mon_slider.valueChanged.connect(self.monitorCB)
        grid.addWidget(self.mon_slider,row,1,1,ncol-1)
        self.mon_txt = QLineEdit()
        grid.addWidget(self.mon_txt,row,ncol)

        # Misc buttons
        row += 1
        col  = 0
        self.btn1 = QPushButton('Contest Mode')
        self.btn1.setToolTip('Toggle Wide/Narrow Filters')
        self.btn1.setCheckable(True)
        self.btn1.clicked.connect(self.ToggleContestMode)
        grid.addWidget(self.btn1,row,col)
        
        col += 1
        self.btn2 = QPushButton('Reset Clarifier')
        self.btn2.setToolTip('Reset Clarifier')
        self.btn2.clicked.connect(lambda: ClarReset(self) )
        grid.addWidget(self.btn2,row,col)
        
        col += 1
        self.btn3 = QPushButton('<<')
        self.btn3.setToolTip('Lower sub-band edge')
        self.btn3.clicked.connect(lambda: SetSubBand(self,1) )
        grid.addWidget(self.btn3,row,col)
        
        col += 1
        self.btn4 = QPushButton('||')
        self.btn4.setToolTip('Middle of Lower sub-band')
        self.btn4.clicked.connect(lambda: SetSubBand(self,2) )
        grid.addWidget(self.btn4,row,col)
        
        col += 1
        self.btn5 = QPushButton('>>')
        self.btn5.setToolTip('Upper sub-band edge')
        self.btn5.clicked.connect(lambda: SetSubBand(self,3) )
        grid.addWidget(self.btn5,row,col)

        col += 1
        self.btn6 = QPushButton('Adjust Mic')
        self.btn6.setToolTip('Adjust Mic Gain')
        self.btn6.clicked.connect(lambda: Auto_Adjust_Mic_Gain(self) )
        grid.addWidget(self.btn6,row,col)
        
        # Buttons to manipulate VFO
        row += 1
        col  = 0
        self.btn10 = QPushButton('VFO A')
        self.btn10.setToolTip('VFO A')
        self.btn10.clicked.connect(lambda: SetVFO(self,'A') )
        grid.addWidget(self.btn10,row,col)

        col += 1
        self.btn11 = QPushButton('VFO B')
        self.btn11.setToolTip('VFO B')
        self.btn11.clicked.connect(lambda: SetVFO(self,'B') )
        grid.addWidget(self.btn11,row,col)

        col += 1
        self.btn12 = QPushButton('A->B')
        self.btn12.setToolTip('Copy A to B')
        self.btn12.clicked.connect(lambda: SetVFO(self,'A->B') )
        grid.addWidget(self.btn12,row,col)

        col += 1
        self.btn13 = QPushButton('B->A')
        self.btn13.setToolTip('Copy B to A')
        self.btn13.clicked.connect(lambda: SetVFO(self,'B->A') )
        grid.addWidget(self.btn13,row,col)

        col += 1
        self.btn14 = QPushButton('A<->B')
        self.btn14.setToolTip('Swap A&B')
        self.btn14.clicked.connect(lambda: SetVFO(self,'A<->B') )
        grid.addWidget(self.btn14,row,col)

        # Init rig controls
        self.rig_status()
        return

    # Routine to determine which of a group of radio buttons is clicked
    def clicked(self,rbs):
        #print 'RADIO BUTTONS:',rbs
        for b in rbs:
            #print b
            if rbs[b].isChecked():
                print(b+" is Checked")
                return b

        print('No buttons checked')
        return ''

    # Callback for band selection radio buttons group
    def bandCB(self):
        #print 'bandCB...'
        b = self.clicked(self.band_buttons)
        if b!=self.band:
            m = self.clicked(self.mode_buttons)
            if self.P.PANADAPTOR:
                df = self.P.PAN_BW/2000.
            else:
                df=0
            print('bandCB:  b=',b,'m=',m,'   df=',df)
            SelectBand(self,b,m,df)
            if self.sock.connection=='HAMLIB':
                # The rig can be slow to respond to changes so just assume it worked
                self.band = b
                self.band_buttons[self.band].setChecked(True)
            else:
                self.rig_status()

    # Callback for band selection radio buttons group
    def modeCB(self):
        m = self.clicked(self.mode_buttons)
        if m!=self.mode:
            b = self.clicked(self.band_buttons)
            SelectMode(self,b,m)
            self.band = b
            self.mode = m
        
    # Callback for antenna selection radio buttons group
    def antCB(self):
        a = self.clicked(self.ant_buttons)
        if a!=self.ant:
            SelectAnt(self,a[-1])
            self.ant = a
        
    # Function to read rig status and update control buttons accordingly
    def rig_status(self):
        print('RIG_STATUS: band=',self.sock.band,self.sock.band=='MW')
        if False:
            #self.band = str( self.sock.get_band() )+'m'
            f = self.P.sock.get_freq()*1e-6
            self.band = freq2band(f)
        else:
            if self.sock.band=='MW':
                self.band='160m'
            else:
                self.band = self.sock.band
        if self.band:
            self.band_buttons[self.band].setChecked(True)

        self.mode = self.sock.get_mode()
        print('RIG_STATUS: mode=',self.mode)
        if self.mode in ['PKT-U','PKTUSB','PSK-U']:
            self.mode='RTTY'
        elif self.mode in ['CWR','CW-U','CW-L']:
            self.mode='CW'
        elif self.mode=='SSB':
            #print('freq=',self.sock.freq)
            if self.sock.freq<10e6:
                self.mode='LSB'
            else:
                self.mode='USB'
        self.mode_buttons[self.mode].setChecked(True)

        self.ant = 'Ant'+ str( self.sock.get_ant() )
        #print( self.ant_buttons.keys() )
        if self.P.sock.rig_type2=='FTdx3000':
            self.ant_buttons[self.ant].setChecked(True)

        p = read_tx_pwr(self)
        self.pwr_slider.setValue(p)
        self.pwr_txt.setText( "{0:,d} W".format(p) )
        
        p = read_mic_gain(self)
        self.mic_slider.setValue(p)
        self.mic_txt.setText( "{0:,d}".format(p) )
        
        p = read_monitor_level(self)
        self.mon_slider.setValue(p)
        self.mon_txt.setText( "{0:,d}".format(p) )

        self.ContestMode=False
        
    # Callback for Contest Mode
    def ToggleContestMode(self):
        self.ContestMode = not self.ContestMode
        print("Content mode=",self.ContestMode)
        SetFilter(self)
    
    # Callback for tx power slider
    def powerCB(self):
        p = self.pwr_slider.value()
        set_tx_pwr(self,p)
        self.pwr_txt.setText( "{0:,d} W".format(p) )
        
    # Callback for mic gain slider
    def gainCB(self):
        p = self.mic_slider.value()
        set_mic_gain(self,p)
        self.mic_txt.setText( "{0:,d}".format(p) )
        
    # Callback for monitor level slider
    def monitorCB(self):
        p = self.mon_slider.value()
        set_mon_level(self,p)
        self.mon_txt.setText( "{0:,d}".format(p) )
        
        
