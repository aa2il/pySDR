############################################################################
#
# Plotting.py - Rev 1.1
# Copyright (C) 2021-3 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Plotting related functions for pySDR
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
import pyqtgraph as pg
from PyQt5.QtGui import QTransform,QFont
from PyQt5.QtWidgets import QLCDNumber,QLabel
from PyQt5.QtCore import * 
from Tables import *
import sig_proc as dsp
import numpy as np
import scipy.signal as signal

################################################################################

def get_color_map(key, pos_min, pos_max):
    #    keys=['jet','autumn','bone','colorcube','cool','copper','gray','hot','hsv','parula','pink','spring','summer','winter']
    #    idx = idx % len(keys)
    #    colormap = colormaps[keys[idx]]
    colormap = COLORMAPS[key]
    #print 'keys=',COLORMAPS.keys()
    
    pos = pos_min + (pos_max - pos_min) * np.arange(len(colormap))/(len(colormap)-1)

    return pg.ColorMap(pos, colormap)

################################################################################

# Object for displaying 1d data
class plot1d():
    def __init__(self,win_label='Plot 1-D',TITLE=None,symbols=[None,None],pens=['r','g']):

        #self.pwin = pg.GraphicsWindow(title=win_label)
        #self.pwin.show()
        self.pwin = pg.GraphicsLayoutWidget(show=True,title=win_label)

        # Create plot for (potentially complex-valued) time series
        self.p1 = self.pwin.addPlot(title=TITLE)
        self.p1.show()
        self.p1.enableAutoRange('xy', True)
        self.curve1i = self.p1.plot(pen=pens[0],symbol=symbols[0],name='I')
        self.curve1q = self.p1.plot(pen=pens[1],symbol=symbols[1],name='Q')

    def plot(self,x,y=[],title=None):
        if len(y)==0:
            y=x
            x=list(range(len(y)))
        #print 'PLOT:',len(x),len(y)
        #print x[0:10],y[0:10]
        if np.iscomplexobj(y):
            self.curve1i.setData(x,y.real)
            self.curve1q.setData(x,y.imag)
        else:
            self.curve1i.setData(x,y)
            self.curve1q.setData([],[])

        if title:
            self.title(title)
        self.p1.show()
        #print 'PLOT Done.'

    def title(self,TITLE):
        self.p1.setTitle(TITLE)

    def grid(self,on_off):
        self.p1.showGrid(x=on_off, y=on_off)

    def setXRange(self,xlim):
        self.p1.setXRange(xlim[0],xlim[1])

    def setYRange(self,ylim):
        self.p1.setYRange(ylim[0],ylim[1])

        
################################################################################

# Object for displaying images
class imager():
    def __init__(self,pwin=None):
        self.xscale = 1
        self.xtrans = 0
        self.yscale = 1
        self.ytrans = 0
        self.xpad   = 0
        self.ypad   = 0
        self.enable_mouse=False # Only want one of these to be turned on
        # Otherwise, we get multiple calls

        if not pwin:
            pwin = pg.GraphicsLayoutWidget()
        self.pwin=pwin

        self.img = pg.ImageItem(border='w')
        self.p3 = pwin.addPlot()   # Need to use PlotItem to get axis
        self.p3.addItem(self.img)

        # Set-up colormap
        cmap = get_color_map('jet', 0.,1.)
        lut = cmap.getLookupTable(0.,1., 256)
        self.img.setLookupTable(lut)

        # Crosshairs
        if self.enable_mouse:
            self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='m')
            self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='m')
            self.p3.addItem(self.vLine, ignoreBounds=True)
            self.p3.addItem(self.hLine, ignoreBounds=True)
            #self.proxy = pg.SignalProxy(self.p3.scene().sigMouseMoved,
            #                            rateLimit=60, slot=self.mouseMoved)
            self.p3.scene().sigMouseMoved.connect(self.mouseMoved)    
            self.p3.scene().sigMouseClicked.connect(self.mouseClicked)    

    # Function to plot an image
    def imagesc(self,data,xlim=[],ylim=[],xdata=[],ydata=[],FLIP=False):
        self.img.setImage(data)
        #self.img.update()
        #self.p3.update()

        # Set axis limits
        if len(xlim)>0:
            self.p3.setXRange(xlim[0],xlim[1], padding=0)
        else:
            self.p3.setXRange(0, data.shape[0]+self.xpad, padding=0)      ########

        if len(ylim)>0:
            self.p3.setYRange(ylim[0],ylim[1], padding=0)
        else:
            self.p3.setYRange(0, data.shape[1]+self.ypad, padding=0)

        # Flip image upside down
        if FLIP:
            self.p3.getViewBox().invertY(True)
            
        # Adjust pixel scaling so image lines use with axis
        if len(xdata)>0:
            xsc = float(xdata[-1]-xdata[0])/data.shape[0] 
            xt = xdata[0]/xsc
            if xsc!=self.xscale or  xt!=self.xtrans:
                # print "Re-scaling"

                # Undo previous shift & scale
                if False:
                    self.img.translate(-self.xtrans, 0)
                    self.img.scale(1./self.xscale,1)
                else:
                    tr1 = QTransform()
                    tr1.translate(-self.xtrans, 0)
                    tr1.scale(1./self.xscale,1)
                    self.img.setTransform(tr1)

                # Apply new shift and scale
                self.xscale = xsc
                self.xtrans= xt
                if False:
                    self.img.scale(self.xscale,1)
                    self.img.translate(self.xtrans, 0)
                else:
                    tr2 = QTransform()
                    tr2.scale(self.xscale,1)
                    tr2.translate(self.xtrans, 0)
                    self.img.setTransform(tr2)

                # print self.xscale,self.xtrans,frq[0],frq[-1],len(frq),npsd

        if len(ydata)>0:
            ysc = (ydata[-1]-ydata[0])/data.shape[1] 
            yt = ydata[0]/ysc
            if ysc!=self.yscale or  yt!=self.ytrans:
                #print "Re-scaling"

                # Undo previous shift & scale
                self.img.translate(0,-self.ytrans)
                self.img.scale(1,1./self.yscale)

                # Apply new shift and scale
                self.img.scale(1,ysc)
                self.yscale = ysc

                self.ytrans= yt
                self.img.translate(0,self.ytrans)

                # print self.xscale,self.xtrans,frq[0],frq[-1],len(frq),npsd

    # Callback when the mouse/crosshairs have moved
    def mouseMoved(self,evt):
        print("IMAGERl mouse move detected:")
        pos = evt   # [0]  ## using signal proxy turns original arguments into a tuple
        if self.p3.sceneBoundingRect().contains(pos):
            mousePoint = self.p3.vb.mapSceneToView(pos)
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

            print("Waterfall:",mousePoint.x(),mousePoint.y())

    def mouseClicked(self,evt):
        pos = evt    #  [0]          ## using signal proxy turns original arguments into a tuple
        print("\nIMAGER Mouse click detected: pos=",pos)
            
    def show(self):
        self.pwin.show()

    def hide(self):
        self.pwin.hide()
        
    def activateWindow(self):
        self.pwin.activateWindow()
        
    def raise_(self):
        self.pwin.raise_()
        
################################################################################

# Object to plot data and its PSD
class three_box_plot():
    def __init__(self,P,win_label,TITLE1,TITLE2,fs,foff,chunk_size,Nfft,overlap,clickCB=None,TRANSPOSE=False):
        self.P = P
        self.enable_mouse=True # This will be the driver routine for the mouse
        self.clickCB = clickCB
        self.foff=foff
        self.fc=0
        self.TRANSPOSE=TRANSPOSE
        self.SpotItems=[]

        # Create plot window and start out with it hidden
        self.pwin = pg.GraphicsLayoutWidget(show=False,title=win_label)
        self.pwin.hide()

        # Tighten borders - order looks like LEFT, TOP, RIGHT, BOTTOM
        self.pwin.centralWidget.layout.setContentsMargins(0,0,0,0)
        #self.pwin.centralWidget.layout.setSpacing(0)

        # Create plot for (potentially complex-valued) time series
        self.p1 = self.pwin.addPlot(title=TITLE1)
        self.p1.enableAutoRange('xy', True)
        self.p1.setMenuEnabled(False)
        # Pen can be a string or an RGB tuple
        # self.curve1i = self.p1.plot(pen=(255,0,0),name='I')
        self.curve1i = self.p1.plot(pen='r',name='I')
        self.curve1q = self.p1.plot(pen='g',name='Q')
        self.p1.show()
        self.pwin.nextRow()
 
        # Create plot for PSD
        self.p2 = self.pwin.addPlot(title=TITLE2)
        self.p2.enableAutoRange('xy', True)
        self.p2.setMenuEnabled(False)
        # self.curve2 = self.p2.plot(pen=(255,255,0),name='PSD')
        self.curve2 = self.p2.plot(pen='y',name='PSD')

        # Make room to plot peaks also
        self.curve2pk = self.p2.plot(pen=None,symbol='o',symbolPen='g',\
                                     symbolBrush=None)
        self.curve2smooth = self.p2.plot(pen='r')

        # Add a line to indicate current center freq
        if self.TRANSPOSE:
            ANGLE=0
        else:
            ANGLE=90
        self.vLine = pg.InfiniteLine(angle=ANGLE, movable=False, pen='w')
        self.p2.addItem(self.vLine, ignoreBounds=True)
        self.p2.show()
        self.p2_visible=True

        # Create object to compute the PSD
        if chunk_size>65536:
            print('************************************************************')
            print('THREE BOX PLOT init - warning, there is a bug somewhere that limits PSD to 2^16 - chopping chunk size from',chunk_size)
            print('************************************************************')
            chunk_size=int(65636/2)
            Nfft=2*chunk_size
        self.psd  = dsp.spectrum(fs,chunk_size,Nfft,overlap)
        nfft = self.psd.NFFT

        # Create waterfall 
        self.pwin.nextRow()
        self.imager = imager(self.pwin)
        self.p3 = self.imager.p3
        self.p3.setMenuEnabled(False)

        self.wf   = -1e38*np.ones( (nfft,100) )
        self.wf_cnt = 0
        self.wf_fc = 0
        self.line = -1e38*np.ones( (nfft,1) )

        # Add a vertical line to indicate current center freq
        pen1=pg.mkPen((128,0,255), width=3)
        self.vLine4 = pg.InfiniteLine(angle=ANGLE, movable=False, pen=pen1)
        self.p3.addItem(self.vLine4, ignoreBounds=True)

        pen2=pg.mkPen((128,0,255), width=3, style=Qt.DotLine)  
        self.vLine5 = pg.InfiniteLine(angle=ANGLE, movable=False, pen=pen2)
        self.p3.addItem(self.vLine5, ignoreBounds=True)
        self.vLine6 = pg.InfiniteLine(angle=ANGLE, movable=False, pen=pen2)
        self.p3.addItem(self.vLine6, ignoreBounds=True)

        pen3=pg.mkPen((255,200,255), width=3, style=Qt.DashLine)  
        self.vLine7 = pg.InfiniteLine(angle=ANGLE, movable=False, pen=pen3)
        self.p3.addItem(self.vLine7, ignoreBounds=True)
        self.vLine8 = pg.InfiniteLine(angle=ANGLE, movable=False, pen=pen3)
        self.p3.addItem(self.vLine8, ignoreBounds=True)
        
        # Crosshairs
        if self.enable_mouse:
            self.vLine2 = pg.InfiniteLine(angle=90, movable=False, pen='m')
            self.hLine2 = pg.InfiniteLine(angle= 0, movable=False, pen='m')
            self.p2.addItem(self.vLine2, ignoreBounds=True)
            self.p2.addItem(self.hLine2, ignoreBounds=True)

            self.vLine3 = pg.InfiniteLine(angle=90, movable=False, pen='m')
            self.hLine3 = pg.InfiniteLine(angle= 0, movable=False, pen='m')
            self.p3.addItem(self.vLine3, ignoreBounds=True)
            self.p3.addItem(self.hLine3, ignoreBounds=True)
            """
            self.proxy1 = pg.SignalProxy(self.p2.scene().sigMouseMoved,
                                        rateLimit=60, slot=self.mouseMoved)
            self.proxy2 = pg.SignalProxy(self.p2.scene().sigMouseClicked,
                                        rateLimit=60, slot=self.mouseClicked)
            """
            self.p3.scene().sigMouseMoved.connect(self.mouseMoved)    
            self.p3.scene().sigMouseClicked.connect(self.mouseClicked)    


    def hide(self):
        self.pwin.hide()
        
    def show(self):
        self.pwin.show()

        
    # Routine to plot next chunk
    def plot(self,x,y,fc,show_time_series,show_psd):
        #print('PLOT 1:',fc,show_time_series,show_psd)
        P=self.P

        # Plot the time series data 
        if show_time_series:
            if np.iscomplexobj(y):
                self.curve1i.setData(x,y.real)
                self.curve1q.setData(x,y.imag)
            else:
                #print 'Hmmm',len(x),len(y)
                self.curve1i.setData(x,y)
                self.curve1q.setData([],[])
            self.p1.show()
        else:
            self.p1.hide()

        # Compute and plot the PSD
        PSD = self.psd.periodogram(y,True)
        #print '\nPlotting ...',fc,self.P.RIG_IF
        frq = self.psd.frq - self.foff + fc
        self.fc=fc-self.foff
        #print "PSD Resolution =",(frq[2]-frq[1])*1000,' Hz'
        #print "PSD frqs:",self.psd.frq[0],self.psd.frq[-1],fc,self.P.BFO*1e-3

        # Peak picking experiments
        #self.PSD = PSD
        #self.frq = frq
        if False:
            dist = self.P.PEAK_DIST/self.psd.df
            #print 'dist=',self.psd.df,self.psd.fs,dist
            #print np.diff(frq)
            peaks, _ = signal.find_peaks(PSD,distance=dist)
            frq2 = frq[peaks]
            PSD2 = PSD[peaks]
            #print peaks
            #print frq2
            #print PSD2
            self.curve2pk.setData(frq2, PSD2)

        # Check if waterfall needs to be shifted bx center freq was changed
        self.shift_waterfall(fc)
        
        self.p2_visible=show_psd
        if show_psd:
            self.curve2.setData(frq,PSD)
            self.p2.show()
        else:
            self.p2.hide()

        # Plot a line showing center freq
        #self.curve3.setData( [fc, fc] , [min(PSD),max(PSD)] )
        self.vLine.setPos(fc)

        # Set freq axis limits depending on selected limits & mode
        f1=min(frq)
        f2=max(frq)
        bw=0
        #print "PSD frqs:",f1,f2,fc
        if P.PAN_BW>0:
            if P.PAN_DIR=='Up/Down':
                bw = P.PAN_BW*0.5e-3
            else:
                bw = P.PAN_BW*1e-3
            f1=max(f1,fc-bw)
            f2=min(f2,fc+bw)
            #print 'f1 f2=',f1,f2
        if P.PAN_DIR=='Up':
            f1=fc-1.
        elif P.PAN_DIR=='Down':
            f2=fc+1.
        self.p2.setXRange(f1,f2, padding=0)
        #print "Axis frqs:",f1,f2,bw,P.PAN_BW,P.PAN_DIR

        # Update Waterfall
        #P.pr.profile('')
        npsd=len(PSD)
        if P.RIG_IF<0:
           PSD = np.flipud(PSD)
        self.line[0:npsd,0]=PSD
        self.line[npsd:,0]=-1e38
        #print 'WF insert for fc=',fc
        if True:
            self.wf = np.concatenate( (self.wf[:,1:self.wf.shape[1]],self.line),axis=1 )
        else:
            self.wf = np.roll( self.wf,-1,axis=1)
            self.wf[0:npsd,-1] = PSD
        if self.wf_cnt<self.wf.shape[1]:
            self.wf_cnt += 1
        self.vLine4.setPos(fc)

        if P.NUM_RX==2:
            # Mark sub-rx freq also
            #print('3-box:',fc,P.FC,P.NUM_RX)
            irx=1-P.MAIN_RX
            self.vLine5.setPos(.001*P.FC[irx])
        else:
            # Mark +/- 1 KHz from center
            #print('3-box:',fc,P.FC,P.NUM_RX)
            self.vLine5.setPos(fc-1)
            self.vLine6.setPos(fc+1)
            
        if P.frqArx:
            self.vLine7.setPos(P.frqArx)
        if P.frqAtx:
            self.vLine8.setPos(P.frqAtx)
            
        #P.pr.profile('')

        # Limit dynamic range & plot the waterfall image
        #wm = np.max(self.wf[0:npsd,-self.wf_cnt:])
        #self.imager.imagesc(np.maximum(self.wf[0:npsd,:],wm-P.PAN_DR) , xlim=[f1,f2],xdata=frq)

        if P.AF_BW>0:
            bw = P.AF_BW
        else:
            bw = P.VIDEO_BW/2.*1e-3
        idx = np.nonzero( abs(self.psd.frq) < bw)
        
        # Peak picking
        if True:
            # Play with background estimator
            #n=len(PSD)
            PSD2=np.mean(self.wf[:,-self.wf_cnt:],1)
            #n = 2*int(dist/2)+1
            #print 'dist=',dist,n
            #bkgnd = signal.medfilt(PSD2,21)
            bkgnd = np.median(PSD2)
            self.curve2smooth.setData(frq, bkgnd*np.ones(npsd))

            dist = self.P.PEAK_DIST/self.psd.df
            #peaks, _ = signal.find_peaks(PSD2,distance=dist)
            peaks, _ = signal.find_peaks(PSD2,distance=dist,height=bkgnd+10)
            #print 'PLOT: peaks=',peaks,len(frq),len(PSD),len(PSD2)
            frq2 = frq[peaks]
            PSD3 = PSD[peaks]
            self.curve2pk.setData(frq2, PSD3)
            #self.peaks = peaks
            self.pk_frqs = frq2

        #print 'PSD frqs:',self.psd.frq[0],self.psd.frq[-1],P.AF_BW,P.VIDEO_BW,bw
        #print idx
        #mu = np.mean(self.wf[0:npsd,-self.wf_cnt:])
        #sigma = np.std(self.wf[0:npsd,-self.wf_cnt:])

        #med = np.median(self.wf[idx,-self.wf_cnt:])
        med=bkgnd
        #print 'PLOT:',PSD2,med
        #print 'PLOT:',len(PSD2),len(bkgnd)
        #print 'WF dyn range:',wm,mu,sigma,med
        #self.imager.imagesc(np.maximum(self.wf[0:npsd,:],mu+sigma*2-P.PAN_DR) , xlim=[f1,f2],xdata=frq)
        #self.imager.imagesc(np.maximum(self.wf[0:npsd,:],med) , xlim=[f1,f2],xdata=frq)

        #zz = (1./sigma)*( self.wf[0:npsd,:] - mu)
        zz = self.wf[0:npsd,:] - med
        zmax = np.nanmax(zz)
        if self.TRANSPOSE:
            self.imager.imagesc(np.maximum(np.transpose(zz),zmax-P.PAN_DR),
                                ylim=[f1,f2],ydata=frq,FLIP=True)
            ax=self.p3.getAxis('bottom')
        else:
            self.imager.imagesc(np.maximum(zz,zmax-P.PAN_DR),
                                xlim=[f1,f2],xdata=frq)
            ax=self.p3.getAxis('left')

        # Hide time axis
        ax.hide()

    # Add spots to waterfall - a work in progress
    def addSpot(self,x,y,txt,c):
        #print('Plotting->AddSpot:',x,y,txt,c)
        if self.TRANSPOSE:
            y,x=x-0.1,y
            self.imager.xpad=20
            txt2=txt
            ftsize=10
            txt0=''
        else:
            # Not sure why the magic offset of 10 here but it works
            # Probably has something to do which text box corner is referenced
            # See https://en.wikipedia.org/wiki/Mathematical_operators_and_symbols_in_Unicode
            # for unicoded symbol table
            #txt2=txt
            #txt2="*"
            txt2="\u2b24"    # Solid circle
            ftsize=10
            x-=0.05*(len(txt2)+1)
            y+=12
            self.imager.ypad=8
            txt0='      '         # Get call sign out from under the mouse
        spot = pg.TextItem(txt2,c)
        spot.setPos(x,y)
        spot.setFont(QFont('Arial',ftsize, QFont.Bold))
        spot.setToolTip(txt0+txt)
        self.pwin.setStyleSheet(" QToolTip{ border: 1px solid white; color: k ; font: bold 12pt}")
        #                         "background-color: lightgoldenrodyellow ;
        self.p3.addItem(spot,ignoreBounds=True)
        self.SpotItems.append(spot)
        #spot.scene().sigMouseClicked.connect(self.mouseClicked2)     # Dont do this - too many calls!
        #print('Plotting->AddSpot:',x,y,txt,c,spot)

    def mouseClicked2(self,evt):
        pos = evt    #  [0]          ## using signal proxy turns original arguments into a tuple
        print("\nSPOTS Mouse click detected: pos=",pos)
            
        
    # Routine to get rid of all spot labels
    def removeAllSpots(self):
        for spot in self.SpotItems:
            self.p3.removeItem(spot)

        
    # Function to shift waterfall when we change freqs
    def shift_waterfall(self,frq):
        df    = self.psd.frq[1]-self.psd.frq[0]
        nbins = int( float(frq - self.wf_fc)/df + 0.5 )
        if nbins!=0:
            print('SHIFT_WATERFALL:',self.wf_fc,frq,df,nbins)
            self.wf = np.roll( self.wf,-nbins,axis=0)
            self.wf_fc = frq
        
        
    # Callback when the mouse/crosshairs have moved
    def mouseMoved(self,evt):
        pos = evt # [0]  ## using signal proxy turns original arguments into a tuple
        #print "Mouse move detected:",pos
        if self.p2_visible and self.p2.sceneBoundingRect().contains(pos):
            #            try:
            # For some reason, this generates a numerical error some times - we don't need to see it
            # Seems to be fixed if we also test if plot is visible
            # Maybe we just want to drive this off of the waterfall (p3) first
            mousePoint = self.p2.vb.mapSceneToView(pos)
            #except:
            #    print "Mouse move error"
            #    return
            self.vLine2.setPos(mousePoint.x())
            self.hLine2.setPos(mousePoint.y())
            self.vLine3.setPos(mousePoint.x())

            self.mouse_x = mousePoint.x()
            self.mouse_y = mousePoint.y()

        elif self.p3.sceneBoundingRect().contains(pos):
            mousePoint = self.p3.vb.mapSceneToView(pos)
            self.vLine3.setPos(mousePoint.x())
            self.hLine3.setPos(mousePoint.y())
            self.vLine2.setPos(mousePoint.x())

            self.mouse_x = mousePoint.x()
            self.mouse_y = mousePoint.y()
            
        # print "Mouse:",mousePoint.x(),mousePoint.y()


    # Callback when the mouse is clicked
    def mouseClicked(self,evt):
        pos = evt    #  [0]          ## using signal proxy turns original arguments into a tuple
        print("\nMouse click detected: pos=",pos,self.mouse_x,self.mouse_y,'\n\tevt=',evt)# ,pos.widget)
        #print 'pos=',pos.pos()
        #print 'button=',pos.button()
        #print 'buttons=',pos.buttons()
        #if pos.button()==1:
        print('Button ',pos.button(),self.mouse_x)

        # Snap to closest peak
        if self.P.gui.Use_Peaks_cb.isChecked():
            idx = ( np.abs(self.pk_frqs - self.mouse_x) ).argmin()
            self.mouse_x = self.pk_frqs[idx]
            
        df = self.mouse_x - self.wf_fc
        self.clickCB(pos.button(),self.mouse_x,self.mouse_y,self.fc)

        # Move cross hairs back to where they were
        self.mouse_x += df
        #print 'CROSS HAIRS TO',self.mouse_x,self.mouse_y
        self.vLine2.setPos(self.mouse_x)
        #self.hLine2.setPos(self.mouse_y)
        self.vLine3.setPos(self.mouse_x)
        self.hLine3.setPos(self.mouse_y)
