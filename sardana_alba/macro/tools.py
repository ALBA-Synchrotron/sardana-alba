import time
from sardana.macroserver.macro import Macro, Type
import PyTango


class dwell(Macro):
    """
    This macro waits for a time amount specified by dtime parameter.
    (python: time.sleep(dtime))
    """

    param_def = [
       ['dtime', Type.Float, None, 'Dwell time in seconds']
    ]

    def run(self, dtime):
        while dtime > 0:
            self.checkPoint()

            if dtime > 1:
                time.sleep(1)
                dtime = dtime - 1
            else:
                time.sleep(dtime)
                dtime = 0


class set_user_pos_pm(Macro):
    """
    This macro set the position of a pseudomotor by changing the offset of its
    motors.
    """

    param_def = [['pm', Type.PseudoMotor, None, 'Pseudo motor name'],
                 ['pos', Type.Float, None, 'Position which will set']]

    def set_pos(self, moveable, pos):
        moveable_type = moveable.getType()
        if moveable_type == "PseudoMotor":
            moveables_names = moveable.elements
            values = moveable.calcphysical(pos)
            sub_moveables = [(self.getMoveable(name), value)
                             for name, value in zip(moveables_names, values)]
            for sub_moveable, value in sub_moveables:
                self.set_pos(sub_moveable, value)
        elif moveable_type == "Motor":
            m = moveable.getName()
            self.execMacro('set_user_pos %s %f' % (m, pos))

    def run(self, pm, pos):
        self.set_pos(pm, pos)


###############################################################################
#                   Photon Shutter Macros
###############################################################################

class PSHU(object):
    OPEN_VALUE = 1
    CLOSE_VALUE = 0

    def __init__(self):
        self.initPSHU()

    def initPSHU(self):
        try:
            sh_attr_name = self.getEnv('PshuAttr')
            self.sh_timeout = self.getEnv('PshuTimeout')
            self.attr = PyTango.AttributeProxy(sh_attr_name)

        except Exception as e:
            msg = 'The macro use the environment variable PshuAttr which ' \
                  'has the attribute name of the EPS to open the shutter, ' \
                  'and the variable PshuTimeout with the timeout in seconds ' \
                  '\n{}'.format(e)
            raise RuntimeError(msg)

    @property
    def state(self):
        return self.attr.read().value

    def _writeValue(self, value):
        self.attr.write(value)
        t1 = time.time()
        msg_to = 'Timeout Error: Could not open the photon shutter'
        if value == self.CLOSE_VALUE:
            msg_to = 'Timeout Error: Could not close the photon shutter'
        while self.state != value:
            t = time.time() - t1
            if t > self.sh_timeout:
                raise RuntimeError(msg_to)
            time.sleep(0.1)
            self.checkPoint()

    def open(self):
        if self.state:
            self.info('The photon shutter was open')
            return
        self.info('Opening photon shutter...')
        self._writeValue(self.OPEN_VALUE)
        self.info('The photon shutter is open')

    def close(self):
        if not self.state:
            self.info('The photon shutter was closed')
            return
        self.info('Closing photon shutter...')
        self._writeValue(self.CLOSE_VALUE)
        self.info('The photon shutter is closed')


pshutter = PSHU()


class shopen(Macro):
    """
    This macro open the photon shutter.

    Other macros: shclose, shstate
    """
    def run(self):
        pshutter.open()


class shclose(Macro):
    """
    This macro close the photon shutter.

    Other macros: shopen, shstate
    """
    def run(self):
        pshutter.close()


class shstate(Macro):
    """
    This macro show the photon shutter state.

    Other macros: shopen, shclose
    """
    def run(self):
        state = pshutter.state
        st_msg = 'closed'
        if state == pshutter.OPEN_VALUE:
            st_msg = 'open'

        self.info('The photon shutter is ' + st_msg)


###############################################################################
#                   Front End Macros
###############################################################################

class FrontEnd(object):
    """
    Class to control the front end
    """

    FE_OPEN_ATTR = 'fe_open'
    FE_OPEN_ATTR_W = 'open_fe'
    FE_CLOSE_ATTR = 'close_fe'
    FE_AUTO_ATTR = 'fe_auto'
    FE_CTRL_ATTR = 'fe_control_disabled'
    FE_PSS_ATTR = ''
    BL_READY = 'bl_ready'
    CLOSE = 1
    OPEN = 2

    def __init__(self):
        self.init_fe()

    def init_fe(self):
        try:
            eps_name = self.getEnv('EPSName')
            self.fe_timeout = self.getEnv('FeTimeout')
            self.eps = PyTango.DeviceProxy(eps_name)

        except Exception as e:
            msg = 'The macro use the environment variable EPSName which has ' \
                  'the EPS device server name and FeTimeout with the ' \
                  'timeout to open/close the front end.' \
                  '\n{}'.format(e)
            raise RuntimeError(msg)

    def is_bl_ready(self):
        return bool(self.eps.read_attribute(self.BL_READY).value)

    def is_fe_open(self):
        return bool(self.eps.read_attribute(self.FE_OPEN_ATTR).value)

    def is_fe_close(self):
        return not self.is_fe_open()

    def is_fe_ctr_disabled(self):
        return bool(self.eps.read_attribute(self.FE_CTRL_ATTR).value)

    # def is_fe_pss_permits(self):
    #     return bool(self.eps.read_attribute(self.))

    def is_fe_auto(self):
        return bool(self.eps.read_attribute(self.FE_AUTO_ATTR).value)

    def _write_value(self, value):
        if value == self.CLOSE:
            attr = self.FE_CLOSE_ATTR
            is_ready = self.is_fe_close
        else:
            attr = self.FE_OPEN_ATTR_W
            is_ready = self.is_fe_open

        self.eps.write_attribute(attr, True)
        t1 = time.time()
        msg_to = 'Timeout Error: Could not open the Front End.\n'
        if value == self.CLOSE:
            msg_to = 'Timeout Error: Could not close the Front End.\n'
        while not is_ready():
            t = time.time() - t1
            if t > self.fe_timeout:
                msg_to += 'Run macro festatus to see the status'
                raise RuntimeError(msg_to)
            time.sleep(0.1)
            self.checkPoint()

    def fe_close(self):
        if self.is_fe_close():
            self.info('The Front End was closed')
            return
        self.info('Closing Front End...')
        self._write_value(self.CLOSE)
        self.info('FE is closed.')

    def fe_open(self):
        if self.is_fe_open():
            self.info('The Front End was open')
            return
        self.info('Opening Front End...')
        self._write_value(self.OPEN)
        self.info('FE is open.')

    def fe_auto(self, value=None):
        if value is not None:
            self.eps.write_attribute(self.FE_AUTO_ATTR, int(value))
            time.sleep(0.1)
        auto_state = bool(self.eps.read_attribute(self.FE_AUTO_ATTR).value)

        st_msg = 'disable'
        if auto_state:
            st_msg = 'enable'
        self.info('Automatic mode of the Front End is: %s' % st_msg)

    def fe_status(self):
        flg_warn = False

        # FE state
        msg = 'open'
        stream = self.info
        if not self.is_fe_open():
            msg = 'close'
            stream = self.warning
            flg_warn = True
        stream('The Front End is: %s.' % msg)

        # BL state
        msg = 'is'
        stream = self.info
        if not self.is_bl_ready():
            msg = 'is not'
            stream = self.warning
            flg_warn = True
        stream('The beamline %s ready.' % msg)

        # FE control room permits
        msg = 'has'
        stream = self.info
        if self.is_fe_ctr_disabled():
            msg = 'has not'
            stream = self.warning
            flg_warn = True
        stream('The beamline %s permits from the controls room.', msg)

        if flg_warn:
            msg = ('You should check if you have permits from the controls '
                   'room. You should check if the optical hatch is closed. '
                   'You should check if there are interlocks.')
            self.error(msg)

    def fe_wait(self):
        if not self.is_fe_auto():
            msg = ('The front end will not open automaticale. You should '
                   'active the automatic mode with the macro feauto.')
            raise RuntimeError(msg)

        self.info('Waiting for opening the Front End')
        while self.is_fe_close():
            time.sleep(0.1)
            self.checkPoint()


fe = FrontEnd()


class feclose(Macro):
    """
    Macro to close the Front End.

    Other macros: feopen, festatus, feauto, fewait
    """

    param_def = []

    def run(self, *args):
        fe.fe_close()


class feopen(Macro):
    """
    Macro to open the Front End.

    Other macros: feclose, festatus, feauto, fewait
    """

    param_def = []

    def run(self, *args):
        fe.fe_open()


class festatus(Macro):
    """
    Macro to see the Front End status.

    Other macros: feclose, feopen, feauto, fewait
    """

    param_def = []

    def run(self, *args):
        fe.fe_status()


class feauto(Macro):
    """
    Macro to set the automatic opening of the Front End.

    If you do not introduce the parameter it will show the current state of
    the automatic mode.

    Other macros: feclose, feopen, festatus, fewait
    """

    param_def = [['Active', Type.String, '', '1/0 or Yes/No']]

    def run(self, active):
        TRUE_VALUES = ['1', 'yes', 'true']
        FALSE_VALUES = ['0', 'no', 'false']

        if active not in TRUE_VALUES + FALSE_VALUES+['']:
            msg = 'Wrong value. See the help for more information.'
            raise ValueError(msg)

        if active in TRUE_VALUES:
            fe.fe_auto(True)
        elif active in FALSE_VALUES:
            fe.fe_auto(False)
        else:
            fe.fe_auto()


class fewait(Macro):
    """
    Macro to wait during the Front End is closed. It raise an exception if
    the automatic mode is off.

    Other macros: feclose, feopen, festatus, feauto
    """

    param_def = []

    def run(self, *args):
        fe.fe_wait()
