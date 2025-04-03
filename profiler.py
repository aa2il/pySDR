############################################################################
#
# profiler.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Some functions to assist in identifying computational bottlenecks.
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

import cProfile
import time

############################################################################

class Profiler:
    def __init__(self,P):
        self.pr = cProfile.Profile()
        self.enabled = False
        self.P = P
        self.dT = P.OUT_CHUNK_SIZE/float(P.FS_OUT)
        self.ps = self.pr.print_stats

    def profile(self,txt=''):

        if self.enabled:
            self.pr.disable()
            self.enabled = False
            print('\n',txt,' - Profile for chunk',self.P.nchunks,':')
            print('\tNominal frame time =',self.dT,' secs.\n')
            self.ps(sort='time')

        elif (self.P.nchunks % 100) == 0:
            self.pr.enable()
            self.enabled = True


class Profiler2:
    def __init__(self):
        self.pr = cProfile.Profile()
        self.enabled = False
        self.triggered = False
        self.ps = self.pr.print_stats

    def start(self,txt=''):
        self.pr.enable()
        self.enabled = True
        self.triggered = True
        self.t1 = time.time()

    def stop(self,txt=''):

        if self.enabled:
            t2 = time.time()
            dT = t2-self.t1
            self.pr.disable()
            self.enabled = False
            print('\n',txt,' - Profile for chunk:')#  ,self.P.nchunks,':'
            print('\tNominal elapsed time =',dT,'secs. =',1000.*dT,'ms\n')
            self.ps(sort='time')


