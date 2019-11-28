from sardana.macroserver.macro import macro, Macro, Type
import PyTango
import time


class XBPMspectra(Macro):
    """ 
    Macro to execute a sequence of scans to calibrate the XBPM of the beamlines
    """
    
    param_def = [['firstValue', Type.Float, 0, 'Value'],
                ]
    
    def prepare(self, *args):
        try:
            dev_name = self.getEnv('XbpmPySignal')
            dev = PyTango.DeviceProxy(dev_name)
            
            properties = ['ScanMotor', 'PhaseMotor', 'MagneticField', 
                          'MagneticField',  'XbpmHMotor', 'XbpmVMotor',
                          'MntGrp']
            properties_values = dev.get_property(properties)
            self.scan_motor = properties_values['ScanMotor'][0]
            self.phase_motor = properties_values['PhaseMotor'][0]
            self.mag_field = properties_values['MagneticField'][0] == 'True'
            self.xbpm_h = properties_values['XbpmHMotor'][0]
            self.xbpm_v = properties_values['XbpmVMotor'][0]
            self.mg = properties_values['MntGrp'][0]
            
            self.scan_values = dev.read_attribute('ScanValues').value
            self.phase_values = dev.read_attribute('PhaseValues').value
            self.scan_range = dev.read_attribute('ScanRange').value
            self.scan_steps = dev.read_attribute('ScanSteps').value
            self.scan_itime = dev.read_attribute('ScanIntTime').value
            self.scan_file = dev.read_attribute('ScanFile').value
            self.scan_dir = dev.read_attribute('ScanDir').value
            self.bck_id_gap = None
            
        except Exception, e:
            msg = ''
            raise Exception(e)
    
    def _saveIDConfig(self):
        if self.mag_field:
            #Implement the way to save the value in BL04
            self.phase_values=[0]
 
        else:
            #Implement the way to save the value in other beamlines
            id_gap = PyTango.DeviceProxy(self.scan_motor)
            self.bck_id_gap = id_gap.read_attribute('Position').value
            if self.phase_motor != 'None':
                id_phase = PyTango.DeviceProxy(self.phase_motor)
                self.bck_id_phase = id_phase.read_attribute('Position').value
            else:
                self.phase_values = [0]
                self.bck_id_phase = 0 
    
    def _loadIDConfig(self):
        if not self.bck_id_gap:
            self._moveID(self.bck_id_gap, self.bck_id_phase)
        else:
            self.error('bck_id_gap is None. The saveIDConfig did not work')
                
    def _moveID(self, scan_value, phase_value):
        if self.mag_field:
            #Implement the way to save the value in BL04
            pass
        else:
            #Implement the way to save the value in other beamlines
            self.execMacro('mv %s %f' %(self.scan_motor, scan_value))
            if self.phase_motor != 'None':
                self.execMacro('mv %s %f' %(self.phase_motor, 
                                            phase_value))
    def run(self, firstValue):
        bck_scan_file = self.getEnv('ScanFile')
        bck_scan_dir = self.getEnv('ScanDir')
        bck_mg = self.getEnv('ActiveMntGrp')
        self.setEnv('ScanFile', self.scan_file)
        self.setEnv('ScanDir', self.scan_dir)
        self.setEnv('ActiveMntGrp', self.mg)
        try:
            self._saveIDConfig()
            for scan_value in self.scan_values:
                if scan_value >= firstValue:
                    for phase_value in self.phase_values: 
                        self._moveID(scan_value, phase_value)
                        mesh_macro = ('mesh %s %f %f %d %s %f %f %d %f' % 
                                      (self.xbpm_h, self.scan_range[0], 
                                       self.scan_range[1], self.scan_steps,
                                       self.xbpm_v, self.scan_range[0], 
                                       self.scan_range[1], self.scan_steps,
                                       self.scan_itime))
                    
                        self.execMacro(mesh_macro)
                        #TODO: Verified if it's possible to move both motor
                        #together
                        self.execMacro('mv %s 0 %s 0' % (self.xbpm_h,
                                                         self.xbpm_v))
        except Exception, e:
            self.error('Error with the scan %s' % str(e))
            
        finally:
            self.setEnv('ScanFile', bck_scan_file)
            self.setEnv('ScanDir', bck_scan_dir)
            self.setEnv('ActiveMntGrp', bck_mg)
            self._loadIDConfig()
        