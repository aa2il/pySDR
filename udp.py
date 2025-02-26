#########################################################################################
#
# udp.py - Rev. 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# UDP messaging for pySDR.
#
############################################################################################
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
#########################################################################################

from tcp_server import *
from rig_io.socket_io import SetTXSplit
from utilities import freq2band
from Plotting import SPOT

#########################################################################################

# UDP Message handler for pySDR
def udp_msg_handler(self,sock,msg):

    P=self.P
    
    id=sock.getpeername()
    print('UDP MSG HANDLER: id=',id,'\tmsg=',msg.rstrip())
    
    msgs=msg.split('\n')
    for m in msgs:
        mm=m.split(':')
        print('UDP MSG HANDLER: m=',m,'\tmm[0]=',mm[0])

        if mm[0]=='SO2V':

            # Set SO2V mode
            P.SO2V = (mm[1]=='ON')
            P.ENABLE_AUTO_MUTE =  P.DXSPLIT or P.SO2V
            P.gui.MuteCB(0,not P.SO2V)
            print('UDP MSG HANDLER: mm=',mm,'\tSetting SO2V',P.SO2V)
            P.gui.so2v_cb.setChecked(P.SO2V)
            return

        elif mm[0]=='SPLIT':
            
            # Set Split for Chasing DX
            P.DXSPLIT = (mm[1]=='ON')
            P.ENABLE_AUTO_MUTE = P.DXSPLIT or P.SO2V
            print('UDP MSG HANDLER: mm=',mm,'\tSetting DX SPLIT',P.DXSPLIT)
            P.gui.split_cb.setChecked(P.DXSPLIT)
            P.gui.MuteCB(0,not P.DXSPLIT)
            return

        elif mm[0]=='Name':

            # Query server name
            if mm[1]=='?':
                print('UDP MSG HANDLER: Server name query')
                msg2='Name:pySDR\n'
                sock.send(msg2.encode())
            else:
                print('UDP MSG HANDLER: Server name is',mm[1])
            return
                
        elif mm[0]=='MODE':

            # Set mode
            if mm[1]=='?':
                print('UDP MSG HANDLER: Mode query')
                msg2='MODE:'+self.P.MODE+'\n'
                sock.send(msg2.encode())
            else:
                self.P.MODE=mm[1]
                self.P.gui.ModeSelect(-1)
                print('UDP MSG HANDLER: SDR mode set to',mm[1])
            return
                
        elif mm[0]=='SPOT':
            
            # Relay to bandmap
            #self.P.udp_client2.Send(m)
            print('UDP MSG HANDLER: Passing on SPOT message')
            return

        elif mm[0]=='SpotList':
            
            if mm[1]=='Refresh':
                
                # Relay to bandmap
                band=self.P.BAND
                msg='SpotList:'+band+':?\n'
                self.P.udp_client2.Send(msg)
                print('UDP MSG HANDLER: Passing on SPOT LIST REFRESH message')
                
            elif mm[1]!='?':
                
                band=mm[1]
                self.P.NEW_SPOT_LIST=eval(mm[2])
                print('UDP MSG HANDLER: New Spot List:',band,
                      self.P.NEW_SPOT_LIST,len(self.P.NEW_SPOT_LIST))
                
            return

        elif mm[0]=='LOG':

            # LOG:CALL:BAND:FREQ:MODE:DATE_OFF:TIME_OFF
            print('\nUDP: Received LOGged contact:',mm)

            call = mm[1]
            freq = float( mm[3] )
            c    = 'r'

            if False:
                # Add another spot - this leads to a big memory leak - wrong thread
                #print('\tcall=',call,'\tfreq=',freq)
                item=P.gui.plots_af.addSpot(freq,100,call,c)
                P.gui.Spots.append(SPOT(call,freq,c,item))

            elif False:
                # Change color of any spots for this callsign
                # This causes a smaller memory leak but let's try something else
                for spot in P.gui.Spots:
                    if spot.call==call:
                        spot.item.setColor('red')

            else:

                # Change color of any spots for this callsign -
                # Create list so this gets done in the proper thread
                self.P.CHANGE_SPOT_COLOR=[call,'red']
                
            return
            
        elif mm[0]=='RunFreq' and False:

            # This pathway uses the bandmap as the arbiter - more up to date but very slow
            if mm[1] in ['UP','DOWN']:
                self.P.udp_client2.Send(m)
            else:
                self.P.udp_client.Send(m)
                
            print('UDP MSG HANDLER: Relayed msg=',m)
            return
        
        elif mm[0]=='RunFreq' and mm[1] in ['UP','DOWN'] and True:

            # Just use whatever spots we already have
            frq=float(mm[2])
            band = freq2band(1e-3*frq)
            print('UDP MSG HANDLER: RunFreq - frq=',frq,'\tband=',band)
            spots = self.P.gui.Spots
            spots.sort(key=lambda x: x.freq, reverse=(mm[1]=='DOWN'))
            #print('spots=',spots)

            flast=None
            MIN_DF=1e-3*500
            for x in spots:
                f  = x.freq
                if not flast:
                    flast = f
                df = abs( f - flast )
                print(x.call,'\t',flast,'\t',f,'\t',df)
                if df>MIN_DF:
                    if (mm[1]=='UP'   and flast>=frq and f>frq) or \
                       (mm[1]=='DOWN' and flast<=frq and f<frq):
                        frq2=0.5*(f+flast)
                        msg='RunFreq:TRY:'+str(frq2)
                        print('UDP MSG HANDLER: RunFreq - Suggested freq=',frq2,
                              '\nSending msg=',msg)
                        #self.P.udp_server.Broadcast(msg)
                        sock.send(msg.encode())
                        return
                flast = f
            print('UDP MSG HANDLER: RunFreq - Unable to suggest a freq')
            return
                
        elif mm[0]=='SpotFreq' and mm[1] in ['UP','DOWN'] and True:

            # Just use whatever spaots we already have
            frq=float(mm[2])
            band = freq2band(1e-3*frq)
            print('UDP MSG HANDLER: SpotFreq - frq=',frq,'\tband=',band)
            spots = self.P.gui.Spots
            spots.sort(key=lambda x: x.freq, reverse=(mm[1]=='DOWN'))
            #print('spots=',spots)

            for x in spots:
                f  = x.freq
                print(x.call,'\t',f)
                if (mm[1]=='UP' and f>frq) or \
                   (mm[1]=='DOWN' and f<frq):
                        msg='SpotFreq:TRY:'+str(f)+':'+x.call+':A'
                        print('UDP MSG HANDLER: SpotFreq - Suggested freq=',f,
                              '\nSending msg=',msg)
                        #self.P.udp_server.Broadcast(msg)
                        sock.send(msg.encode())
                        return

            print('UDP MSG HANDLER: SpotFreq - Unable to find a spot freq')
            return
                
        print('UDP MSG HANDLER: Not sure what to do with this',mm)
        
