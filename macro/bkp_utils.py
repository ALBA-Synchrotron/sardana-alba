from sardana.macroserver.macro import macro, Type, Macro
import ConfigParser
import time
import fandango
import PyTango
import sardana
import json

class bkp_sardana(Macro):
    """
    Macro to save the configuration of all controller, their elements,
    environments and MeasurementGroups.
    """
    param_def = [["filename", Type.String, None, "Filename path"]]

    def run(self, filename):
        data = {}
        error_flg = False
        error_msg = ''

        # Add backup sardana version.
        version = sardana.release.version
        self.info('Creating Sardana %r Backup' % version)
        data['Version'] = version

        # Add backup time
        t = time.strftime("%b %d %Y %H:%M:%S", time.gmtime(time.time()))
        data['Date'] = t

        # Add Pool names
        pools = self.getPools()
        type_k = 'Pools'
        data[type_k] ={}

        self.info('\tSaving Pools')
        self.info('\t\tSaving Pools Properties')

        # Pools
        for pool in pools:

            #Read Pool Properties
            data[type_k][str(pool)] = {}
            properties = pool.get_property(pool.get_property_list('*'))
            data[type_k][str(pool)]['Properties'] = {}
            for k, v in properties.items():
                data[type_k][str(pool)]['Properties'][k] = str(v)

        #MacroServer and Doors

        self.info('\tSaving MacroServers')
        self.info('\t\tSaving MacroServer Properties')
        macroservers = fandango.tango.get_class_devices('MacroServer')
        type_k = 'MacroServers'
        data[type_k] ={}
        for ms in macroservers:
            data[type_k][str(ms)] = {}
            data[type_k][str(ms)]['Properties'] = {}
            ms_dev = PyTango.DeviceProxy(ms)

            try:
                #Read Pool Properties
                properties = ms_dev.get_property(ms_dev.get_property_list('*'))
                for k, v in properties.items():
                    data[type_k][str(ms)]['Properties'][k] = str(v)
            except Exception as e:
                data[type_k][str(ms)]['Properties'] = "ERROR on read"
                #self.error(e)

        # Read Environments
        environments = self.getManager()._environment_manager._getAllEnv()
        type_k = 'Environment'
        data[type_k] = {}
        self.info('\tSaving Environments')

        for env_name, val in environments.items():
            data[type_k][env_name] = {}
            data[type_k][env_name]['Value'] = val
            data[type_k][env_name]['Type'] = repr(type(val))

        #Controllers
        type_k = 'Controllers'
        data[type_k] = {}
        ctrls = self.getControllers()

        self.info('\tSaving Controllers')
        self.info('\t\tSaving Controllers Properties')

        self.info('\t\tSaving Controllers Elements')
        self.info('\t\t\tSaving Elements Properties')
        self.info('\t\t\tSaving Elements Attributes')

        # List of valid object types retrieved as controller elements.
        etypes = ["Pool", "Controller", "Motor", "CTExpChannel", 
                  "ZeroDExpChannel", "OneDExpChannel", "TwoDExpChannel", 
                  "ComChannel", "IORegister", "TriggerGate", "PseudoMotor", 
                  "PseudoCounter", "MeasurementGroup", "Instrument"]

        for ctrl in ctrls.values():
            ctrl = ctrl.getObj()

            ctrl_name = ctrl.getName()
            data[type_k][ctrl_name] = {}

            # Read the Controller properties
            properties = ctrl.get_property(ctrl.get_property_list('*'))
            data[type_k][ctrl_name]['Properties'] = {}

            for k, v in properties.items():
                data[type_k][ctrl_name]['Properties'][k] = v[0]

            data[type_k][ctrl_name]['Elements'] = {}
            elements = ctrl.elementlist

            if elements:
                for element in elements:

                    # elements (motors, counter/timers, etc...)
                    data[type_k][ctrl_name]['Elements'][str(element)] = {}
                    try:
                        elm = self.getObj(element, etypes)
                    except Exception as e:
                        self.error('Cannot get element %s\n%s' % (element, str(e)))
                    # Read element Properties
                    properties = elm.get_property(elm.get_property_list('*'))
                    data[type_k][ctrl_name]['Elements'][str(element)]['Properties'] = {}

                    for k, v in properties.items():
                        data[type_k][ctrl_name]['Elements'][str(element)][
                            'Properties'][k] = v[0]

                    # Read elements Attributes
                    attrs = elm.get_attribute_list()
                    data[type_k][ctrl_name]['Elements'][str(element)]['Attributes'] = {}
                    for attr in attrs:
                        try:
                            attr_value = repr(elm.read_attribute(attr).value)
                        except Exception as e:
                            attr_value = 'Error on the read %s ' % attr
                            error_flg = True
                            error_msg += "Error in read %r from %r" % (
                                attr,elm)
                        data[type_k][ctrl_name]['Elements'][str(element)]['Attributes'][attr] = \
                            attr_value

        # MeasurementGroups
        self.info('\tSaving MeasurementGroups')
        self.info('\t\tSaving MeasurementGroups Properties')
        self.info('\t\tSaving MeasurementGroups Attributes')
        filter = ".*"
        measurementGroups = self.findObjs(filter,
                                          type_class=Type.MeasurementGroup,
                                          subtype=Macro.All, reserve=False)
        type_k = 'MeasurementGroups'
        data[type_k] = {}

        for meas in measurementGroups:

            # Measurement Group attributes
            data[type_k][meas.name] = {}
            attrs = meas.get_attribute_list()
            data[type_k][meas.name]['Attributes'] = {}
            for attr in attrs:
                try:
                    val = meas.read_attribute(attr).value
                except:
                    val = 'Error on the read %s' % attr
                data[type_k][meas.name]['Attributes'][attr] = val

            # Measurement Groups Properties
            data[type_k][meas.name]['Properties'] = {}
            properties = meas.get_property(meas.get_property_list('*'))
            for k, v in properties.items():
                data[type_k][meas.name]['Properties'][k] = v[0]

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        self.info('Saved backup in: %r' % filename)
        

class MntGrpConf(object):
    """
    Class Helper to read the configuration file.
    """

    def _tolist(self, data):
        data = data.replace('\n', ' ')
        data = data.replace(',', ' ')
        return data.split()

    def _create_bkp(self):
        self.info('Creating backup...')
        path, filename = self.config_path.rsplit('/', 1)
        t = '{0}/bkp_{1}_{2}'
        nfilename = t.format(path,time.strftime('%Y%m%d_%H%M%S'), filename)
        self._save_file(nfilename)
        self.info('Created backup file: %s' % nfilename)

    def _save_file(self, filename):
        """
        :param filename: New file name to save the current configuration.
        """
        with open(filename,'w') as f:
            self.config_file.write(f)

    def init_config(self, config_path):
        self.config_file = ConfigParser.RawConfigParser()
        self.config_file.read(config_path)
        self.config_path = config_path

    def get_config(self, mnt_grp):
        mnt_grp = mnt_grp.lower()
        self.info(mnt_grp)
        try:
            config_value = self.config_file.get(mnt_grp, 'configuration')

        except:
            raise RuntimeError('The configuration file is corrupted or you '
                               'did not save the configuration.')

        return config_value

    def save(self, mnt_grp, config):
        self._create_bkp()
        self.info('Saving configuration....')
        mnt_grp = mnt_grp.lower()
        if not self.config_file.has_section(mnt_grp):
            self.config_file.add_section(mnt_grp)
        self.config_file.set(mnt_grp, 'configuration', config)
        self._save_file(self.config_path)
        self.output('Saved configuration.')


class save_mntgrp(Macro, MntGrpConf):
    """
    Macro to create backups of the measurement group configurations

    """

    env = ('MntGrpConfFile',)
    param_def = [['mg', Type.MeasurementGroup, None, 'Measurement Group'],
                 ['UseDefault', Type.Boolean, False, 'Use default']]

    def run(self, mg, use_default):
        config_path = self.getEnv('MntGrpConfFile')
        if use_default:
           path = config_path.rsplit('/',1)[0]
           filename = '/mntgrp_default.cfg'
           config_path = path + filename
        self.init_config(config_path)
        config = mg.read_attribute('configuration').value
        self.save(mg.getName(), config)


class load_mntgrp(Macro, MntGrpConf):
    """
    Macro to create backups of the measurement group configurations

    """

    env = ('MntGrpConfFile',)
    param_def = [['mg', Type.MeasurementGroup, None, 'Measurement Group'],
                 ['UseDefault', Type.Boolean, True, 'Use default']]

    def run(self, mg, use_default):
        config_path = self.getEnv('MntGrpConfFile')
        if use_default:
           path = config_path.rsplit('/',1)[0]
           filename = '/mntgrp_default.cfg'
           config_path = path + filename
       
        self.init_config(config_path)

        mg_bkp_config = self.get_config(mg.getName())
        mg_config = mg.read_attribute('configuration').value
        diff_conf = mg_config != mg_bkp_config
        msg = 'The current configuration %s the same than the backup' % \
              ['is', 'is not'][diff_conf]
        if diff_conf:
            self.warning(msg)
            self.info('Loading backup...')
            mg.write_attribute('configuration', mg_bkp_config)
            self.output('Loaded backup')
        else:
            self.output(msg)
