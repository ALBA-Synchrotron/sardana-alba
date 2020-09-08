"""
    Macros for data acquisition with LimaCCDs DS
"""
import taurus
import PyTango
import os, errno
import time
import functools

from sardana.macroserver.macro import Macro, Type, ParamRepeat


def catch_error(meth):
    @functools.wraps(meth)
    def _catch_error(self, *args, **kws):
        try:
            return meth(self, *args, **kws)
        except Exception as e1:
            self.debug(e1)
            try:  
                self.error("Macro %s failed with argument %s" %(meth.__name__ , " ".join(args)))
            except Exception as e2:
                self.error("Error processing  _catch_error, args[0].")
            finally:
                raise e1
    return _catch_error



class lima_status(Macro):
    """Returns device and acquisition status."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def =  [['state_and_status',Type.String, None, 
                    'Device State and Acquisition Status']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        state = '%s %s' % (lima.State(), 
                           lima.read_attribute('acq_status').value)
        return state



class lima_saving(Macro):
    """Configure data storage."""

    param_def = [['dev',Type.String, None, 'Device name or alias'],
                 ['BaseDir', Type.String, None, 
                  'Base directory to store data.'],
                 ['Prefix', Type.String, None, 'Prefix for the experiment.'],
                 ['Format', Type.String, 'EDF', 'File format'],
                 ['Autosave' , Type.Boolean, True, 
                  'Flag to save all frames automatically'],
                 ['NextNumber', Type.Integer, 0, 'Number for the first image']
                 ]

    @catch_error
    def run(self,dev,basedir,prefix,fileformat,auto,next):
        lima = taurus.Device(dev)
        lima.set_timeout_millis(30000)


        if auto:
            self.debug('Writing saving_mode to AUTO_FRAME')
            lima.write_attribute('saving_mode', 'AUTO_FRAME')
        else:
            self.debug('Writing saving_mode to MANUAL')
            lima.write_attribute('saving_mode', 'MANUAL')
            
        if not os.path.exists(basedir):
            try:
                os.makedirs(basedir)
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise

        self.debug('Writing saving_directory to %s' % basedir)
        lima.write_attribute('saving_directory', basedir)
        self.debug('Writing saving_prefix to %s' % prefix)
        lima.write_attribute('saving_prefix', prefix)
        self.debug('Writing saving_format to %s' % fileformat)
        lima.write_attribute('saving_format', fileformat)
#        self.debug('Writing image next number to %s' % next)
#        lima.write_attribute('saving_next_number', next)



class lima_prepare(Macro):
    """Prepare a set of NF frames with Texp exposure time and Tlat latency time.
Trigger modes are:
  INTERNAL_TRIGGER    EXTERNAL_TRIGGER_MULTI    EXTERNAL_START_STOP
  EXTERNAL_TRIGGER    EXTERNAL_GATE"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['Texp', Type.Float, 1.0, 'Exposure time.'],
                  ['Tlat', Type.Float, 0.0, 'Latency time.'],
                  ['NF', Type.Integer, 1, 'Number of frames.'],
                  ['Trig', Type.String, 'INTERNAL_TRIGGER', 'Trigger mode.']]

    @catch_error
    def run(self,dev,Texp,Tlat,NF,Trig):
        lima = taurus.Device(dev)
        lima.set_timeout_millis(30000)

        TrigList = ['INTERNAL_TRIGGER'
                    ,'EXTERNAL_TRIGGER'
                    ,'EXTERNAL_TRIGGER_MULTI'
                    ,'EXTERNAL_GATE'
                    ,'EXTERNAL_START_STOP']
        
        if Trig not in TrigList:
            self.info("Error, Trigger mode %s not accepted." % Trig)

        lima.write_attribute('acq_trigger_mode', Trig)

        lima.write_attribute('acq_nb_frames', NF)
        lima.write_attribute('acq_expo_time', Texp)
        lima.write_attribute('latency_time', Tlat)

        lima.prepareAcq()



class lima_acquire(Macro):
    """
    Aquire a set of frames
    """

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        lima.startAcq()



class lima_stop(Macro):
    """Aborts acquisition."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        lima.stopAcq()



class lima_reset(Macro):
    """Resets lima device server."""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        lima.reset()



class lima_common_header(Macro):
    """Defines a list of common headers
Example:
    lima_common_header my_device "beam_x=1024|beam_y=1024" 
"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['header', Type.String, None, 
                   'Header definition syntax: key1=value1|key2=value2|key3=value3 ...']]

    @catch_error
    def run(self,dev,header):
        lima = taurus.Device(dev)
        lima.write_attribute('saving_common_header', header.split("|"))
        


class lima_image_header(Macro):
    """Defines a list of image headers
Example:
    lima_image_header my_device "0;beam_x=1024|beam_y=1024" "1;beam_x=1024|beam_y=1024" ...
"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['header_list',
                   ParamRepeat(['header', Type.String, None, 
                   'Header definition syntax: IMAGE_ID;key1=value1|key2=value2|key3=value3 ...']),
                   None, 'List of header definitions']
                  ]

#    @catch_error
    def run(self,*args):
        dev = args[0]
        headers = args[1]
        lima = taurus.Device(dev)
        lima.write_attribute('saving_header_delimiter', ['=','|',';'])
        lima.setImageHeader(headers)
        


class lima_write_image(Macro):
    """Writes on disk the image with the given ID"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['ImageID',Type.Integer, None, 'ID of image to be written']]

    @catch_error
    def run(self,dev,imageid):
        lima = taurus.Device(dev)
        lima.writeImage(imageid)
 


class lima_getconfig(Macro):
    """Returns the desired parameter value
Parameter list:
    FileDir       FileFormat    ExposureTime    TriggerMode
    FilePrefix    NbFrames      LatencyTime     NextNumber     SavingMode"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['paramIn',Type.String, None, 'Parameter name.']]
    result_def = [['paramOut',Type.String, None, 'Parameter value']]
        
    param_list = {'FileDir': 'saving_directory',
                 'FilePrefix': 'saving_prefix',
                 'FileFormat': 'saving_format',
                 'NbFrames': 'acq_nb_frames',
                 'ExposureTime': 'acq_expo_time',
                 'LatencyTime': 'latency_time',
                 'TriggerMode':'acq_trigger_mode',
                 'NextNumber':'saving_next_number',
                 'SavingMode':'saving_mode'}

    @catch_error
    def run(self,dev,param):
        lima = taurus.Device(dev)
        value = lima.read_attribute(self.param_list[param]).value
        return str(value)



class lima_printconfig(Macro):
    """Prints configuration"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]

    @catch_error
    def run(self,dev):

        for par in lima_getconfig.param_list:            
            result = self.execMacro(['lima_getconfig', dev, par])
            self.info("%s = %s" % (par, result.getResult()))



class lima_lastbuffer(Macro):
    """Returns the frame Id of last buffer ready"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['lastBuffer',Type.Integer, None, 
                   'Frame Id of last buffer ready']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute("last_image_ready").value
        return value
     


class lima_lastimage(Macro):
    """Returns the image Id of last image saved"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['lastImage',Type.Integer, None, 'Id of last image saved']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute("saving_next_number").value - 1 
        return value 
     

class lima_nextimagefile(Macro):
    """Returns file name for next image to be saved"""
    
    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['lastImage',Type.String, None, 
                   'Filename for next image to be saved']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute("saving_next_number").value
        dir = lima.read_attribute("saving_directory").value
        prefix = lima.read_attribute("saving_prefix").value
        id = str("%04d" % value)
        suffix = lima.read_attribute("saving_suffix").value
        filename = dir + prefix + id + suffix
        return filename
     


class lima_nextimage(Macro):
    """Set next image number to be saved"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['image_nb',Type.Integer, None, 
                   'next image number to be saved']]

    @catch_error
    def run(self, dev, imgn):
        lima = taurus.Device(dev)
        lima.write_attribute('saving_next_number', imgn)



class lima_set_flip(Macro):
    """Flips image Left-Right and/or Up-Down"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['flipLR',Type.Boolean, None, 'Boolean to flip Left-Right'],
                  ['flipUP',Type.Boolean, None, 'Boolean to flip Up-Down']]

    @catch_error
    def run(self, dev, flipLR, flipUP):
        lima = taurus.Device(dev)
        lima.write_attribute('image_flip', [flipLR, flipUP])
       


class lima_get_flip(Macro):
    """Get image flip configuration"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['flip state',Type.String, None, 
                   'Flip state Left-Right Up-Down']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute('image_flip').value

        return "%s %s" % (str(value[0]),str(value[1]))



class lima_set_bin(Macro):
    """Set image binning"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['binx',Type.Integer, None, 
                   'Number of pixels to be binned in x axis'],
                  ['biny',Type.Integer, None, 
                   'Number of pixels to be binned in y axis']]

    @catch_error
    def run(self, dev, binx, biny):
        lima = taurus.Device(dev)
        lima.write_attribute('image_bin', [binx, biny])
       


class lima_get_bin(Macro):
    """Get get image binning"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['binning',Type.String, None, 
                   'Number of pixels binned in x and y axis']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute('image_bin').value

        return "%s %s" % (str(value[0]),str(value[1]))



class lima_set_first_image(Macro):
    """Set image number of first image"""

    param_def =  [['dev',Type.String, None, 'Device name or alias'],
                  ['first_image',Type.Integer, None, 
                   'Image number for first image']]

    @catch_error
    def run(self, dev, first):
        lima = taurus.Device(dev)
        lima.write_attribute('saving_next_number', first)
       


class lima_get_first_image(Macro):
    """Get get image number of first image"""

    param_def =  [['dev',Type.String, None, 'Device name or alias']]
    result_def = [['first_image',Type.Integer, None, 
                   'Image number for first image']]

    @catch_error
    def run(self,dev):
        lima = taurus.Device(dev)
        value = lima.read_attribute('saving_next_number').value

        return value



class lima_take(Macro):
    """Simple macro to take N images."""

    param_def = [['dev',Type.String, None, 'Device name or alias'],
                 ['BaseDir', Type.String, '/tmp', 
                  'Base directory to store data.'],
                 ['Texp', Type.Float, 1.0, 'Exposure time.'],
                 ['Tlat', Type.Float, 0.0, 'Latency time.'],
                 ['NF', Type.Integer, 1, 'Number of frames.'],
                 ['Prefix', Type.String, 'Test', 'Prefix for the experiment.'],
                 ['Format', Type.String, 'EDF', 'File format'],
                 ['Autosave' , Type.Boolean, True, 
                  'Flag to save all frames automatically'],
                 ['Trig', Type.String, 'INTERNAL_TRIGGER', 'Trigger mode.'],
                 ]

    def prepare(self, dev, bdir, texp, tlat, nf, pref, form, auto, trig):
        self.device = dev

    def on_abort(self):
        lima = taurus.Device(self.device)
        lima.stopAcq()

    @catch_error
    def run(self, dev, bdir, texp, tlat, nf, pref, form, auto, trig):
        self.execMacro(['lima_saving', dev, bdir, pref, form, auto]) 
        self.execMacro(['lima_prepare', dev, texp, tlat, nf, trig]) 
        self.execMacro(['lima_acquire', dev]) 
        self.info("Started")
        
        status = self.execMacro('lima_status',dev)
        state, acq = status.getResult().split()
        self.info(acq)

        while True:
            status = self.execMacro('lima_status',dev)
            state, acq = status.getResult().split()
            time.sleep(0.5)
            if acq != 'Running' :
                break
            
        self.info(acq)


class lima_macros_test(Macro):

    param_def =  [['dev', Type.String, None, 'Device name or alias']]

    def run(self, dev):
        status = self.execMacro("lima_status", dev).getResult()
        self.info("%s Status %s" % (dev, status))
        
        self.execMacro("lima_printconfig", dev)
        
        last_buffer = self.execMacro("lima_lastbuffer", dev).getResult()
        self.info("Last buffer %i" % last_buffer)
        
        last_image = self.execMacro("lima_lastimage", dev).getResult()
        self.info("Last image %i" % last_image)
        
        self.execMacro("lima_nextimage", dev, last_image + 2)
        
        next_imagefile = self.execMacro("lima_nextimagefile", dev).getResult()
        self.info("Next image file %s" % next_imagefile)
        
        flip = self.execMacro("lima_get_flip", dev).getResult()
        flip = [bool(x) for x in flip.split()]
        self.info("Current flip %s" % str(flip))
        self.execMacro("lima_set_flip", dev, not flip[0], not flip[1])
        flip = self.execMacro("lima_get_flip", dev).getResult()
        flip = [bool(x) for x in flip.split()]
        self.info("New flip %s" % str(flip))
        self.execMacro("lima_set_flip", dev, not flip[0], not flip[1])
        flip = self.execMacro("lima_get_flip", dev).getResult()
        flip = [bool(x) for x in flip.split()]
        self.info("Original flip %s" % str(flip))
        
        binning = self.execMacro("lima_get_bin", dev).getResult()
        binning = [int(x) for x in binning.split()]
        self.info("Current binning %i %i" % (binning[0], binning[1]))
        self.execMacro("lima_set_bin", dev, 1, 1)
        new_binning = self.execMacro("lima_get_bin", dev).getResult()
        self.info("New binning %s" % new_binning)
        self.execMacro("lima_set_bin", dev, binning[0], binning[1])
        binning = self.execMacro("lima_get_bin", dev).getResult()
        self.info("Original binning %s" % str(binning))
        
        self.execMacro("lima_set_first_image", dev, 10)
        first = self.execMacro("lima_get_first_image", dev).getResult()
        self.info("First Image %i" % first)
        
        self.execMacro("lima_reset", dev)
        
        self.execMacro("lima_common_header", dev,
                       "CommonHeader=True|Header=True")
        self.execMacro("lima_take", dev)

        self.execMacro("lima_saving", dev, "/tmp", "LimaTest", "EDF", False)
        self.execMacro("lima_prepare", dev)
        self.execMacro("lima_acquire", dev)
        
        while True:
            status = self.execMacro('lima_status',dev)
            state, acq = status.getResult().split()
            time.sleep(0.5)
            if acq != 'Running' :
                break

        self.execMacro("lima_image_header", dev,
                       ["0;ImageHeader=True|Image=0"])
        self.execMacro("lima_write_image", dev, 0)
        self.execMacro("lima_stop", dev)
