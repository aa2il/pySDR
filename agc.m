% Script to examine AGC loop filter

clear all
close all

beta=.1

b=beta
a=[1 beta-1]

x=[zeros(1,100) ones(1,100)];
y=filter(b,a,x);

figure
subplot(2,1,1)
[h,w] = freqz(b,a);
plot(w,20*log10(abs(h)))
xlabel('Frequency (rad/sample)')
ylabel('Magnitude (dB)')

subplot(2,1,2)
plot(x)
hold on
plot(y,'r')
