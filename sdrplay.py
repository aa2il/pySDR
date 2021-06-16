#! /usr/bin/python

# Testing of SDRplay interface functions

# Notes:
#    - For whatever reason, we need to use -IF=0 for SRATE = 0.25 or >=2 MHz
#    - -offset doesn't seem quite right
#    - need to get control of RF gain

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

# Plotting examples
if False:
    import pyqtgraph.examples
    pyqtgraph.examples.run()
    sys.exit(0)
