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
fname='demod_20190321_225218.dat';

% Russian ISS SSTV - low mod index
fname='SatComm2/baseband_iq_20190413_221346.dat'


% Read data 
fname
NFFT=1024*16
[y,hdr,str]=read_sdr_data(fname);

length(y)
hdr
fs=hdr(1)
nchan=hdr(4)

t=(0:(length(y)-1))/fs;


% Design filter
NN=5
fc=3000/(fs/2)
[B, A] = butter(NN, fc,'low');

[H,w] = freqz(B,A);
H=20*log10( abs(H) );
 
figure
plot(w*fs/(2*pi),H)
grid on

%return

%y = filter(B,A,y);


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












  
