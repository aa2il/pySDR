#! /usr/bin/python -u
################################################################################
#
# sdrplay.py - Rev 1.0
# Copyright (C) 2021 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Testing of SDRplay interface functions
#
# Notes:
#    - For whatever reason, we need to use -IF=0 for SRATE = 0.25 or >=2 MHz
#    - -offset doesn't seem quite right
#    - need to get control of RF gain
#
################################################################################
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
################################################################################

import sig_proc as dsp
import numpy as np
from pySDR_support import *
from pySDR_gui import *

################################################################################

# Experiment with Soapy interface
if True:
    from sdr_playpen import *
    P=RUN_TIME_PARAMS()
    sdrPlayPen(P)
    sys.exit(0)

# Plotting examples - this is in the demos area now
if False:
    import pyqtgraph.examples
    pyqtgraph.examples.run()
    sys.exit(0)
