#! /usr/bin/python
############################################################################
#
# srates.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Here's how to determine rate change params
#
############################################################################
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
############################################################################

from Tables import SDRplaysrates
from sig_proc import up_dn

############################################################################

for f1 in SDRplaysrates:
    fs1=int(f1*1e6)
    for f2 in [48e3,96e3,192e3]:
        fs2=int(f2)
        up,dn = up_dn(fs1,fs2)
        print(fs1/1e6,'\t',fs2/1e3,'\t',up,'\t',dn,'\t\t',fs1/dn/1000.,'\t',fs2/1000.)

#    RF fs      AF fs     Up     Down
#    0.25       48.0      24     125
#    0.25       96.0      48     125
#    0.25      192.0      96     125
#    0.5        48.0      12     125
#    0.5        96.0      24     125
#    0.5       192.0      48     125
#    1.0        48.0       6     125
#    1.0        96.0      12     125
#    1.0       192.0      24     125
#    2.0        48.0       3     125
#    2.0        96.0       6     125
#    2.0       192.0      12     125
#    2.048      48.0       3     128
#    2.048      96.0       3      64
#    2.048     192.0       3      32
#    3.0 	48.0 	2 	125 		24.0 	48.0
#    3.0 	96.0 	4 	125 		24.0 	96.0
#    3.0 	192.0 	8 	125 		24.0 	192.0
#    4.0 	48.0 	3 	250 		16.0 	48.0
#    4.0 	96.0 	3 	125 		32.0 	96.0
#    4.0 	192.0 	6 	125 		32.0 	192.0
#    5.0 	48.0 	6 	625 		8.0 	48.0
#    5.0 	96.0 	12 	625 		8.0 	96.0
#    5.0 	192.0 	24 	625 		8.0 	192.0
#    6.0 	48.0 	1 	125 		48.0 	48.0
#    6.0 	96.0 	2 	125 		48.0 	96.0
#    6.0 	192.0 	4 	125 		48.0 	192.0
#    7.0 	48.0 	6 	875 		8.0 	48.0
#    7.0 	96.0 	12 	875 		8.0 	96.0
#    7.0 	192.0 	24 	875 		8.0 	192.0
#    8.0 	48.0 	3 	500 		16.0 	48.0
#    8.0 	96.0 	3 	250 		32.0 	96.0
#    8.0 	192.0 	3 	125 		64.0 	192.0
#    9.0 	48.0 	2 	375 		24.0 	48.0
#    9.0 	96.0 	4 	375 		24.0 	96.0
#    9.0 	192.0 	8 	375 		24.0 	192.0
#   10.0 	48.0 	3 	625 		16.0 	48.0
#   10.0 	96.0 	6 	625 		16.0 	96.0
#   10.0 	192.0 	12 	625 		16.0 	192.0
