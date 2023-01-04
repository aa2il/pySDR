#########################################################################################
#
# udp.py - Rev. 1.0
# Copyright (C) 2022 by Joseph B. Attili, aa2il AT arrl DOT net
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

from tcp_client import *

#########################################################################################

# UDP Message handler for pySDR
def udp_msg_handler(self,sock,msg):

    #P=udp_msg_handler.P
    P=self.P
    
    id=sock.getpeername()
    print('UDP MSG HANDLER: id=',id,'\tmsg=',msg.rstrip())
    
    msgs=msg.split('\n')
    for m in msgs:
        print('UDP MSG HANDLER: m=',m,len(m))

        mm=m.split(':')
        if mm[0]=='SO2V':
            if mm[1]=='ON':
                P.SO2V=True
            else:
                P.SO2V=False
            print('UDP MSG HANDLER: mm=',mm,'\tSetting SO2V',P.SO2V)
            P.gui.so2v_cb.setChecked(P.SO2V)
            self.P.MUTED[0]=False
            P.gui.MuteCB(0,True)

        elif mm[0]=='Name':
            if mm[1]=='?':
                print('UDP MSG HANDLER: Server name query')
                msg2='Name:pySDR\n'
                sock.send(msg2.encode())
            else:
                print('UDP MSG HANDLER: Server name is',mm[1])
                
        
# Function to open UDP client
def open_udp_client(P,port):
    
    #udp_msg_handler.P=P
    
    try:
        
        print('Opening UDP client ...')
        P.udp_client = TCP_Client(P,None,port,Handler=udp_msg_handler)
        worker = Thread(target=P.udp_client.Listener,args=(), kwargs={}, name='UDP Client' )
        worker.setDaemon(True)
        worker.start()
        P.threads.append(worker)
        return True
    
    except Exception as e:
        
        print(e)
        print('--- Unable to connect to UDP socket ---')
        P.udp_client = None
        return False
    
