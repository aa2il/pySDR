% Script to play with raw IQ data recorded from sdr

close all
clear all

more off
format compact
pkg load signal
addpath('~/m-files')

% Use this if we want to see the entire waterfall but it is slow
%graphics_toolkit("gnuplot")
graphics_toolkit("fltk")          % Much fast but buggy

% User Params
fname = 'raw_iq_20181108_212625.dat';         # Default
fname = 'raw_iq_20181108_213313.dat' ;        # fs=2 foffset=100
#fname = 'raw_iq_20181108_214229.dat';        # AM with fs=2 foffset=100
fname = 'raw_iq_20181108_224006.dat';         # fs=2 foffset=0
fname = 'raw_iq_20181108_224836.dat';         # fs=2 foffset=100 200Khz IF filter
fname = 'raw_iq_20181108_231526.dat';         # Default with 200 KHz IF filter
fname = 'raw_iq_20181108_232011.dat';         # fs=3 foffset=100 300Khz IF filter
fname = 'baseband_iq_20190208_194246.dat';

fname = 'SatComm/baseband_iq_20190208_194246.dat';
fname = 'SatComm/baseband_iq_20190209_003549.dat';
fname = 'SatComm/baseband_iq_20190209_010321.dat';
fname = 'SatComm/baseband_iq_20190209_010618.dat';
fname = 'SatComm/baseband_iq_20190209_011505.dat';       % CW & SSB  
%fname = 'SatComm/baseband_iq_20190209_014754.dat';

% ISS SSTV
fname = 'SatComm/baseband_iq_20190209_020710.dat';      % ISS SSTV
fname = 'SatComm/baseband_iq_20190209_184402.dat';       % Overhead pass

fname='baseband_iq_20190216_173349.dat';
fname='baseband_iq_20190215_182952.dat';
fname='baseband_iq_20190226_230830.dat';

% CW
#fname='demod_20190321_225218.dat';

fname

NFFT=1024*16

% Russian ISS SSTV - low mod index
fname='SatComm2/baseband_iq_20190413_221346.dat'
fname='SatComm2/baseband_iq_20190412_013210.dat'
fname='SatComm2/baseband_iq_20190413_185551.dat'
fname='SatComm2/baseband_iq_20190414_012518.dat'


% Read data 
[y,hdr,str]=read_sdr_data(fname);

% Keep a piece - use waterfall to find segs
idx=[];
idx = (2000*NFFT/2) : (2800*NFFT/2);          % SSTV section
if length(idx)>0
  y = y(idx);
  y(1:10)
  
  fname2='junk.dat'
  write_sdr_data(fname2,hdr,str,100*y);

  %[y,hdr,str]=read_sdr_data(fname2);
  %y(1:10)
  %stop
  
end

% Write wave file
%y(1:10)
yy=[real(y) , imag(y)];
%yy(1:10,:)
[d,n,e]=fileparts(fname)
if length(d)==0, d='.'; end
fout = [d '/' n '.wav']
fs=hdr(1)
wavwrite(yy,fs,fout)
clear yy

length(y)
hdr
fs=hdr(1)
nchan=hdr(4)



t=(0:(length(y)-1))/fs;

figure
subplot(2,1,1)
plot(t,real(y))
hold on
plot(t,imag(y),'r')
title('Raw Data')
xlabel('Time (sec)')
ylabel('Amplitude')
legend('I','Q')
z=axis;
axis([0 t(end) z(3:4)])
grid on

subplot(2,1,2)
x = y;
X = fft(x);
X = 10*log10( X.*conj(X) );

N=length(x)
frq = ((0:(N-1))/N - 0.5)*fs/1000. ;

plot(frq,fftshift(X))
title('PSD of Raw Data')
xlabel('Freq (KHz)')
ylabel('PSD (dB)')
grid on

z=axis;
axis([-fs/2000 fs/2000 z(3:4)])



[WF,istart] = waterfall(y,NFFT,NFFT,0.5);
WF2=10*log10(WF);

  figure
  imagesc(WF2,max(WF2(:)) + [-100 0])
  colormap(jet)
  title('Waterfall of Raw Data')
  xlabel('Time')
  ylabel('Freq bin')
  colorbar;

%  z=axis;
%  axis([z(1) z(2) NFFT/2 NFFT])

% NFM det
IQ = y(3:end);
d  = IQ - y(1:end-2);
y1 = y(2:end-1);
fm = real(y1).*imag(d) - imag(y1).*real(d);

%sound(100*fm,fs,16)

figure
plot(fm)












  
