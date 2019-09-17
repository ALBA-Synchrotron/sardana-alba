import PyTango, taurus

from sardana import pool
from sardana.pool.controller import IORegisterController

class FeIORController(IORegisterController):
    ""
      
    class_prop = { 'EpsDevice' :{'Type' : 'PyTango.DevString', 'Description' : 'Name of EPS tango device'},
                   'OpenFeAttribute' :{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which opens fe'},
                   'CloseFeAttribute':{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which closes fe'},
                   'IsFeOpenedAttribute':{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which indicates if fe is opened'},
                   'IsFeInterlockedAttribute' :{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which indicates fe interlock'},
                   'IsFeFirstValveClosedAttribute' :{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which indicates state of the fe first valve'},
                   'IsFeControlDisabledAttribute' :{'Type' : 'PyTango.DevString', 'Description' : 'Name of the tango attribute which indicates if control of the fe is disabled'}
                  }

    ctrl_extra_attributes = { 'Labels': {'Type':'PyTango.DevString', 'Description':'String list with meaning of the fe state', 'R/W Type':'PyTango.READ_WRITE'} }

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        if len(self.EpsDevice.split('/')) != 3:
            raise Exception('EpsDevice property is not properly set.')
        self.epsDevice = taurus.Device(self.EpsDevice)
        
    def AddDevice(self, axis):
        pass
        
    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        try:
            state = self.epsDevice.state()
        except Exception, e: 
            return (PyTango.DevState.ALARM,'Verifying state of eps tange device thrown the following exception:\n %s' % str(e))
        status = 'The EPS device is in %s' % repr(state)
        isFeControlDisabled = self.epsDevice.read_attribute(self.IsFeControlDisabledAttribute).value
        if isFeControlDisabled:
            state = PyTango.DevState.ALARM
            status += '\nControl over fe is disabled from the Control Room'
        isFeFirstValveClosed = self.epsDevice.read_attribute(self.IsFeFirstValveClosedAttribute).value
        if isFeFirstValveClosed:
            state = PyTango.DevState.ALARM
            status += '\nFirst valve of the fe is closed'
        isFeInterlocked = self.epsDevice.read_attribute(self.IsFeInterlockedAttribute).value
        if isFeInterlocked:
            state = PyTango.DevState.ALARM
            status += '\nfe is interlocked'
        return (state, status)

    def ReadOne(self, axis):
        isFeOpened = self.epsDevice.read_attribute(self.IsFeOpenedAttribute).value
        return int(isFeOpened)
        
    def WriteOne(self, axis, value):        
        if value == 1:
            openFeAttr = self.epsDevice.write_attribute(self.OpenFeAttribute, True)
        elif value == 0:
            closeFeAttr = self.epsDevice.write_attribute(self.CloseFeAttribute, True)
        else:
          raise ValueError("This ior accepts only 0 and 1 values")
    
    def GetExtraAttributePar(self, axis, name):
        if name.lower() == 'labels':
            return "Open:1 Close:0"
  
    def SetExtraAttributePar(self,axis, name, value):
        pass