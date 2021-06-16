close all
clear all
more off

fp=fopen('LOG1.TXT');
tt=[];
nn=[];
i=0;
while !feof(fp)
  i=i+1;
  b=fgetl(fp);
  tt(i)=str2num(b(3:20));
  nn(i)=str2num(b(71:77));
  
  c=fgetl(fp);
end
fclose(fp)
tt
nn

%return

a=load('LOG2.TXT');

rb_size = a(1,1)
fs = a(1,2)
half = .5*rb_size         %/fs
upper = .75*rb_size       %/fs
lower = .25*rb_size       %/fs

a=a(2:end,:);
t0=a(1,1)
t=(a(:,1)-t0)/3600.;
latency = a(:,2);

N=101;
h=ones(N,1)/N;
avg = conv(latency,h,'same');

filt(1)=latency(1);
total_correction=0
for i=2:length(latency)
  if i<100 
    alpha=1./i;
  else
    alpha=0.01;
  end
  filt(i) = (1-alpha)*filt(i-1) + alpha*latency(i);

  corrected(i)=(filt(i)-half) + total_correction;
  if i>10 && corrected(i)<-2*1024
    fprintf('Adjusting up at i=%d\n',i)
    total_correction=total_correction+1024
  elseif i>10 && corrected(i)>2*1024
    fprintf('Adjusting down at i=%d\n',i)
    total_correction=total_correction-1024
  end
end

plot(t,latency)
hold on
plot(t,avg,'r')
plot(t,filt,'y')
plot(t,corrected+half,'m')
plot([t(1) t(end)],[half half],'g')
plot([t(1) t(end)],[upper upper],'g')
plot([t(1) t(end)],[lower lower],'g')

tt=(tt-t0)/3600.;
plot(tt,nn,'k*')

xlabel('Time (Hours)')
ylabel('Latency (sec.)')
grid on
axis([t(1) t(end) 0 2*half])

return

figure
plot(t,(filt-half)/1024,'r')
hold on
plot([t(1) t(end)],[0 0],'g')
plot([t(1) t(end)],[half half]/1024,'g')
plot([t(1) t(end)],-[half half]/1024,'g')

xlabel('Time (Hours)')
ylabel('Latency (sec.)')
grid on
%axis([t(1) t(end) 0 2*half])

         
