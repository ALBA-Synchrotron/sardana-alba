import math
import PyTango
from sardana import pool
from sardana.pool import PoolUtil
from sardana.pool.controller import PseudoMotorController


class CommonDirectionSlit(PseudoMotorController):
    """A Slit pseudo motor controller for handling gap and offset pseudo
       motors. The system uses to real motors sl2t (top slit) and sl2b (bottom
       slit)."""

    gender = "Slit"
    model = "Common direction slit"
    organization = "CELLS - ALBA"
    image = "slit.png"
    logo = "ALBA_logo.png"

    pseudo_motor_roles = ("Gap", "Offset")
    motor_roles = ("sl2t", "sl2b")

    class_prop = {
        'sign': {
            'Type': 'PyTango.DevDouble',
            'Description': 'Gap = sign * calculated gap\n'
                           'Offset = sign * calculated offet',
            'DefaultValue': 1}}

    def calc_physical(self, index, pseudo_pos):
        half_gap = pseudo_pos[0] / 2.0
        if index == 1:
            ret = self.sign * (pseudo_pos[1] + half_gap)
        else:
            ret = self.sign * (pseudo_pos[1] - half_gap)
        return ret

    def calc_pseudo(self, index, physical_pos):
        gap = physical_pos[0] - physical_pos[1]
        if index == 1:
            ret = self.sign * gap
        else:
            ret = self.sign * (physical_pos[0] - gap / 2.0)
        return ret

    def calc_all_pseudo(self, physical_pos):
        """Calculates the positions of all pseudo motors that belong to the
           pseudo motor system from the positions of the physical motors."""
        gap = physical_pos[0] - physical_pos[1]
        return (self.sign * gap,
                self.sign * (physical_pos[0] - gap / 2.0))

    def calc_all_physical(self, pseudo_pos):
        """Calculates the positions of all motors that belong to the pseudo
           motor system from the positions of the pseudo motors."""
        half_gap = pseudo_pos[0] / 2.0
        return (self.sign * (pseudo_pos[1] + half_gap),
                self.sign * (pseudo_pos[1] - half_gap))
