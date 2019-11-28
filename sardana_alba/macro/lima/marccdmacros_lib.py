"""
    Macros for data acquisition with Marccd specific DS
"""

import PyTango
import time
import functools

from sardana.macroserver.macro import Macro, Type



def catch_error(meth):
    @functools.wraps(meth)
    def _catch_error(self, *args, **kws):
        try:
            return meth(self, *args, **kws)
        except Exception as e:
            self.error("Could not comunicate with %s. Check if device server is exported.\n" % args[0])
            self.debug(e)
            raise e
    return _catch_error



class marccd_takebg(Macro):
    """Take background images. (In fact are dark current images)"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['path',Type.String, '/', 'Path to save background']]

    @catch_error
    def run(self,dev,path):
        marccd = PyTango.DeviceProxy(dev + "_custom")
        if path == '/':
            marccd.takeBackgroundFrame()
        else:
            lima = PyTango.DeviceProxy(dev)
            marccd.saveBG()
            prefix = "BG" + time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
            self.execMacro(['lima_take', dev, path, 0.5, 3, 1, prefix, "EDF"])


class marccd_camstatus(Macro):
    """ Returns Marccd camera status"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['camstat',Type.Integer, None, 'Camera status']]

    @catch_error
    def run(self,dev):
        marccd = PyTango.DeviceProxy(dev + "_custom")
        value = marccd.read_attribute('cam_state').value
        return value



class marccd_getheader(Macro):
    """Returns the desired header value
Header list:
    beam_x         integration_time      acquire_timestamp    counts
    beam_y         exposure_time         header_timestamp     mean  
    distance       readout_time          save_timestamp       rms   
    pixelsize_x    wavelength            mean_bias            
    pixelsize_y    photons_per_100adu"""

    param_def  = [['dev',Type.String, None, 'Device name or alias'],
                  ['paramIn',Type.String, None, 'Parameter name.']]
    result_def = [['paramOut',Type.String, None, 'Parameter value']]

    @catch_error
    def run(self,dev,param):
        marccd = PyTango.DeviceProxy(dev + "_custom")

        Param = {'beam_x':            'header_beam_x',
                 'beam_y':            'header_beam_y',
                 'distance':          'header_distance',
                 'pixelsize_x':       'header_pixelsize_x',
                 'pixelsize_y':       'header_pixelsize_y',
                 'integration_time':  'header_integration_time',
                 'exposure_time':     'header_exposure_time',
                 'readout_time':      'header_readout_time',
                 'wavelength':        'header_wavelength',
                 'acquire_timestamp': 'header_acquire_timestamp',
                 'header_timestamp':  'header_header_timestamp',
                 'save_timestamp':    'header_save_timestamp',
                 'mean_bias':         'header_mean_bias',
                 'photons_per_100adu':'header_photons_per_100adu',
                 'counts':            'header_counts',
                 'mean':              'header_mean',
                 'rms':               'header_rms'
            }

        value = marccd.read_attribute(Param[param]).value
        return str(value)



class marccd_set_beam(Macro):
    """Sets beam possition"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['X',Type.Float, None, 'X possition'],
                  ['Y',Type.Float, None, 'Y possition']]

    @catch_error
    def run(self, dev, X, Y):
        lima = PyTango.DeviceProxy(dev + "_custom")
        lima.write_attribute('source_beam_x', X)
        lima.write_attribute('source_beam_y', Y)


class marccd_set_beam_x(Macro):
    """Sets beam possition"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['X',Type.Float, None, 'X possition'],]

    @catch_error
    def run(self, dev, X):
        lima = PyTango.DeviceProxy(dev + "_custom")
        lima.write_attribute('source_beam_x', X)

class marccd_set_beam_y(Macro):
    """Sets beam possition"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['Y',Type.Float, None, 'X possition'],]

    @catch_error
    def run(self, dev, Y):
        lima = PyTango.DeviceProxy(dev + "_custom")
        lima.write_attribute('source_beam_y', Y)


class marccd_set_distance(Macro):
    """Sets source distance"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['D',Type.Float, None, 'Distance']]

    @catch_error
    def run(self, dev, D):
        lima = PyTango.DeviceProxy(dev + "_custom")
        lima.write_attribute('source_distance', D)



class marccd_set_wavelength(Macro):
    """Sets source wavelength"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['W',Type.Float, None, 'Wavelength']]

    @catch_error
    def run(self, dev, W):
        lima = PyTango.DeviceProxy(dev + "_custom")
        lima.write_attribute('source_wavelength', W)


