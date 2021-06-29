##############################################################################
##
## This file is part of Sardana
##
## http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Sardana is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Sardana is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
##
##############################################################################
import time
import numpy

import PyTango
import taurus

from sardana import State
from sardana.pool.controller import CounterTimerController, Memorized
from sardana.pool import AcqTriggerType

        
class AmptekPX5CounterTimerController(CounterTimerController):
    "This class is the AmptekPX5 Sardana CounterTimerController"

    MaxDevice = 17

    class_prop = {'deviceName':{'Type':str,'Description':'AmptekPX5 Tango device name','DefaultValue':None},}

    axis_attributes = { "lowThreshold"   : { "Type" : long, "R/W Type": "READ_WRITE" },
                        "highThreshold" : { "Type" : long, "R/W Type": "READ_WRITE" }}

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.amptekPX5 = taurus.Device(self.deviceName)
        self.amptekPX5.set_timeout_millis(7000)
        self.acqTime = 0
        self.sta = State.On
        self.acq = False
        self.timeout = 0 #not need for now

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("SetAxisExtraPar() entering...")
        if axis == 1:
            raise Exception("Axis parameters are not allowed for axis 1.")
        name = name.lower()
        scai = axis - 1
        if name == "lowthreshold":
            conf = ["SCAI=%d"%scai, "SCAL"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
        elif name == "highthreshold":
            conf = ["SCAI=%d"%scai, "SCAH"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
        v = long(ret[1].split("=")[1])
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        if axis == 1:
            raise Exception("Axis parameters are not allowed for axis 1.")
        name = name.lower()
        scai = axis - 1
        if name == "lowthreshold":
            conf = ["SCAI=%d"%scai, "SCAH"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
            scah = long(ret[1].split("=")[1])
            conf = ["SCAI=%d"%scai, "SCAL=%d"%value, "SCAH=%d"%scah]
            for c in conf:
                self._log.debug("conf: %s" % repr(c))
                self.amptekPX5.SetTextConfiguration([c])
        elif name == "highthreshold":
            conf = ["SCAI=%d"%scai, "SCAL"]
            ret = self.amptekPX5.GetTextConfiguration(conf)
            scal = long(ret[1].split("=")[1])
            conf = ["SCAI=%d"%scai, "SCAL=%d"%scal, "SCAH=%d"%value]
            for c in conf:
                self._log.debug("conf: %s" % repr(c))
                self.amptekPX5.SetTextConfiguration([c])

    def AddDevice(self,ind):
        pass

    def DeleteDevice(self,ind):
        pass

    def PreStateAll(self):
        pass

    def PreStateOne(self, ind):
        pass

    def StateAll(self):
        self._log.debug("StateAll(): entering...")
        #to fixed the callback error
        dt = time.time() - self.t1

        if dt < self.timeout:
            return
        sta = self.amptekPX5.State()
        self.status = self.amptekPX5.Status()
        self._log.info("AmptekPX5CounterTimerController StateOne - state = %s" % repr(sta))
        if self.sta == State.Moving and sta != State.Moving:
            self.acq = False
            self.sca_values = self.amptekPX5.LatchGetClearSCA()
        self.sta = sta
        self.t1 = time.time()
        
        
    def StateOne(self, ind):
        return self.sta, self.status

    def PreReadAll(self):
        pass

    def PreReadOne(self,ind):
        pass

    def ReadAll(self):
        pass

    def ReadOne(self, ind):
        self._log.debug("ReadOne(%d): entering..." % ind)
        if ind == 1:
            val = self.acqTime
        else:
            val = self.sca_values[ind-2]
        self._log.debug("ReadOne(%d): returning %d" % (ind,val))
        return val

    def PreStartAllCT(self):
        self.amptekPX5.ClearSpectrum()
        self.amptekPX5.LatchGetClearSCA()
        self.sca_values = [0] * 16

    def PreStartOneCT(self, ind):
        return True

    def StartOneCT(self, ind):
        pass

    def StartAllCT(self):
        self._log.debug("StartAllCT(): entering...")
        self.amptekPX5.Enable()
        self.acq = True

    def LoadOne(self, ind, value):
        self._log.debug("LoadOne(): entering...")
        self.acqTime = value
        self.amptekPX5.SetTextConfiguration(['PRET=%f'%value])

    def AbortOne(self, ind):
        self.amptekPX5.Disable()


class AmptekPX5SoftCounterTimerController(CounterTimerController):
    """"This class is the AmptekPX5 Sardana CounterTimerController.
     Its first channel is an acquisition timer. It is used to preset the acquisition time.
     Its second channel is a Fast Counter (Incoming Count Rate ICR). 
     It counts all the incoming events.
     Its third channel is a Slow Counter (Total Count Rate TCR). 
     Any event that is counted in the spectrum is also counter here.
     Rest of the channels are software ROI of the spectrum - so called SCAs."""

    MaxDevice = 17

    class_prop = {'deviceName':{'Type':str,'Description':'AmptekPX5 Tango device name','DefaultValue':None},}

    axis_attributes = { "lowThreshold"   : { "Type" : long, "R/W Type": "READ_WRITE", "memorized":Memorized },
                        "highThreshold" : { "Type" : long, "R/W Type": "READ_WRITE", "memorized":Memorized }
                      }

    def __init__(self, inst, props, *args, **kwargs):
        CounterTimerController.__init__(self, inst, props, *args, **kwargs)
        self.amptekPX5 = taurus.Device(self.deviceName)
        self.amptekPX5.SetTextConfiguration(['MCAC=%d'%4096])
        self.amptekPX5.set_timeout_millis(7000)
        self.acqTime = 0
        self.sta = State.On
        self.acqStartTime = None
        self.spectrum = None
        self.icr = None
        self.tcr = None
        self.scas = {}

    def GetAxisExtraPar(self, axis, name):
        self._log.debug("GetAxisExtraPar() entering...")
        if axis in [1,2,3]:
            raise Exception("Axis parameters are not allowed for axes 1 and 2.")
        name = name.lower()
        v = self.scas[axis][name]
        return v

    def SetAxisExtraPar(self, axis, name, value):
        self._log.debug("SetAxisExtraPar() entering...")
        if axis in [1,2,3]:
            raise Exception("Axis parameters are not allowed for axes 1 and 2.")
        name = name.lower()
        self.scas[axis][name] = value

    def AddDevice(self,ind):
        self._log.debug("AddDevice() entering...")
        if not (ind in [1,2,3]):
            self.scas[ind] = {"lowthreshold":0, "highthreshold":0}
        self._log.debug("AddDevice() leaving...")

    def DeleteDevice(self,ind):
        self.scas.pop(ind)

    def PreStateAll(self):
        pass

    def PreStateOne(self, ind):
        pass

    def StateAll(self):
        self._log.debug("StateAll(): entering...")
        if self.acqStartTime != None: #acquisition was started
            now = time.time()
            elapsedTime = now - self.acqStartTime
            if elapsedTime < self.acqTime: #acquisition has probably not finished yet
                self.sta = State.Moving
                self.status = "Acqusition time has not elapsed yet."
                return
            else:
                self.acqStartTime = None
        try:
            self.sta = self.amptekPX5.State()
        except PyTango.DevFailed, e:
            self.amptekPX5.ClearInputBuffer()
            self.sta = self.amptekPX5.State()
        self.status = self.amptekPX5.Status()


    def StateOne(self, ind):
        self._log.debug("StateOne(%d): entering..." % ind)
        return self.sta, self.status

    def ReadAll(self):
        self._log.debug("ReadAll(): entering...")
        if self.sta != State.Moving and self.spectrum == None: #reading only once and only if we are not in the middle of acquisition
            self.spectrum = self.amptekPX5.read_attribute("Spectrum").value
        self._log.debug("ReadAll(): leaving...")

    def ReadOne(self, ind):
        self._log.debug("ReadOne(%d): entering..." % ind)
        if self.spectrum == None: #acquisition has not finished yet
            val = 0
        else:
            if ind == 1: #timer
                val = self.acqTime
            elif ind == 2: #icr
                if self.icr == None:
                    self.icr = self.amptekPX5.read_attribute("FastCount").value
                val = self.icr
            elif ind == 3: #tcr
                if self.tcr == None:
                    self.tcr = self.amptekPX5.read_attribute("SlowCount").value
                val = self.tcr
            else: #calculating software ROIs
                lowThreshold = self.scas[ind]['lowthreshold']
                highThreshold = self.scas[ind]['highthreshold']
                val = numpy.sum(self.spectrum[lowThreshold:highThreshold])
        self._log.debug("ReadOne(%d): returning %d" % (ind,val))
        return val

    def PreStartAllCT(self):
        self.amptekPX5.ClearSpectrum()

    def PreStartOneCT(self, ind):
        return True

    def StartOneCT(self, ind):
        pass

    def StartAllCT(self):
        self._log.debug("StartAllCT(): entering...")
        self.spectrum = None
        self.icr = None
        self.tcr = None
        self.amptekPX5.Enable()
        self.acqStartTime = time.time()
        self.sta = State.Moving
        self.status = "Acquisition was started"
        self._log.debug("StartAllCT(): leaving...")

    def LoadOne(self, ind, value):
        self._log.debug("LoadOne(): entering...")
        if value < 0.1:
            raise Exception("AmptekPX5 does not support acquisition times lower than 0.1 second")
        self.amptekPX5.SetTextConfiguration(['PRET=%f'%value])
        self.acqTime = float(self.amptekPX5.GetTextConfiguration(['PRET'])[0].split('=')[1])
        self._log.debug("LoadOne(): leaving...")

    def AbortOne(self, ind):
        self.amptekPX5.Disable()
