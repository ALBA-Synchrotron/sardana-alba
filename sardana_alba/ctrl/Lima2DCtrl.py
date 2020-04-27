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

#import time

from sardana import State
from sardana.pool.controller import TwoDController
from sardana.pool.controller import Type, MaxDimSize

import PyTango
import numpy


class LimaTwoDController(TwoDController):
    "This class is a Tango Sardana TwoD controller"

    gender = "Lima"
    model = "Basic"
    organization = "CELLS - ALBA"
    image = "Lima_ctrl.png"
    logo = "ALBA_logo.png"

    axis_attributes = {
        'ExposureTime': {
            Type: float,
            'R/W Type': 'READ_WRITE',
            'Description': 'Exposure time',
            'Defaultvalue': 1.0},
        'LatencyTime': {
            'Type': float,
            'R/W Type': 'READ_WRITE',
            'Description': 'Latency time',
            'Defaultvalue': 1.0},
        'NbFrames': {
            'Type': int,
            'R/W Type': 'READ_WRITE',
            'Description': 'Number of frames to be acquired',
            'Defaultvalue': 1},
        'TriggerMode': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'Mode in case of external trigger',
            'Defaultvalue': 'EXTERNAL_TRIGGER'},
        'FilePrefix': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'File prefix',
            'Defaultvalue': 'Img'},
        'FileFormat': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'File format',
            'Defaultvalue': 'EDF'},
        'FileDir': {
            'Type': str,
            'R/W Type': 'READ_WRITE',
            'Description': 'Directory path to save files',
            'Defaultvalue': '/tmp'},
        'NextNumber': {
            'Type': int,
            'R/W Type': 'READ_WRITE',
            'Description': 'File number for next image',
            'Defaultvalue': 1},
        'LastImageReady': {
            'Type': int,
            'R/W Type': 'READ',
            'Description': 'Image Id of last acquired image',
            },
        }

    ctrl_properties = {
        'DetectorDevice': {'type': str,
                           'description': 'Detector device name'
                           }
        }

    MaxDevice = 1

    StoppedMode = 0
    TimerMode = 1
    MonitorMode = 2
    CounterMode = 3

    BufferSize = 1024, 1024

    def __init__(self, inst, props, *args, **kwargs):
        TwoDController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug('Detector device: %s' % self.DetectorDevice)
        self.det = PyTango.DeviceProxy(self.DetectorDevice)
        self.det.write_attribute('saving_mode', 'MANUAL')

    def GetAxisAttributes(self, axis):
        # We fit the MaxDimSize to the actual image size
        size = self.det.read_attribute('image_sizes').value
        attrs = super(LimaTwoDController, self).GetAxisAttributes(axis)
        attrs['Value'][MaxDimSize] = tuple(size[2:4])
        return attrs

    def StateOne(self, axis):
        limaState = self.det.read_attribute('acq_status').value
        self._log.debug('SateOne [%s]' % limaState)
        if limaState == 'Ready':
            return State.Standby, limaState
        elif limaState == 'Running':
            return State.Running, limaState
        elif limaState == 'Configuration':
            return State.Init, limaState
        else:
            return State.Fault, limaState

    def ReadOne(self, axis):
        self._log.debug('ReadOne')
        dataSize = self.det.read_attribute('image_sizes').value
        data = self.det.command_inout('getImage', 0)
        if dataSize[1] == 2:
            data.dtype = 'uint16'
        elif dataSize[1] == 4:
            data.dtype = 'uint32'
        data.resize(dataSize[2], dataSize[3])

        img = numpy.float32(data)
        self._log.debug('Image data min %f max %f' % (img.min(), img.max()))
        return img

    def ReadAll(self):
        pass

    def PreStartOne(self, axis, position=None):
        self._log.debug("Prepare")
        try:
            self.det.prepareAcq()
        except:
            return False

        return True

    def StartOne(self, axis, position=None):
        pass

    def StartAll(self):
        self._log.debug("Start Acq")
        self.det.startAcq()

    def LoadOne(self, axis, value):
        self.det.write_attribute('acq_expo_time', value)

    def AbortOne(self, axis):
        self.det.stopAcq()

    def SetAxisExtraPar(self, axis, name, value):
        if name == 'ExposureTime':
            self.det.write_attribute('acq_expo_time', value)
        elif name == 'LatencyTime':
            self.det.write_attribute('latency_time', value)
        elif name == 'NbFrames':
            self.det.write_attribute('acq_nb_frames', value)
        elif name == 'TriggerMode':
            TrigList = ['INTERNAL_TRIGGER',
                        'INTERNAL_TRIGGER_MULTI',
                        'EXTERNAL_TRIGGER',
                        'EXTERNAL_TRIGGER_MULTI',
                        'EXTERNAL_GATE',
                        'EXTERNAL_START_STOP']
            if value in TrigList:
                self.det.write_attribute('acq_trigger_mode', value)
            else:
                self._log.error('Attribute TriggerMode: ' + 
                                'Not supported trigger mode (%s).' % (value))
        elif name == 'FilePrefix':
            self.det.write_attribute('saving_prefix', value)
        elif name == 'FileFormat':
            self.det.write_attribute('saving_format', value)
        elif name == 'FileDir':
            self.det.write_attribute('saving_directory', value)
        elif name == 'NextNumber':
            self.det.write_attribute('saving_next_number', value)

    def GetAxisExtraPar(self, axis, name):
        if name == 'ExposureTime':
            value = self.det.read_attribute('acq_expo_time').value
            self._log.debug('ExposureTime: %s' % value)
            return value
        elif name == 'LatencyTime':
            value = self.det.read_attribute('latency_time').value
            self._log.debug('LatencyTime: %s' % value)
            return value
        elif name == 'NbFrames':
            value = self.det.read_attribute('acq_nb_frames').value
            self._log.debug('NbFrames: %s' % value)
            return value
        elif name == 'TriggerMode':
            value = self.det.read_attribute('acq_trigger_mode').value
            self._log.debug('TriggerMode: %s' % value)
            return value
        elif name == 'FilePrefix':
            value = self.det.read_attribute('saving_prefix').value
            self._log.debug('FilePrefix: %s' % value)
            return value
        elif name == 'FileFormat':
            value = self.det.read_attribute('saving_format').value
            self._log.debug('FileFormat: %s' % value)
            return value
        elif name == 'FileDir':
            value = self.det.read_attribute('saving_directory').value
            self._log.debug('FileDir: %s' % value)
            return value
        elif name == 'NextNumber':
            value = self.det.read_attribute('saving_next_number').value
            self._log.debug('NextNumber: %s' % value)
            return value
        elif name == 'LastImageReady':
            value = self.det.read_attribute('last_image_ready').value
            self._log.debug('LastImageReady: %s' % value)
            return value
