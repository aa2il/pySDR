% Script to convert an SDR demod file to WAV format

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
%user=getenv('USER');
fname = 'demod_20191028_010040.dat'
#fname = 'baseband_iq_20190208_194246.dat'


% Some code to get WAVE file stuff working again in python code - don't usually do thi
if 0
  fname='demod_20191028_012145.wav'
  [y,fs,nbits]=wavread(fname);
  
  y(1:10,:)
  size(y)
  fs
  nbits
  figure
  plot(y)
  return
end


% Read SDR file
[y,hdr,str]=read_sdr_data(fname);

disp ' '
N=length(y)
hdr
fs=hdr(1)
nchan=hdr(4)
disp ' '

% Consturct output file name
[d,n,e]=fileparts(fname)
fout = [d n '.wav']

% Write wave file
y(1:10)
yy=[real(y) , imag(y)];
yy(1:10,:)
wavwrite(yy,fs,fout)

% Plot it
if 1
  figure
  plot(real(y),'b')
  hold on
  plot(imag(y),'r')
  grid on
end

% Play it
if 1
  player=audioplayer(y,fs)
  play(player)
end


disp 'Done.'


