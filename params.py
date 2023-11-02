############################################################################
#
# params.py - Rev 1.0
# Copyright (C) 2021-3 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Command line param parser for pySDR.
# Support routines for pySDR
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

import argparse
from rig_io.ft_tables import bands,CONNECTIONS,RIGS
from Tables import MODES,SDRplaysrates,RTLsrates
from utils import *
import numpy as np
from sig_proc import up_dn
import platform

############################################################################

MAX_RX=6              # max number of receivers to open

############################################################################

# Structure to contain users and processing params
class RUN_TIME_PARAMS:
    def __init__(self):

        # Process command line args
        # Can add required=True to anything that is required
        arg_proc = argparse.ArgumentParser()

        arg_proc.add_argument('-sdrplay', action='store_true',
                              help='SDRPlay RSP Device')
        arg_proc.add_argument('-rtl', action='store_true',
                              help='RTL Dongle Device above 25 MHz')
        arg_proc.add_argument('-rtlhf', action='store_true',
                              help='RTL Dongle Device below 30 MHz')
        arg_proc.add_argument('-fake', action='store_true',
                              help='Use fake RTL driver')
        arg_proc.add_argument('-replay', help="Replay",
                              type=str,default="",nargs='+')
        arg_proc.add_argument('-test', action='store_true')
        arg_proc.add_argument('-ft8', action='store_true',
                              help='Sub RX follows FT8 subband')
        arg_proc.add_argument('-ft4', action='store_true',
                              help='Sub RX follows FT4 subband')
        arg_proc.add_argument('-ft44', action='store_true',
                              help='Last Sub RX follows FT4 subband')
        arg_proc.add_argument('-aux', action='store_true',
                              help='Send loopback audio to speakers also')
        arg_proc.add_argument("-audio", help="Audio Scheme for routing RXs",
                              type=int,default=1)
        arg_proc.add_argument("-delay", help="Audio Buffer Delay",
                              type=int,default=16)
        
        #arg_proc.add_argument('-left', help='Put Main RX on left channel', action='store_true')
        #arg_proc.add_argument('-right', help='Put Main RX on right channel', action='store_true')

        arg_proc.add_argument("-fc", help="RF Ceneter frequency (KHz)",
                              type=float,default=600,nargs='*')
        arg_proc.add_argument("-src", help="Source for input samples for each RX",
                              type=int,default=-1,nargs='*')
        arg_proc.add_argument("-foffset", help="Tuning offset (KHz)",
                              type=float,default=100)            # Was zero
        arg_proc.add_argument("-mode", help="Demod mode",
                              type=str,default="AM",
                              choices=MODES)
        arg_proc.add_argument("-ant", help="Antenna",
                              type=str,default="A",
                              choices=['A','B','Z'])
        arg_proc.add_argument("-vol", help="Audio Volume",
                              type=int,default=50)
        arg_proc.add_argument("-bfo", help="CW pitch",
                              type=float,default=0)
        arg_proc.add_argument("-t", help="Play duration (sec)",
                              type=float,default=1e38)

        srates = SDRplaysrates + RTLsrates
        #print 'Srates        =',srates,'\n'
        arg_proc.add_argument("-fs", help="RF Sampling rate (MHz)",
                              type=float,default=0,
                              choices=srates)

        arg_proc.add_argument("-IF", help="SDRplay IF Freq (KHz)",
                              type=int,default=0,                    # Was 450
                              choices=[0,450,1620,2048])
        arg_proc.add_argument("-lna", help="SDRplay RF LNA gain",
                              type=int,default=-1,
                              choices=[0,1,2,3,4,5,6,7])
        arg_proc.add_argument("-ifgain", help="SDRplay IF gain",
                              type=int,default=58,
                              choices=range(20,59))
        arg_proc.add_argument("-rigIF", help="SDR is connected to a rig IF (MHz)",
                              type=float,default=0)
        arg_proc.add_argument("-if_bw", help="IF Bandwidth (KHz)",
                              type=float,default=0)
        arg_proc.add_argument("-vid_bw", help="Video Bandwidth (KHz)",
                              type=float,default=0)
        arg_proc.add_argument("-af_bw", help="Audio Bandwidth (KHz)",
                              type=float,default=0)
        arg_proc.add_argument('-pan', help='Pan Adaptor',
                              action='store_true')
        arg_proc.add_argument('-transpose', help='Transpose Waterfalls',
                              action='store_true')
        arg_proc.add_argument('-bandmap', help='Add spots to Waterfall',
                              action='store_true')
        arg_proc.add_argument("-pan_bw", help="Pan Adaptor Bandwidth (KHz)",
                              type=float,default=0)
        arg_proc.add_argument("-pan_dr", help="Pan Adaptor Dynamic Range (dB)",
                              type=int,default=60)
        arg_proc.add_argument("-ppm", help="Clock Freq Correction (PPM)",
                              type=float,default=0)
        arg_proc.add_argument("-fsout", help="Output rate (KHz)",
                              type=float,default=48)  
        arg_proc.add_argument("-corr", help="Audio playback correction (Hz)",
                              type=int,default=0)
        arg_proc.add_argument("-nfilt", help="Filter Length",
                              type=int,default=1001)
        arg_proc.add_argument("-save_iq", help="Save raw IQ data",
                              action="store_true")
        arg_proc.add_argument("-save_baseband", help="Save baseband IQ data",
                              action="store_true")
        arg_proc.add_argument("-save_demod", help="Save demodulated data",
                              action="store_true")

        arg_proc.add_argument('-hop', help="List of Hop Frequencies (KHz)",
                              nargs='*', type=float,default=None)
        arg_proc.add_argument("-hop_time", help="Hop Time (sec)",
                              type=float,default=4*60)
        arg_proc.add_argument('-loopback', help='Use loopback device for demod out',
                              action='store_true')
        arg_proc.add_argument('-follow_freq', help='Follow rig freq',
                              action='store_true')
        arg_proc.add_argument('-follow_band', help='Follow rig band',
                              action='store_true')
        arg_proc.add_argument('-so2v', help='VFO-B follows SDR',
                              action='store_true')
        arg_proc.add_argument('-digi', help='Add 1KHz digi offset',
                              action='store_true')
        arg_proc.add_argument('-rtty', help='Enable wideband RTTY decoder',
                              action='store_true')
        arg_proc.add_argument('-mute', help='Mute the audio replay',
                              action='store_true')
        arg_proc.add_argument('-udp', action='store_true',
                              help='Start UDP client')
        arg_proc.add_argument('-nosplash', help='Dont put up splash screen',
                              action='store_true')
        arg_proc.add_argument("-rig", help="Connection Type",
                              type=str,default="NONE",nargs='+',
                              choices=CONNECTIONS+['NONE']+RIGS)
        #choices=['FLDIGI','FLRIG','DIRECT','HAMLIB','ANY','NONE'])
        arg_proc.add_argument("-port", help="Connection Port",
                              type=int,default=0)
        arg_proc.add_argument("-xlmrpc", help="Try to open xlmrpc port(s)",
                              nargs='*', type=int,default=[])
        arg_proc.add_argument('-geo',type=str,default=None,
                              help='Geometry')
        arg_proc.add_argument("-v", "--verbosity", action="count",
                              help="increase output verbosity")
        arg_proc.add_argument('-no_rigctl', help="Disable rig control menu",
                              action='store_true')
        arg_proc.add_argument('-no_hamlib', help="Disable hamlib servers",
                              action='store_true')
        arg_proc.add_argument('-desktop',type=int,default=None,
                              help='Desk Top Work Space No.')
        args = arg_proc.parse_args()

        if False:
            print("\nArg list:")
            print(args)
            print(vars(args))
            print(args.rtl)
            sys.exit(0)

        # Determine SDR type which is connected to computer
        self.PLATFORM     = platform.system()
        self.TEST_MODE    = args.test
        self.GEO          = args.geo
        self.DESKTOP      = args.desktop
        self.USE_FAKE_RTL = args.fake
        #self.USE_FAKE_RTL=True
        self.sdr = find_sdr_device(self,args)
        print('P.sdr=',self.sdr)
        #sys.exit(0)
        
        # The set of available sampling rates is different for the two SDRs
        # Pick the one that is closest to what the user asked for
        fs = args.fs
        if self.SDR_TYPE=='rtlsdr':
            print('RTL     rates =',RTLsrates)
            if fs==0:
                fs=2
            #if not args.fs in RTLsrates:
            idx = np.argmin( np.abs( np.array(RTLsrates) - fs ) )
            self.SRATE = 1e6*RTLsrates[idx]
        else:
            print('SDRplay rates =',SDRplaysrates)
            if fs==0:
                fs=1     # Was 0.5
            #if not args.fs in SDRplaysrates:
            idx = np.argmin( np.abs( np.array(SDRplaysrates) - fs ) )
            self.SRATE = 1e6*SDRplaysrates[idx]

            #print 'Hmmmm:',self.SRATE,args.fs*1e6
            #sys.exit(0)
        
        # Convert user params to base units
        self.SHOW_SPLASH     = not args.nosplash
        #self.MAIN_LEFT       = args.left
        #self.MAIN_RIGHT      = args.right
        self.RIG_IF          = args.rigIF*1e3

        if self.RIG_IF!=0:
            fc = np.array(np.abs(self.RIG_IF)) * 1e3
        else:
            fc = np.array(args.fc) * 1e3
        if np.isscalar(fc):
            fc = np.array( [fc] )
        self.NUM_RX          = len(fc)
        print('SUPPORT: fc=',fc)

        self.FT8             = args.ft8
        self.FT4             = args.ft4
        self.FT44            = args.ft44
        if self.FT8 and self.NUM_RX==1:
            fc = np.append( fc,fc[0] )
            self.NUM_RX = 2
        if self.FT4:
            fc = expand_ft4(fc*1e-3)*1e3
            self.NUM_RX *= 2
        if self.FT44:
            #print('FT44a:',fc,fc[0],self.NUM_RX)
            #f4 = expand_ft4([fc[0]*1e-3])*1e3
            fc = np.append( fc,fc[0] )
            self.NUM_RX += 1
            #print('FT44b:',fc,f4,self.NUM_RX)

        self.MAX_RX=MAX_RX
        if self.NUM_RX>MAX_RX:
            print(' ')
            print('******************* WARNING - Only 1 to',MAX_RX,'receivers are supported *******************')
            print(' ')
            fc=fc[0:MAX_RX]
            self.NUM_RX = len(fc)
            #sys,exit(0)
        print('FC=',fc)
        self.FC              = fc
        while len(self.FC)<self.NUM_RX:
            self.FC = np.append(self.FC,[0.])
        self.VFO             = MAX_RX*['A']
        self.MODE            = args.mode
        self.ANTENNA         = args.ant
        self.FOFFSET         = args.foffset*1e3
        self.AUX_AUDIO       = args.aux
        self.AUX_USE_BPF     = False
        self.AUDIO_SCHEME    = args.audio

        # Sources for IQ data
        src = np.array(args.src)*1
        if np.isscalar(src):
            src = np.array( [src] )
        while len(src)<self.NUM_RX:
            src = np.append(src,[-1])
        self.SOURCE = src

        # Number of audio play back players
        if self.AUDIO_SCHEME==1:
            self.NUM_PLAYERS=int( self.NUM_RX )
        elif self.AUDIO_SCHEME==2:
            self.NUM_PLAYERS=int( (self.NUM_RX+1)/2 )
        else:
            print('ERROR - Invalid audio playback scheme'.se);f/AUDIO_SCHEME
            sys.exit(0)

        # List of receivers
        self.rx = self.NUM_RX*[None]
            
        # Set SDR lo so it lands in middle of desired tuning range
        if self.FOFFSET==0:
            fo = 0.5*( max(fc)+min(fc) )
            print(min(fc),max(fc),fo)
            self.FOFFSET = fo-max(fc)
            print('Init FOFFSET=',self.FOFFSET)
            print(fc,fo)

        self.BFO             = args.bfo
        if self.MODE=='CW' and self.BFO==0:
            self.BFO         = 700
        
        self.DURATION        = args.t
        self.IF_BW           = args.if_bw*1e3
        self.VIDEO_BW        = args.vid_bw*1e3
        if self.VIDEO_BW==0:
            if self.MODE=='WFM':
                self.VIDEO_BW = 200e3
            else:
                self.VIDEO_BW = 10e3
                
        self.PANADAPTOR      = args.pan
        self.PAN_BW          = args.pan_bw*1e3
        self.PAN_DR          = args.pan_dr
        self.FS_OUT          = args.fsout*1e3
        self.TRANSPOSE       = args.transpose
        self.BANDMAP         = args.bandmap # or self.TRANSPOSE
        self.FS_OUT_CORR     = args.corr
        self.SAVE_IQ         = args.save_iq
        self.SAVE_BASEBAND   = args.save_baseband
        self.SAVE_DEMOD      = args.save_demod
        self.LNA             = args.lna
        self.PPM             = args.ppm
        self.IFGAIN          = float(args.ifgain)
        self.IF              = args.IF
        self.FILT_LEN        = args.nfilt              # Decimation filter length
        self.AF_BW           = args.af_bw*1e3
        self.SHUT_DOWN       = False
        self.PEAK_DIST       = 10e3
        self.FOLLOW_FREQ     = args.follow_freq
        self.FOLLOW_BAND     = args.follow_band
        self.SO2V            = args.so2v
        self.DXSPLIT         = False
        self.DIGI_OFFSET     = args.digi
        self.ENABLE_RTTY     = args.rtty
        if self.REPLAY_MODE:
            self.RIG_CONNECTION  = 'NONE'
        else:
            self.RIG_CONNECTION  = args.rig[0]
        if len(args.rig)>=2:
            self.RIG         = args.rig[1]
        else:
            self.RIG         = None
        self.PORT            = args.port
        self.frqArx          = None
        self.frqAtx          = None
        self.UDP_CLIENT      = args.udp

        self.HAMLIB_SERVERS  = not args.no_hamlib and not self.REPLAY_MODE
        self.RIG_CONTROL_MENU = not args.no_rigctl
        
        if False:
            for afbw in AF_BWs:
                a=afbw.split(" ")
                bw = int(a[0])
                if a[1]=="KHz":
                    bw *= 1e3 
                elif a[1]=="MHz":
                    bw *= 1e6
            sys.exit(0)
        
        # Freq hopping (scanning)
        self.LOOPBACK = args.loopback
        if self.LOOPBACK and self.FS_OUT!=48000:
            print(' ') 
            print('*** ERROR *** Output sampling rate must be 48KHz to use loopback device') 
            print(' ')
            sys.exit(1)
        
        self.HOP_LIST = args.hop
        self.HOP_TIME = args.hop_time
        self.HOPPER   = self.HOP_LIST is not None
        if self.HOPPER and len(self.HOP_LIST)>0:
            self.FC   = self.HOP_LIST[0]*1e3
        self.FC_OLD   = -self.FC

        print('Hipputis Hoppotis:',self.FC,self.HOP_LIST,self.HOPPER,self.HOP_TIME,args.hop)
        #sys.exit(0)

        # Compute inter/decim factors needed to effect down sampling
        if self.FS_OUT<1 or self.FS_OUT>192e3:
            print(self.FS_OUT/1e3)
            print('\n*** ERROR in RUN_TIME_PARAMS - Invalid output sampling rate ***')
            print('  Must be between 1 KHz and 192 KHz\n')
            sys.exit(1)
        self.UP , self.DOWN = up_dn(self.SRATE , self.FS_OUT )
        self.FS_OUT = int( self.SRATE *self.UP / self.DOWN   )

        self.XLMRPC_LIST  = args.xlmrpc
        self.XLMRPC_SOCKS = [None]*len(self.XLMRPC_LIST)
        self.XLMRPC_CNTRS = [0]*len(self.XLMRPC_LIST)
        self.sock1        = None
        
        # Set other defaults
        self.SHOW_RF_PSD       = False                   # No PSD plots        
        self.SHOW_BASEBAND_PSD = False                   # 
        self.SHOW_AF_PSD       = False                   # 
        self.psd               = 0                       # 
        self.tuning_step_khz   = 10                      # Tuning step for mouse wheel
        self.FREQ_CHANGE       = False                   # No freq changes pending
        self.NEW_FREQ          = self.FC
        self.MODE_CHANGE       = False                   # No mode changes pending
        self.NEW_MODE          = self.MODE
        
        self.AF_GAIN           = 0.5                     # AF slider in the middle
        self.VOL               = args.vol
        
        self.RX_HOLD           = False                   # RX is not held
        self.MUTED             = MAX_RX*[args.mute]      # Start with audio muted?
        self.INTERNALS         = 'internals.mat'         # Output file where we dump internal vars such as filter coeffs

        self.fnames            = ['raw_iq','baseband_iq','demod']
        self.fp                = [-1]*3
        self.status            = [0]*3
        self.threads           = []
        self.NEW_SPOT_LIST     = None

        # Compute size of RF sampling chunk and playback ring buffer:
        # Pulse audio wants in chunks of 1024 samples ...
        self.OUT_CHUNK_SIZE = 1024

        # ... We'll therefore grab thr RF samples in chunks large enough
        # to accomodate one playback block ...
        #self.IN_CHUNK_SIZE  = self.OUT_CHUNK_SIZE*self.NDEC
        self.IN_CHUNK_SIZE  = int( self.OUT_CHUNK_SIZE*self.DOWN/float(self.UP) + 0*0.5 )

        # ... Not quite sure how big we really need to make the ring buffer
        # between the sig processor and the audio playback but this seems to
        # work
        #self.RB_SIZE        = args.nbuff*self.OUT_CHUNK_SIZE
        self.RB_SIZE        = 32*self.OUT_CHUNK_SIZE
        self.DELAY          = min(32,max(1,args.delay))*self.OUT_CHUNK_SIZE

        if self.NUM_RX>2 and True:
            self.RB_SIZE *= 4

        if self.SDR_TYPE == 'rtlsdr':
            self.RB_SIZE *= 2              # 
            
        if self.FS_OUT>100e3:
            self.RB_SIZE *= 4              # Not sure why but this seems to clobber some problems
        elif self.FS_OUT>50e3:
            self.RB_SIZE *= 2              # Not sure why but this seems to clobber some problems

        # Adjust tuning offset so we don't have to compute sines/cosines
        # over and over in the local osc
        adjust_foffset(self)

    def list_fields(self):
        vv=vars(self)
        #print vv
        #print vv.keys()
        for key in list(vv.keys()):
            print(key,'\t',vv[key],'\t',type( vv[key] ))
            
    def copy_fields11(self):
        class NEWCOPY():
            def __init__(self):
                newcopy.__dict__.update(self.__dict__)
                return newcopy

    def copy_fields22(self):
        class Empty():
            def __init__(self):
                pass
        newcopy = Empty()
        #newcopy.__class__ = obj.__class__
        newcopy.__dict__.update(self.__dict__)
        return newcopy

    # Routine to copy the properties (i.e. fields) of this class (i.e. structure)
    def copy_fields(self,CleanUp):

        # Function to create an empty class (structure)
        def empty_copy(obj):
            class Empty(obj.__class__):
                def __init__(self):
                    pass
            newcopy = Empty( )
            newcopy.__class__ = obj.__class__
            return newcopy

        # Create empty class and then populate it with all properties
        newcopy = empty_copy(self)
        newcopy.__dict__.update(self.__dict__)
        
        # Delete properties containing objects that will cause trouble with Pickled for queue messaging
        if CleanUp:
            del newcopy.rx
            del newcopy.rxStream
            del newcopy.sdr
            del newcopy.q1
            del newcopy.q2
            
        return newcopy

    
