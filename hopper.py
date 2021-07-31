############################################################################
#
# hopper.py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Functions related to freqeuncy hopping
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

from collections import OrderedDict
import csv
import xlrd
from unidecode import unidecode
import sys
import datetime
import time
from support import adjust_foffset,expand_ft4

from dx.wsjt_helper import WSJT_LOGFILE3,WSJT_LOGFILE4,WSJT_LOGFILE5
import os
import numpy as np
from rig_io.util import convert_freq2band
from rig_io.ft_tables import bands

from PyQt5.QtCore import QTimer

############################################################################

PRESETS_FNAME = 'data/presets.xls'

############################################################################

# Freq Hopping
class FreqHopper:
    def __init__(self,P):

        print('\n((((((((((((( FREQ HOPPER )))))))))))))))))))')
        self.P = P
        self.hop_idx  = 0

        if P.HOPPER:
            if len(P.HOP_LIST)==0:
                self.use_pattern = True
                self.hop_pattern = self.read_hop_pattern(P.FT4)
                P.HOP_LIST=[P.FC[0]]    # We need something here
            else:
                self.use_pattern = False
            self.Hopper()            # Init hop list according to current time

        self.align_clock()
        #time.sleep(1.)               # Add a delay so ALL.TXT freqs will be correct

        self.timer = QTimer()
        self.timer.timeout.connect(self.Hopper)
        self.timer.start(P.HOP_TIME*1000)

    # Function to read hop pattern from a spreadsheet
    def read_hop_pattern(self,Expand_FT4):
        pattern = OrderedDict()

        book  = xlrd.open_workbook(PRESETS_FNAME,formatting_info=True)
        sheet2 = book.sheet_by_name('Hops')

        for i in range(1, sheet2.nrows):
            row=[]
            for j in range(0, sheet2.ncols):
                cell = sheet2.cell(i, j).value
                if cell!='':
                    row.append( float( cell ) )
            pattern[row[0]] = row[1:]
            #print i,row

        # Make sure log files exist
        for fname in [WSJT_LOGFILE3,WSJT_LOGFILE4,WSJT_LOGFILE5]:
            if not os.path.isfile(fname):
                open(fname, 'a').close()

        # Monitor FT8 decodes
        self.sz3 = os.path.getsize(WSJT_LOGFILE3)
        self.sz4 = os.path.getsize(WSJT_LOGFILE4)
        self.sz5 = os.path.getsize(WSJT_LOGFILE5)
        print(WSJT_LOGFILE3,self.sz3,self.sz4,self.sz5)

        # Add FT4 sub-bands also
        if Expand_FT4 and False:
            for key in list(pattern.keys()):
                print(key,pattern[key])
                pattern[key] = expand_ft4( pattern[key] )
                print(pattern[key])
                print(' ')
            #sys.exit(0)
            
        return pattern


    # Function to change SDR center freq
    def Hopper(self):

        P=self.P
        nfrqs = len(P.HOP_LIST)
        if P.FT4:
            NUM_RX = int( P.NUM_RX/2 )
        elif P.FT44:
            NUM_RX = P.NUM_RX-1
        else:
            NUM_RX = P.NUM_RX
            
        t = datetime.datetime.now()
        if self.use_pattern and self.hop_idx==0:
            P.HOP_LIST = self.hop_pattern[ t.hour ]
            nfrqs = len(P.HOP_LIST)
            print('------ HOP PATTERN:',P.HOP_LIST,self.hop_idx,nfrqs)

        else:
            sz3 = os.path.getsize(WSJT_LOGFILE3)
            sz4 = os.path.getsize(WSJT_LOGFILE4)
            sz5 = os.path.getsize(WSJT_LOGFILE5)
            print(WSJT_LOGFILE3,sz3-self.sz3,sz4-self.sz4,sz5-self.sz5)

        # Set new frqs 
        print('------ HOPPING1:',self.hop_idx,NUM_RX,P.NUM_RX)
        if self.hop_idx+NUM_RX>nfrqs:
            self.hop_idx=nfrqs - NUM_RX
        #print('------ HOPPING2:',self.hop_idx)
        fc  = []
        for i in range(NUM_RX):
            fc.append( P.HOP_LIST[self.hop_idx+i]*1e3 )
        self.hop_idx = (self.hop_idx+NUM_RX) % nfrqs

        if P.NUM_RX>=2:
            fo = 0.5*( max(fc)+min(fc) )
            P.FOFFSET = fo-max(fc)
            adjust_foffset(P)
            print('New FOFFSET=',P.FOFFSET)

        #print '------ HOPPING3:',self.hop_idx,nfrqs
        P.FREQ_CHANGE=True
        if P.FT4:
            P.NEW_FREQ=expand_ft4( np.array(fc)*1e-3 )*1e3
        elif P.FT44 and NUM_RX==3:
            b = convert_freq2band(np.array(fc)*1e-3,True)
            if '20m' in b:
                f4 = float(bands['20m']['FT4'])
            elif '40m' in b:
                f4 = float(bands['40m']['FT4'])
            elif '15m' in b:
                f4 = float(bands['15m']['FT4'])
            else:
                f4 = float(bands[b[-1]]['FT4'])
            fc.append(f4*1e3)
            P.NEW_FREQ=fc
        else:
            P.NEW_FREQ=fc

        if P.gui and (P.MP_SCHEME==2 or P.MP_SCHEME==3):
            frq1 = .001*np.array( P.NEW_FREQ )
            P.gui.FreqSelect(frq1,True,P.VFO)

        print('------ HOPPING:',t,P.NEW_FREQ)

    # Function to delay start of timer so we are aligned with WSJT clock
    def align_clock(self,nsecs=15,offset=0.5):
        print('Aligning clock: nsecs=',nsecs,'\toffset=',offset,' ...')
    
        t1 = datetime.datetime.now()
        print('t1=',t1)
        secs = t1.second + t1.microsecond*1e-6
        delay = nsecs-(secs % nsecs) - offset
        if delay<0:
            delay+=nsecs
    
        time.sleep(delay)
        t2 = datetime.datetime.now()
        print('t2=',t2)

