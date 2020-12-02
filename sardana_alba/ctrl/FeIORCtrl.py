import tango
from sardana.pool.controller import IORegisterController, Type, Description, \
    Access, DataAccess
from sardana import State
from sardana.tango.core.util import from_tango_state_to_state


class FeIORController(IORegisterController):
    """

    """
      
    ctrl_properties = {
        'EpsDevice': {
            Type: str,
            Description: 'Name of EPS tango device'},
        'OpenFeAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which opens fe'},
        'CloseFeAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which closes fe'},
        'IsFeOpenedAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which indicates if '
                         'fe is opened'},
        'IsFeInterlockedAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which indicates '
                         'fe interlock'},
        'IsFeFirstValveClosedAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which indicates state '
                         'of the fe first valve'},
        'IsFeControlDisabledAttribute': {
            Type: str,
            Description: 'Name of the tango attribute which indicates if '
                         'control of the fe is disabled'}
    }

    axis_attributes = {
        'Labels': {Type: str,
                   Description: 'String list with meaning of the fe state',
                   Access: DataAccess.ReadWrite}
    }

    MaxDevice = 1

    def __init__(self, inst, props, *args, **kwargs):
        IORegisterController.__init__(self, inst, props, *args, **kwargs)
        if len(self.EpsDevice.split('/')) != 3:
            raise Exception('EpsDevice property is not properly set.')
        self.epsDevice = tango.DeviceProxy(self.EpsDevice)
        
    def AddDevice(self, axis):
        pass
        
    def DeleteDevice(self, axis):
        pass

    def StateOne(self, axis):
        try:
            state = from_tango_state_to_state(self.epsDevice.state())
        except Exception as e:
            state = State.Alarm
            status = 'Verifying state of eps tange device thrown the ' \
                     'following exception:\n {}'.format(e)
            return state, status

        status = 'The EPS device is in {}'.format(repr(state))
        isFeControlDisabled = self.epsDevice.read_attribute(
            self.IsFeControlDisabledAttribute).value
        if isFeControlDisabled:
            state = State.Alarm
            status += '\nControl over fe is disabled from the Control Room'

        isFeFirstValveClosed = self.epsDevice.read_attribute(
            self.IsFeFirstValveClosedAttribute).value
        if isFeFirstValveClosed:
            state = State.Alarm
            status += '\nFirst valve of the fe is closed'

        isFeInterlocked = self.epsDevice.read_attribute(
            self.IsFeInterlockedAttribute).value
        if isFeInterlocked:
            state = State.Alarm
            status += '\nfe is interlocked'
        return state, status

    def ReadOne(self, axis):
        isFeOpened = self.epsDevice.read_attribute(
            self.IsFeOpenedAttribute).value
        return int(isFeOpened)
        
    def WriteOne(self, axis, value):        
        if value == 1:
            self.epsDevice.write_attribute(self.OpenFeAttribute, True)
        elif value == 0:
            self.epsDevice.write_attribute(self.CloseFeAttribute, True)
        else:
            raise ValueError("This ior accepts only 0 and 1 values")
    
    def GetAxisExtraPar(self, axis, name):
        if name.lower() == 'labels':
            return "Open:1 Close:0"
  
    def SetAxisExtraPar(self, axis, name, value):
        pass
