###################################################################

# Functions related to file I/O

import time
import numpy as np
import wave
import struct
import os
import sys
from scipy.io import wavfile

#import limits

###################################################################

# A playpen for alg dev
def alg_dev():
    print('Hey &&&&')
    fname='demod1.dat'
    hdr,tag,x = read_data(fname)             # This needs to be updated

    print('hdr=',hdr)
    print('tag=',tag)
    print('x=',x[0:10],' ... ',x[-1],len(x))

    # Plot IQ data
    app = QApplication(sys.argv)
    plotter = plot1d()
    plotter.plot(x)

    # Event loop
    app.exec_()
    
###################################################################

def limiter(x,a):
    return np.maximum( np.minimum(x,a) ,-a)


class sdr_fileio:
    def __init__(self,fname,rw,P=None,nchan=2,tag=''):
        self.P     = P
        self.fname = fname
        self.nchan = nchan
        self.nbytes = 2
        self.tag   = tag.upper()
        self.fp    = None
        self.WAVE_OUT = False

        ext = os.path.splitext(self.fname)[1]
        print('ext=',ext)
        self.WAVE_IN  = ext=='.wav'

        if rw=='r':
            self.hdr = self.read_header()

            # Position pointer to start of requested data
            if P:
                istart = int( P.REPLAY_START*60*self.srate*self.nchan*4 )
                if istart>0:
                    if self.WAVE_IN:
                        print('*** SDR_FILE_IO - Seek not yet supported for wav files ***')
                    else:
                        print('Seeking',istart/1024,'Kbytes into file - Start time=', \
                              P.REPLAY_START,'min')
                        self.fp.seek(istart, os.SEEK_CUR)

        elif rw=='w':
            self.hdr_written = False
            
        else:
            print('ERROR - rw must be r or w',rw)
            sys.exit(1)

    # Function to close the file nicely
    def close(self):
        self.hdr_written = False
        if self.fp:
            print('Closing',self.fname2)
            self.fp.close()
            if self.WAVE_OUT and False:
                wave.close(self.fp_wav)
                print('Closed',self.wave_fname)

    # Functions to read data from disk
    def read_header(self):

        VERBOSITY=1

        if self.WAVE_IN:
            fp = wave.open(self.fname, 'rb')
            hdr_ver =  0.0
        else:
            fp = open(self.fname,'rb')
            hdr_ver = float( np.fromfile(fp,np.float32,1) )
        self.fp = fp

        # Read header
        if hdr_ver==0.0:
            # Wave file
            self.nchan = fp.getnchannels()
            self.srate = fp.getframerate()
            self.fc    = 0
            self.duration = 0
            hdr=[]
        elif hdr_ver==1.0:
            # SDR file - Next version should include IF, foffset,bw...
            hdr_len = int( np.fromfile(fp,np.float32,1) )
            if VERBOSITY>0:
                print('hdr_len=',hdr_len)
            hdr = np.fromfile(fp,np.float32,hdr_len-2)
            if VERBOSITY>0:
                print('hdr=',hdr)

            self.srate    = hdr[0]
            self.fc       = hdr[1]
            self.duration = hdr[2]
            self.nchan    = int( hdr[3] )
            
            tag_len       = int( hdr[4] )
            self.tag      = fp.read(tag_len)
            if VERBOSITY>0:
                print('tag=',self.tag)

            chk     = np.fromfile(fp,np.float32,2)
            if VERBOSITY>0:
                print('chk=',chk)

        else:
            print('Unknown file format')
            sys.exit(1)

        if self.nchan == 2:
            self.dtype = np.complex64
        else:
            self.dtype = np.float32

        if VERBOSITY>0:
            print('READ_HEADER: hdr_ver=',hdr_ver)
            sz = os.path.getsize(self.fname)
            print('\tfname       =',self.fname)
            print('\thdr      =',hdr)
            print('\tsrate    =',self.srate)
            print('\tfc       =',self.fc)
            print('\tduration =',self.duration)
            print('\tnchan    =',self.nchan)
            print('\ttag      =',self.tag)
            print('\tsize     =',sz,'bytes')
            print('\tduration = ',float(sz)/float( self.srate*self.nchan*4*60 ),' minutes')
            print(' ')

        return hdr

    # Function to read data
    def read_data(self):

        # Read the data
        print('Reading data...',self.fp,self.dtype)
        if self.WAVE_IN:
            samplerate, data = wavfile.read(self.fname)
            print('ndim,shape=',np.ndim(data),np.shape(data))
            if np.ndim(data)==1:
                x=data
            else:
                x=data[:,0]
            print('shape=',np.shape(x))
            
            #CHUNK = 1024
            #data = self.fp.readframes(CHUNK)
            #print('type=',type(data))
            #while len(data) > 0:
            #    data = self.fp.readframes(CHUNK)
            #    print('type=',type(data))


        else:        
            x = np.fromfile(self.fp,self.dtype,-1)
        
        # Close the file
        self.fp.close()

        return x


    # Function to write header info to disk
    def write_header(self,P,fname,nchan,tag):

        # Open output files & write a simple header
        s=time.strftime("_%Y%m%d_%H%M%S", time.gmtime())      # UTC
        dirname='../data/'
        dirname=''
        self.fname2 = dirname+fname+s+'.dat'
        print('\nOpening',self.fname2,'...')
        self.fp     = open(self.fname2,'wb')

        if nchan==2:
            self.dtype = np.complex64
        else:
            self.dtype = np.float32

        hver=1.0
        if tag=='RAW_IQ':
            self.fs = P.SRATE
            self.WAVE_OUT = False
        elif tag=='BASEBAND_IQ':
            self.fs = P.FS_OUT
            self.WAVE_OUT = False
        else:
            self.fs = P.FS_OUT
            self.WAVE_OUT = True
            
        hdr = [hver,0,self.fs, P.FC[0],P.DURATION,nchan,len(tag),0]
        hdr[1] = len(hdr)
        hdr = np.array(hdr, np.float32)
        print("hdr=",hdr,tag)
        hdr.tofile(self.fp)
        self.fp.write(tag.encode())
        chk = np.array([12345,0], np.float32)
        chk.tofile(self.fp)

        
    # Function to write data to disk
    def save_data(self,x):

        # If this is the first block, write out a simple header
        if not self.hdr_written:
            self.write_header(self.P,self.fname,self.nchan,self.tag)
            self.hdr_written = True

            if self.WAVE_OUT:
                self.wave_fname = self.fname2.replace('.dat','.wav')
                print('SAVE_DATA: wave_name=',self.wave_fname,'\tnchan=',self.nchan)
                self.fp_wav = wave.open(self.wave_fname, "w")
                self.nbytes=2
                #self.nbytes=4          # Signed ints (32-bits) doesnt work
                self.fp_wav.setparams((self.nchan, self.nbytes, self.fs, 0, 'NONE', 'not compressed'))

        # Convert data to 32-bit floats & write it out
        if len(x)>0:
            if self.nchan==1:
                x.real.astype(self.dtype).tofile(self.fp)
            else:
                x.astype(self.dtype).tofile(self.fp)
                
            if self.WAVE_OUT:
                # In Python3, this seemed to get a whole lot easier - or maybe I was just over thinking it!
                if sys.version_info[0]==3:
                    sc=32767.  #/4
                    if self.nchan==1:
                        # Convert singale channel data to ints - can't figure out how to write floats to wave?
                        #xx = (sc*x.real).astype(np.int16)
                        xx = (sc*limiter(x.real,1.)).astype(np.int16)
                    else:
                        # Interleave data - there probably is a better way but this seems to work
                        #print('x=',x)
                        xx = np.empty( 2*x.size, dtype=np.int16 )
                        #xx[0::2] = sc*x.real
                        #xx[1::2] = sc*x.imag
                        xx[0::2] = sc*limiter(x.real,1.)
                        xx[1::2] = sc*limiter(x.imag,1.)
                        #print('xx=',xx)

                    self.fp_wav.writeframes(xx)
                    return

                # Old Python 2 code - doesn't work quite right but good enough for now ...
                
                mask = 0xffffffff
                #xx = np.int(32767*x.real) + 1j*np.int(32767*x.imag)                      # Doesn't work
                sc=32767.
                sc=sc/4
                #sc=1
                #sc=.1
                #xx = np.int32(sc*x.real) + 1j*np.int32(sc*x.imag)                      # Works
                xx = np.int16(sc*x.real) + 1j*np.int16(sc*x.imag)                      # Works

                #print 'Should be saving wave data ...',x[0:5],xx[0:5]

                #xx = np.maximum( np.minimum(x.real,1.) , -1. ) + 1j*np.maximum( np.minimum(x.imag,1.) , -1. )
                
                #packed = "".join((struct.pack('h', 32767.*item ) for item in x))
                #packed = "".join((struct.pack('h', (32767.*item) & 0xffffffff ) for item in x))

                #packed = "".join((struct.pack('h', 32767.*item ) for item in xx))
                #print x

                #print limits.shrt_max
                #print xx

                if self.nbytes==2:
                    packed = "".join((struct.pack('h', item) for item in xx))   # Signed shorts (16-bits)
                else:
                    packed = "".join((struct.pack('i', item) for item in xx))   # Signed ints (32-bits) doesnt work
                
                self.fp_wav.writeframes(packed)
 
