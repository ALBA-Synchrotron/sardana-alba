import math
from sardana.pool.controller import PseudoMotorController, Description, \
    DefaultValue, Type


class TwoXStageController(PseudoMotorController):
    """
    This is a pseudomotor controller for a stage with two lateral translation
    motors. It expects two physical motors: mx1, mx2 and provides 2
    pseudomotors: x, yaw. Motor mx1 is the upstream one, and yaw angle is
    increasing with increasing its position.

    It requires definition of 3 properties:
    Tx1Coordinates - a string representing Tx1 x,y coordinates
                     in local system e.g. "-711.9, 0"
    Tx2Coordinates - a string representing Tx2 x,y coordinates
                     in local system e.g. "689, 0"
    Dx - nominal x shift of the center in local system.
    """

    pseudo_motor_roles = ('x', 'yaw')
    motor_roles = ('mx1', 'mx2')

    class_prop = {
        'Tx1Coordinates':
            {Type: str,
             Description: 'tx1 coordination: x,y in local system'},
        'Tx2Coordinates':
            {Type: str,
             Description: 'tx2 coordination: x,y in local system'},
        'Dx':
            {Type: str,
             Description: 'nominal x shift of the center in local system',
             DefaultValue: 0}
    }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        try:
            self.tx1 = [float(c) for c in props['Tx1Coordinates'].split(',')]
            self.tx2 = [float(c) for c in props['Tx2Coordinates'].split(',')]
            self.dx = float(props['Dx'])

            if len(self.tx1) != 2 or len(self.tx2) != 2:
                raise ValueError("Tx1 and Tx2 Coordinates properties must "
                                 "be x,y coordinates in local system")

            if self.tx1[1] == self.tx2[1]:
                raise ValueError('The mirror must be initially horizontal!')

        except ValueError as e:
            self._log.error('Could not parse class properties to '
                            'generate coordinates.')
            raise e

    def calc_physical(self, index, pseudos):
        return self.calc_all_physical(pseudos)[index - 1]

    def calc_pseudo(self, index, physicals):
        return self.calc_all_pseudo(physicals)[index - 1]

    def calc_all_physical(self, pseudos):
        x, yaw = pseudos
        tanYaw = math.tan(yaw/1000)  # converts back to radians
        tx1 = -tanYaw * self.tx1[1] + x
        tx2 = -tanYaw * self.tx2[1] + x
        return tx1, tx2

    def calc_all_pseudo(self, physicals):
        tx1, tx2 = physicals
        x = tx1 - (tx2 - tx1) * self.tx1[1] / (self.tx2[1] - self.tx1[1])
        yaw = -math.atan((tx2 - tx1) / (self.tx2[1] - self.tx1[1]))
        yaw *= 1000  # conversion to mrad
        return x, yaw
