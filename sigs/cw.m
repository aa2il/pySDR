% Script to play with demod CW recorded from SDR

close all
clear all

more off
format compact
pkg load signal
addpath('~/m-files')

% Use this if we want to see the entire waterfall but it is slow
%graphics_toolkit("gnuplot")
graphics_toolkit("fltk")          % Much faster but buggy

% User Params
fname='demod_20190321_225218.dat';
wpm_max = 50*1                     % Fastest speed we're likely to deal with


fname

% Read data 
[y,hdr,str]=read_sdr_data(fname);

% Keep a piece - use waterfall to find segs
idx=[];
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

% Play segment
if 0
  sound(y,fs,16)
end



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


if 1
  dotlen = 1.2/wpm_max             % Duration of a dot
  Ndot = fs*dotlen                 % No. samples in a dot
  NFFT=2^nextpow2(Ndot)
  
  [WF,istart] = waterfall(y,Ndot,NFFT,0.75);
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
end


[Xm,bin]=max(sum(WF2,2))
XX=WF2(bin,:);

figure
plot(XX)


return


figure
Y=log( y.*y );
plot(Y)


% Let's try playing with Goertzel Alg
%  s[n]=x[n]+2cos(w0)s[n-1]-s[n-2]
% y[n]=s[n]-e^{-jw0}s[n-1]

NFFT=N
[Xm,bin]=max(X(1:(NFFT/2)))
f0=fs*bin/NFFT
w0=2*pi*f0/fs
cosw0=2*cos(w0)
e=exp(-j*w0)
s=0*x;
yy=s;
s(1) = x(1);
s(2) = x(2) + cosw0*s(1);
for n=3:N
  s(n)  = x(n) + cosw0*s(n-1) - s(n-2);
  yy(n) = s(n) - e*s(n-1);
end

figure
plot(abs(yy))

return

w = 2*pi*bin/N
cr = cos(w);
ci = sin(w);
coeff = 2 * cr;

sprev = 0;
sprev2 = 0;
for n=1:N
  s = x(n) + coeff * sprev - sprev2;
  sprev2 = sprev;
  sprev = s;
end

power = sprev2 * sprev2 + sprev * sprev - coeff * sprev * sprev2;
