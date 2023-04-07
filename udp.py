#########################################################################################
#
# udp.py - Rev. 1.0
# Copyright (C) 2022-3 by Joseph B. Attili, aa2il AT arrl DOT net
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
            if mm[1]=='ON':
                P.SO2V=True
            else:
                P.SO2V=False
            print('UDP MSG HANDLER: mm=',mm,'\tSetting SO2V',P.SO2V)
            P.gui.so2v_cb.setChecked(P.SO2V)
            self.P.MUTED[0]=False
            P.gui.MuteCB(0,True)
            return

        elif mm[0]=='SPLIT':
            if mm[1]=='ON':
                P.DXSPLIT=True
            else:
                P.DXSPLIT=False
            print('UDP MSG HANDLER: mm=',mm,'\tSetting DX SPLIT',P.DXSPLIT)
            P.gui.split_cb.setChecked(P.DXSPLIT)

            #df=1  # Defaults to 1 KHz UP
            #SetTXSplit(self.P,df)
            
            self.P.MUTED[0]=False
            P.gui.MuteCB(0,True)
            return

        elif mm[0]=='Name':
            if mm[1]=='?':
                print('UDP MSG HANDLER: Server name query')
                msg2='Name:pySDR\n'
                sock.send(msg2.encode())
            else:
                print('UDP MSG HANDLER: Server name is',mm[1])
            return
                
        elif mm[0]=='SpotList':
            if mm[1]=='Refresh':
                band=self.P.BAND
                msg='SpotList:'+band+':?\n'
                self.P.udp_client2.Send(msg)
            elif mm[1]!='?':
                band=mm[1]
                self.P.NEW_SPOT_LIST=eval(mm[2])
                print('UDP MSG HANDLER: New Spot List:',band,self.P.NEW_SPOT_LIST)
            return

        print('UDP MSG HANDLER: Not sure what to do with this',mm)
        
