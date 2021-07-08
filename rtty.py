############################################################################
#
# .py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Portion of GUI related to wideband RTTY
#
# This is not quite functional yet.
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

from __future__ import print_function

import sys
import time
import math
if False:
    # use Qt4 
    from PyQt4.QtGui import *
    from PyQt4.QtCore import * 
else:
    # use Qt5
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import * 
import pyqtgraph as pg
import numpy as np
from sig_proc import ring_buffer2
import threading
from Plotting import *
import multiprocessing as mp
from profiler import *

################################################################################

DEBUG=True
#DEBUG=False

MAX_DECODERS=100

mark_bins = [559]                        # 20170919_221412
#mark_bins = [555,514]                    # 20170919_210138
#mark_bins = [517,639]
#b1=900   #1100
#mark_bins = range(b1,b1+150,1)
#mark_bins = [485]                        # 20170919_193518

b1=810  
mark_bins = range(b1,b1+MAX_DECODERS,1)            # rtty_sprint
mark_bins = [860,1049,1073,1104,1201] 
#mark_bins = [1049]
YLIM=[800,1250]

#b1=256-233                               # All of the narrow-band wav files from CQ WW
#mark_bins = range(b1,b1+21,1)
#b1=256-241                               # vp6d_17m
#mark_bins = range(b1,b1+61,1)

PROFILE=False

################################################################################

def nextpow2(n):
    # Returns next power of two above n
    return math.ceil(math.log(n,2))

# Print w/o cr/linefeed
def my_print(msg):
    print(msg,end='',flush=True)        # Python 3
    #print(msg,)                          # Python 2?

################################################################################

# Multichannel RTTY Demodulator
class RTTY_GUI(QWidget):

    # Any GUI update must be inside GUI thread so we use a 
    # signal to indicate new waterfall ready.
    # Note that signals need to be defined inside a QObject class/subclass
    # The args for the handlers are defined here also
    #wf_ready   = pyqtSignal()                   # No args
    wf_ready = pyqtSignal(np.ndarray)
    char_ready = pyqtSignal(int,str)

    ### This is probably true of the text box also so perhaps we need a second signal/slot for this?
    
    def __init__(self,P):
        super(RTTY_GUI,self).__init__()

        # Init
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Init RYRYRYRYRYRYRYRYRYRYRYRYRYRY')
        self.P = P
        self.RTTY  = RTTY_Params(P.FS_OUT)
        self.active = False

        # Set up sig proc thread
        self.q_in  = mp.Queue()
        self.q_out = mp.Queue()
        #self.q_in  = Queue.Queue()
        #self.q_out = Queue.Queue()
        self.worker = RTTY_Executive( args=(self.P,self.q_in,self.q_out,) )
        self.worker2 = threading.Thread(target=self.msg_handler, args=())
        self.worker2.setDaemon(True)
        self.worker2.start()
        self.worker.start()

        # Set up separate window to show waterfall and decoded text
        self.hide()
        self.resize( 1200,1000 )
        self.setWindowTitle("Wideband RTTY")
        self.grid = QGridLayout()
        self.setLayout(self.grid)

        # Area for waterfall display
        self.w1 = pg.GraphicsLayoutWidget()
        self.grid.addWidget(self.w1,0,0,2,1)
        self.imager = imager(self.w1)

        # Area for plotting
        if DEBUG:
            self.plotter=plot1d()
            #self.plotter=plot1d(symbols=['x','o'],pens=[None,None])
            self.grid.addWidget(self.plotter.pwin,3,0,1,1)

        # Box for decoded text
        if False:
            self.txt = QPlainTextEdit()
            self.grid.addWidget(self.txt,0,1)
        else:
            self.listWidget = QListWidget()
            self.grid.addWidget(self.listWidget,0,1)
            self.list_items = []
            odd=False
            for i in range(MAX_DECODERS):
                item = QListWidgetItem()
                #item.setText('~')
                if odd:
                    item.setBackground( QColor(255,0,0,48) )
                else:
                    item.setBackground( QColor(255,255,0,48) )
                odd=not odd
                self.listWidget.addItem(item)
                self.list_items.append(item)
            self.listWidget.show()

        # Some control buttons
        btn = QPushButton('Wrap-Up')
        btn.clicked.connect(self.wrap_up)
        self.grid.addWidget(btn,1,1)
        
        btn = QPushButton('Pause')
        btn.clicked.connect(self.pause)
        self.grid.addWidget(btn,2,1)

        btn = QPushButton('Quit')
        btn.clicked.connect(self.quit)
        self.grid.addWidget(btn,3,1)

        # Connect the signals
        self.wf_ready.connect(self.update_waterfall)
        self.char_ready.connect(self.update_list)

        return


    def msg_handler(self):
        print('MSG Handler -----------------------------------------------------------------------------')
        self.Done=False
        while not self.Done:
            while self.q_out.qsize()>0:
                msg,x,y=self.q_out.get()
                if msg=='WF_Ready':
                    #self.wf = x
                    self.wf_ready.emit(x)
                elif msg=='Char':
                    #print('MSG Handler: msg=',msg,'\tx=',x,'\ty=',y)
                    self.char_ready.emit(x,y)
                elif msg=='Exit':
                    self.Done=True
                    break
            time.sleep(.02)
        print('@@@@ RTTY Msg Handler Quitting ...')
        self.quit()
    
    # Slot to update waterfall display - not sure what the argument is for
    @pyqtSlot(np.ndarray)
    def update_waterfall(self,wf):
        #print('... Updating WF')
        #return
        wm = np.max(wf)
        #wf = self.wf[:,self.space_bin-100:self.mark_bin+100]
        wf = np.maximum(wf,wm-60)

        # Show where decoders are placed
        for mark_bin in self.RTTY.mark_bins:
            if mark_bin==mark_bins[2]:
                mark  = wf[:,mark_bin].copy()
                space = wf[:,mark_bin+self.RTTY.NBINS]
            wf[0:50,mark_bin]  = wm-60

        # Compute axis data
        frq = self.RTTY.frq + self.P.FC[0]*1e-3
        f1=min(frq)
        f2=max(frq)
        #print frq
        
        #self.imager.imagesc(wf)
        self.imager.imagesc(wf,ylim=YLIM)
        #self.imager.imagesc(wf,ylim=[f1,f2],ydata=frq[::-1])

        if DEBUG:
            if False:
                psd = sum(wf,1)
                self.plotter.plot(psd)
                self.plotter.setXRange(YLIM)
            elif False:
                #self.plotter.plot(mark+1j*space)
                self.plotter.plot(mark,space)
            elif False:
                bits = (mark>space).astype(int)
                a = (mark-space)
                b = (mark+space)
                #a = (2*bits-1)*(mark-space)
                
                #self.plotter.plot(a+1j*b)
                self.plotter.plot(a,b)
                self.plotter.setXRange([-50,50])
                self.plotter.setYRange([-100,50])
            elif False:
                mm = np.mean(mark)
                ms = np.mean(space)
                sc = (mark-mm)*(ms-space) + 0.5*(mm+ms)
                sc2 = np.mean(sc)
                sc = sc +1j*sc2
                #sc=mark+space
                self.plotter.plot(sc)
                self.plotter.setYRange([-500,500])
            elif False:
                bits1 = (mark>space+18).astype(int)
                bits2 = (space>mark+18).astype(int)
                a = bits1*mark + bits2*space
                b = bits2*mark + bits1*space
                sc = a - b
                h  = np.ones(21)/21
                sc2 = np.convolve(sc,h,'same')
                self.plotter.plot(sc+1j*sc2)
                self.plotter.setYRange([0,50])
            else:
                bits = (mark>space).astype(int)
                #a = bits*mark + (1-bits)*space
                #b = (1-bits)*mark + bits*space
                #sc = a - b
                sc = (2*bits-1)*(mark-space)
                h  = np.ones(21)/21
                sc2 = np.convolve(sc,h,'same')
                self.plotter.plot(sc+1j*sc2)
                self.plotter.setYRange([0,50])
                
                

    # Slot to update list
    @pyqtSlot(int,str)
    def update_list(self,idx,ch):
        #print('-------------------------- Update list -----------------------------------',idx,ch)

        #if False:
        #    self.txt.insertPlainText( ch )
        
        if len(ch)>1:
            print('HEY!!!!!',ch)
        elif ord(ch)==10:
            ch=' \\n '
        elif ord(ch)==13:
            ch=' \\r '

        txt=self.list_items[idx].text()
        #print('idx=',idx,'\tch=',ch,'\ttxt=',txt)

        txt=txt[7:]
        txt=txt[-50:]
        txt2="{:5d}: {}".format(self.RTTY.mark_bins[idx],txt+ch)
        
        self.list_items[idx].setText(txt2)

        
    # Start the RTTY decoder
    def start(self):
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY start')
        
        self.show()
        #self.raise_()
        self.activateWindow()
        self.active=True
        self.q_in.put(('Start',None))
        
    # Stop the RTTY decoder
    def stop(self):
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY stop')
        self.hide()
        self.active=False
        self.q_in.put(('Stop',None))

    # Pause the decoder
    def pause(self):
        self.active=not self.active

    # Quit the RTTY decoder
    def quit(self):
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Quit')
        self.hide()
        self.active=False
        self.q_in.put(('Exit',None))

    def test(self):
        print('TEST TEST')
    

    def wrap_up(self):
        print('Wrapping up ....')
        self.q_in.put(('Exit',None))
        self.q_out.put(('Exit',None,None))

        if DEBUG:
            #self.plotter.plot(self.mark)
            #self.plotter.plot(self.mark + 1j*self.space)
            #self.sig = self.mark-self.space
            #self.plotter.plot(self.sig)
            #self.plotter.plot(self.scores[:,0])
            #self.plotter.plot(self.isyms2)
            #self.plotter.plot(self.snr,title='Symbol SNR')
            #self.plotter.title('Symbol SNR')
            self.plotter.grid(True)
            #self.imager.imagesc(self.scores)
            print('Plotted')
            self.P.app.processEvents() 
        
            #print 'SIG  =',self.sig
            #print 'ISYMS=',self.isyms2
            #print 'SCORES 0 =',self.scores[:,0]
            #print 'SCORES 31=',self.scores[:,31]
            #print 'SC =',self.sc
            
            #print self.symbols
            #print self.text
            #print(''.join(self.text))
        
            np.savetxt('sig.txt',self.sig)
            np.savetxt('sc.txt',self.sc)
            np.savetxt('sc2.txt',self.sc2)
            np.savetxt('isyms.txt',self.isyms2)
            #np.savetxt('scores.txt',self.scores)
            np.savetxt('timing.txt',self.timing)
            np.savetxt('snr.txt',self.snr)


################################################################################

# Processing parameters for 45-baud rtty
class RTTY_Params():
    def __init__(self,FS_OUT):

        # RTTY Params
        self.T             = 22e-3                        # Bit time = 22ms
        #self.BAUD         = 1/self.T                     # Baud rate =45.4545...
        self.FSK_SHIFT     = 170                          # Freq shift
        self.SAMPS_PER_BIT = 4                            # The match filtering output is 4 samples per bit

        STOP_BITS = 1.5
        self.M    = int(4*(1+5+STOP_BITS))                # 4 samps/bit * (5-bits/symbol + 1 start bit and 1.5 stop bits )
        print('M=',self.M)
        
        self.N             = int( round(self.T*FS_OUT) )        # Number of samples per symbol
        self.NFFT          = int( 2**nextpow2(self.N) )         # FFT size
        NSTEP = self.N/4.
        self.NSTART=[]
        for i in range(4):
            self.NSTART.append( int(NSTEP*i+0.5) )
        print('N=',self.N,'\tNFFT=',self.NFFT)
        print('NSTEP=',NSTEP,'\tNSTART=',self.NSTART)

        bin_size = FS_OUT/float(self.NFFT)                       # Freq resolution
        self.NBINS = int( round( self.FSK_SHIFT/bin_size ) )     # No. bins separating mark and space freqs
        print('nbins=',self.NBINS)

        self.frq = np.fft.fftshift( np.fft.fftfreq(self.NFFT, d=1000./FS_OUT) ) + 0

        self.mark_bins = np.array(mark_bins)
        
################################################################################

class FIFO():
    def __init__(self,n,dtype=None):
        self.x    = np.zeros(n,dtype)

    def push(self,xx):
        self.x[:-1] = self.x[1:]
        self.x[-1]  = xx
        return self.x
        

class FIFO2():
    def __init__(self,m,n,dtype=np.float32):
        print("FIFO2",m,n,dtype)
        self.x    = np.zeros((m,n),dtype)

    def push(self,xx):
        #print(np.shape(xx),np.shape(self.x))
        self.x[:-1,:] = self.x[1:,:]
        self.x[-1,:]  = xx
        #print(self.x[:,1024])
        return self.x
        

class RTTY_Decoder():

    def __init__(self,nid,RTTY,q_out,mark_bin):
        if nid==0:
            print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Decoder Init')
            self.pr = Profiler2()
            self.ncalls=0
        self.q_out = q_out
        self.nid = nid

        # Extract required processing params
        self.M      = RTTY.M
        self.NFFT   = RTTY.NFFT
        self.NBINS  = RTTY.NBINS
        self.THRESH = 8

        # Generate procesing tables
        self.baudot(nid==0)
        self.symbol_bits(nid==0)

        # FFT is upsidedown so we need to flip sense of mark & space bins - not true anymore!
        #self.mark_bin  = self.NFFT - mark_bin
        #self.space_bin = self.NFFT - (mark_bin - self.NBINS)
        self.mark_bin  = mark_bin
        self.space_bin = mark_bin + self.NBINS

        # Processing buffers
        self.mark_buf  = FIFO(3*32,np.float32)
        self.space_buf = FIFO(3*32,np.float32)
        self.signal    = FIFO(32,np.float32)
        self.isyms     = FIFO(self.M, np.int32)
        self.sc3       = FIFO(self.M , np.float32)
        self.sc_buf    = FIFO(4*self.M+1 , np.float32)
        if DEBUG:
            self.mark    = []
            self.space   = []
            self.sig     = []
            self.sc      = []
            self.isyms2  = []
            self.sc2     = []
            self.scores  = []
            self.timing  = []
            self.symbols = []
            self.snr     = []
            self.text    = []

        # Init history
        self.shift = False                       # Fig shift 
        self.tlast = 0                           # Last declaration time
        self.sym   = 0                           # Last declared symbol

        
    def decode(self,line,n):

        # Extract mark and space bins
        mark      = line[0,self.mark_bin]
        space     = line[0,self.space_bin] 
        self.mark_buf.push(mark)
        self.space_buf.push(space)

        # For each time step, compute score for each 5-bit symbol (32 symbols in all)
        # We haven't determined the sampling periods yet so determine most likely symbols
        # at each quater-symbol sampling point
        signal = self.signal.push( mark-space )
        score = np.matmul(self.H,signal)
        isym = np.argmax(score)
        self.isyms.push(isym)
        self.sc_buf.push( score[isym] )

        if self.nid==0 and PROFILE:
            self.ncalls+=1
            if self.ncalls==800:
                self.pr.start(str(self.ncalls))

        # Determine timing - step 1 is to look over a few symbols and
        # integrate the scores
        sc2  = np.sum( self.sc_buf.x[-1::-self.M] )
        #sc2  = sum( self.sc_buf.x[-1::-self.M] )         # Same as 'reduce ufunc'
        if self.nid==0 and self.ncalls==800:
            self.pr.stop(str(self.ncalls))
            
        self.sc3.push(sc2)                # Scores at all samples in a symbol

                               
        # Save debugging info
        if DEBUG:
            self.mark  = np.append( self.mark  , mark )
            self.space = np.append( self.space , space)
            self.sig = np.append( self.sig   , mark-space)
            self.sc.append(score[isym])
            self.isyms2.append(isym)
            self.sc2.append( sc2 )
            if len(self.scores)==0:
                self.scores=score
            else:
                self.scores=np.vstack((self.scores,score))

        # The sampling times should above the highest score in each symbol window
        # Recall, M is the number of quarter symbols samples in a symbols
        if (n % self.M) ==0:
            i = np.argmax(self.sc3.x)                # Point to highest score
            t = n+i-self.M                         # Corresponding sampling time

            # Compare current and previous sampling declaration and filter out  anomalies
            dt = t-self.tlast
            if dt>=25:
                            
                # Timing step is approximately one symbol so decode the previous symbol
                # Compute SNR for this symbol
                snr2 = self.compute_snr(self.sym,self.tlast-n)
                
                # Use SNR to select only good-quality symbols to decode
                ch = self.decode_symbol(self.sym,snr2)
                if ch:
                    #my_print(ch)
                    #print('Decode',self.nid,ch)
                    self.q_out.put( ('Char',self.nid,ch) )
                    
                # Save debugging info
                if DEBUG:
                    self.symbols.append(self.sym)
                    self.timing.append(t)
                    self.snr.append(snr2)
                    if ch:
                        self.text.append( ch )
                                
            else:
                # Timing step was too small so delete prior timing declaration
                if DEBUG and len(self.timing)>0:
                    self.timing[-1]=t

            # Get ready for next iteration
            self.tlast = t
            self.sym   = self.isyms.x[t-n]


    # Generate baudot table
    def baudot(self,iplot):

        SPACE=' ';
        #SPACE='=';          # For Debugging
  
        if False:
            self.ltrs = ['<NULL>','E','<CR>','A',SPACE,'S'   ,'I','U','<LF>','D','R','J', \
                         'N','F','C','K','T','Z','L','W','H','Y','P','Q','O','B','G', \
                         '<FIGS>','M','X','V','<LTRS>']
            self.figs = ['<NULL>','3','<CR>','-',SPACE,'<BELL>','8','7','<LF>','$','4',"'", \
                         ',','!',':','(','5','"',')','2','#','6','0','1','9','?','&', \
                         '<FIGS>','.','/',';','<LTRS>']
        else:
            self.ltrs = ['\0','E','\n','A',SPACE,'S','I','U','\r','D','R','J', \
                         'N','F','C','K','T','Z','L','W','H','Y','P','Q','O','B','G', \
                         '<FIGS>','M','X','V','<LTRS>']
            self.figs = ['\0','3','\n','-',SPACE,'\g','8','7','\r','$','4',"'", \
                         ',','!',':','(','5','"',')','2','#','6','0','1','9','?','&', \
                         '<FIGS>','.','/',';','<LTRS>']

        if iplot:
            my_print('LTRS: ')
            for i in range(32):
                ch=self.ltrs[i]
                if len(ch)==1 and ord(ch)<32:
                    my_print(repr(ch))
                else:
                    my_print(ch)
                    
            my_print('\nFIGS: ')
            for i in range(32):
                ch=self.figs[i]
                if len(ch)==1 and ord(ch)<32:
                    my_print(repr(ch))
                else:
                    my_print(ch)

            print('\n')


    # Creates a table of bits for all the symbols at 4 bits per symbols
    def symbol_bits(self,iplot):

        stop = 4*[1]
        zero = 4*[0]
        H=[]
        B=[]

        # LSB bits are sent first, MSB last so we need to reverse order
        for i in range(32):
            b=np.binary_repr(i,5)

            b=b.replace('1','1 ')
            b=b.replace('0','0 ')
            b1=b.split(' ')
            h=list(map(int, b1[:5] ))
            h=[1,0] + h[::-1] + [1]

            if len(B)==0:
                B=h
            else:
                B=np.vstack((B,h))

            b=b.replace('1','1 1 1 1')
            b=b.replace('0','0 0 0 0')
            b2=b.split(' ')
            h=list(map(int, b2[:20] ))
            h=stop + zero + h[::-1] + stop

            h=np.asarray(h,np.float32)            
            if len(H)==0:
                H=h
            else:
                H=np.vstack((H,h))

            if iplot:
                if i==0:
                    print('\nH=')
                else:
                    print(i,'\t',H[i])
                
        self.H=2*H-1             # Map 0 & 1 to +/-1 for convoultion
        self.B=B
        if iplot:
            print('B=',B)
            print(B.dtype,H.dtype)

        #sys.exit(0)
        return

    
    # Function to compute SNR for a symbol
    def compute_snr(self,sym,t):
        bits  = self.B[sym]
        path  = t - 29 + 4*np.arange(8)
        mark  = [self.mark_buf.x[i]  for i in path]
        space = [self.space_buf.x[i] for i in path]

        signal = bits*mark + (1-bits)*space
        noise  = (1-bits)*mark + bits*space
            
        snr2 = np.mean(signal - noise)
        return snr2


    # Function to decode a symbol
    def decode_symbol(self,sym,snr2):
    
        # Use SNR to select only good-quality symbols to decode
        ch=None
        if snr2>=self.THRESH:
  
            # Look for LTRS/FIGS control chars 
            if sym==32-1:
                self.shift=False
                ctrl=True
            elif sym==28-1:
                self.shift=True
                ctrl=True
            elif sym==1-1:
                # Filter out non-printable chars: \0
                ctrl=True
            else:
                ctrl=False

            # Assign char from proper set
            if not ctrl:
                if self.shift:
                    ch = self.figs[sym]
                else:
                    ch = self.ltrs[sym]

        return ch
    

    
################################################################################            
        
class RTTY_Executive(mp.Process):

    def __init__(self,args):
        super(RTTY_Executive,self).__init__()
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Executive Init')

        self.P        = args[0]
        self.q_in     = args[1]
        self.q_out    = args[2]
        self.active   = False
        self.Done     = False

        #self.rb = ring_buffer2('RTTY',self.P.RB_SIZE,False,True)
        self.rb = ring_buffer2('RTTY',self.P.RB_SIZE)
        print('tag=',self.rb.tag)

        # Instantiate a profiler
        self.pr = Profiler2()
        

    def msg_handler2(self):
        #print 'MSG Handler 2 -----------------------------------------------------------------------------'
        while self.q_in.qsize()>0:
            msg,x = self.q_in.get()
            #print 'msg=',msg
            if msg=='Start':
                self.active=True
            elif msg=='Stop':
                self.active=False
            elif msg=='IQ':
                self.rb.push(x)
            elif msg=='Exit':
                print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Executive Quitting ...')
                self.active=False
                self.Done=True
                #sys.exit(0)

                
    def find_sigs(self,line):
        #print("Find Sigs...",np.shape(self.line))

        wf=self.wf.x
        wm = np.max(wf)
        self.det.push(line)

        ndet=0
        for i in range(YLIM[0],YLIM[1]-self.RTTY.NBINS):
            mark  = self.det.x[:,i]
            space = self.det.x[:,i+self.RTTY.NBINS]
            bits = (mark>space).astype(int)
            sc = (2*bits-1)*(mark-space)
            sc2 = np.sum(sc)
            if sc2>20*21:
                #print("Found sig in bin",i)
                wf[0:50,i]  = wm-50
                ndet+=1
        print('ndet=',ndet)
       
        return
        
        for i in range(YLIM[0],YLIM[1]-self.RTTY.NBINS):
            mark  = wf[:,i]
            space = wf[:,i+self.RTTY.NBINS]
            bits = (mark>space).astype(int)
            sc = (2*bits-1)*(mark-space)
            h  = np.ones(21)/21
            sc2 = np.convolve(sc,h,'same')
            if sc2[50]>20:
                print("Found sig in bin",i)
                wf[0:50,i]  = wm-50
                
                
                
    # Run the RTTY Executive
    def run(self):
        print('\nRYRYRYRYRYYRYRYRYRYRYRYRYRYRYRY RTTY Executive Run')

        # Processing params
        self.RTTY   = RTTY_Params(self.P.FS_OUT)
        self.N      = self.RTTY.N
        self.NSTART = self.RTTY.NSTART
        self.NFFT   = self.RTTY.NFFT

        #self.mark_bin = self.NFFT - int(559*48./25.)
        print('Mark bin(s) :',self.RTTY.mark_bins)
        if len(self.RTTY.mark_bins)>MAX_DECODERS:
            print('\n\n******************************* Too many mark bins - Aborting **************************\n\n',MAX_DECODERS)
            sys.exit(0)

        self.decoders=[]
        nid=0
        for mark_bin in self.RTTY.mark_bins:
            self.decoders.append( RTTY_Decoder(nid,self.RTTY,self.q_out,mark_bin) )
            nid+=1
        
        #self.wf   = np.zeros( (200,self.NFFT) )
        self.wf   = FIFO2( 200,self.NFFT )
        self.det  = FIFO2( 21,self.NFFT )
        self.line = np.zeros( (1,self.NFFT) )

        self.First_Time=True
        self.window  = np.kaiser(self.N,8.6)
        n=0
        icnt=0

        while not self.Done:
            #print 'RTTY Run1',self.rb.tag,self.rb.nsamps
            self.msg_handler2()
                
            if not self.active:
                print('RTTY not active - RB size:',self.rb.nsamps)
                time.sleep(1)
                
            elif self.rb.ready(self.NFFT):
                #print 'RTTY Run2 - RB size:',self.rb.nsamps,self.N,self.NFFT,self.active
                if n>500 and not self.pr.triggered and PROFILE:
                    self.pr.start(str(n))
                    
                # Pull a symbols worth of data an append it to the previous symbol
                iq = self.rb.pull(self.N)
                if self.First_Time:
                    prev=iq
                    self.First_Time=False
                    continue
                else:
                    x=np.concatenate( (prev , iq) )
                    
                # Process a symbol's worth of data, i.e. 4 samples
                for i in range(4):

                    # Compute filterbank (i.e. FFT) at each quarter symbol timing epoch
                    xx=x[self.NSTART[i]:(self.NSTART[i]+self.N)]
                    #print i,len(xx)
                    X = np.fft.fftshift( np.fft.fft(xx * self.window , self.NFFT) )
                    #XX = np.square(X.real) + np.square(X.imag)
                    XX = 10*np.log10( np.square(X.real) + np.square(X.imag) )

                    self.line[0,0:]=np.flipud(XX)
                    #self.wf = np.concatenate( (self.wf[1:self.wf.shape[1],:],self.line),axis=0 )
                    self.wf.push(self.line)

                    # Check for active signals @@@@@@@
                    self.find_sigs(self.line)

                    # Decode next symbol in the bit stream
                    n+=1
                    for decoder in self.decoders:
                        decoder.decode(self.line,n)
                    
                # Save data for next go round
                prev = iq

                if self.pr.enabled:
                    self.pr.stop(str(n))
                    print('\tSymbol time=',self.RTTY.T,'secs.')
                    print('\t',len(self.decoders),'decoders running\n')
                
                # Update waterfall display
                icnt = (icnt+1) % 4
                if icnt==0:
                    #for mark_bin in self.RTTY.mark_bins:
                    #    self.wf[0:50,mark_bin]  = -200
                    self.q_out.put(('WF_Ready',self.wf.x,None))

        print('@@@@ RTTY Exec exiting @@@@')
        

