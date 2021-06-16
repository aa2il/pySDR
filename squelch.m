% Squelch alg development

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
fname = 'data/roars_2018_11_08.wav'            % Not enough audio BW to try out
fname = 'demod_20181109_010056.wav'

% Read SDR file
idx=[];
if 0
  [y,hdr,str]=read_sdr_data(fname);
  length(y)
  hdr
  fs=hdr(1)
  nchan=hdr(4)
else
  [y,fs,nbits]=wavread(fname);
  fs
  nbits

  %idx=.9e7:2e7;
end

if 0
  fh1=figure
                                %ax(1)=subplot(2,1,1);
  plot(y)
  grid on
  stop
end

if length(idx)>0
  y = y(idx);
end
if 0
  player = audioplayer (y, fs, 16);
  play (player);
end

t=(0:(length(y)-1))/fs;


NFFT=2048;
[WF,istart] = waterfall(y,NFFT/2,NFFT,0.25);
if 1
  WF2=10*log10(WF);
  f=((0:(NFFT-1))/NFFT-0.5)*fs/1000.;
  
  figure
  imagesc(t,f,WF2,max(WF2(:)) + [-40 0])
  colormap(jet)
  title('Waterfall')
  xlabel('Time (sec.)')
  ylabel('Freq (KHz)')
  colorbar;

  z=axis;
  axis([z(1) z(2) 0 fs/2000.])
end

mu=mean(WF);
sig2=var(WF);

figure
subplot(2,1,1)
plot(mu.^2)
hold on
plot(sig2)

subplot(2,1,2)
plot(sig2./(mu.^2))
grid on

%stop

fh1=figure
ax(1)=subplot(2,1,1);
plot(t,y)
grid on

% Design filters
N=5
fc=5000/(fs/2)
[B, A] = butter(N, fc,'high');
%[B1, A1] = butter(N, [200 600]/(fs/2.));
%[B2, A2] = butter(N, [1000 1500]/(fs/2.));
%[B1, A1] = butter(N, 3000/(fs/2.));
%[B2, A2] = butter(N, 4000/(fs/2.),'high');

[B1, A1] = ellip(N, 5,40,3000/(fs/2.));
%[B1, A1] = ellip(N, 5,40,[200 3000]/(fs/2.));
[B2, A2] = ellip(N, 5,40,4000/(fs/2.),'high');

if 1
  [H,w] = freqz(B,A);
  H=20*log10( abs(H) );
  [H1,w] = freqz(B1,A1);
  H1=20*log10( abs(H1) );
  [H2,w] = freqz(B2,A2);
  H2=20*log10( abs(H2) );
  
  figure
  plot(w*fs/(2*pi),H)
  hold on
  plot(w*fs/(2*pi),H1,'m')
  plot(w*fs/(2*pi),H2,'k')
  grid on
end

z=filter(B,A,y);
z1=filter(B1,A1,y);
z2=filter(B2,A2,y);

alpha=0.001
sq = filter(alpha,[1 alpha-1],abs(z));
sq1 = filter(alpha,[1 alpha-1],abs(z1));
sq2 = filter(alpha,[1 alpha-1],abs(z2));

figure(fh1)
ax(2)=subplot(2,1,2);
plot(t,z)
hold on
plot(t,sq,'r')
plot(t,sq1,'m')
plot(t,sq2,'k')
%plot(t,z1,'m')
%plot(t,z2,'k')
grid on

linkaxes(ax,'x')


figure
plot(sq1./sq2)
