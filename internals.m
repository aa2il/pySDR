# Script to examine internals

close all
clear all

more off
pkg load signal
addpath('~/m-files')

%graphics_toolkit("gnuplot")
graphics_toolkit("fltk")          % Much fast but buggy


load internals.mat

whos
AF_BWs
fsout

%return

fh1=figure;
grid on
fh2=figure;
grid on

fsout
NFFT=1024*4;
N=NFFT;
frq = ((0:(N-1))/N - 0.5)*double(fsout)/1000. ;

hh = h_bank_r;           % Demod filters - real
hh = h_bank_c;           % Demod filters - complex

c='brgmkycbrgmkyc'
lgd={};
for i=1:size(hh,1)
  cc = c( mod(i-1,length(c)) +1 );
  lgd{i}=AF_BWs(i,:);
  
  h = hh(i,:);
  H = fft(h,NFFT);
  HdB = 10*log10( H.*conj(H) );

  figure(fh1)
  hold on
  plot(h,cc)

  figure(fh2)
  hold on
  plot(frq,fftshift(HdB),cc)
end

figure(fh1)
title('Demod Filters - Impulse Response')
xlabel('Sample Number')

figure(fh2)
title('Demod Filters - Frequency Response')
xlabel('f (KHz)')
ylabel('dB')
legend(lgd)

figure(fh2)
legend(lgd)
axis([min(frq),max(frq),-150,1])





