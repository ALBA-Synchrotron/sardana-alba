import math

from sardana.pool.controller import (
    PseudoMotorController, Type, Description, DefaultValue)


class TwoLeggedTable:
    """ This formulas units are: 'm' for distances and 'rad' for angles.
        This is a generic 'two legged table' class which is able to
        translate from two phyisical translation actuators to the pseudo
        common translation and rotation in a given pivoting point.
    """

    def get_trans(self, dist, pos, rot):
        """ Get motor translation"""
        return pos + (dist * math.tan(rot))

    def get_pos(self, dist_1, dist_2, trans_1, trans_2):
        """ Get table position"""
        return (dist_2 * trans_1 - dist_1 * trans_2) / (dist_2 - dist_1)

    def get_rot(self, dist_1, dist_2, trans_1, trans_2):
        """ Get table rotation """
        return math.atan2((trans_2 - trans_1), (dist_2 - dist_1))


class TwoLeggedTableController(PseudoMotorController, TwoLeggedTable):
    """ PseudoMotor controller for Two legged table's position and rotation.

    Assuming an XYZ right handed coordinate system:
    * dist_1 and dist_2 are the distances from the pivoting point in the table
    to the first and second jack in X direction. (They may be negative)
    * rot is the rotation angle around Y axis
    * trans_1, trans_2 and pos are the translations in Z for the first and
    second motor and the pivoting point position

    The calculation assumes no pivoting point displacement along X axis.

    Values are in 'mm' for distances and 'mrad' for angles.

    User units must be: mm for distances and mrad for angles.
    z1 is the upstream jack.
    """

    gender = "Table"
    model = "ALBA two legged table"
    organization = "CELLS - ALBA"

    pseudo_motor_roles = ('pos', 'rot')
    motor_roles = ('t1', 't2')

    ctrl_properties = {
        'dist1': {
            Type: 'PyTango.DevDouble',
            Description: 'First jack possition in mm',
            DefaultValue: -500.0  # mm
        },
        'dist2': {
            Type: 'PyTango.DevDouble',
            Description: ('Second jack possition in mm'),
            DefaultValue: 500.0  # mm
        },
    }

    def __init__(self, inst, props):
        PseudoMotorController.__init__(self, inst, props)

    def CalcPhysical(self, index, pseudos, curr_physicals):
        return self.CalcAllPhysical(pseudos, curr_physicals)[index - 1]

    def CalcPseudo(self, index, physicals, curr_pseudos):
        return self.CalcAllPseudo(physicals, curr_pseudos)[index - 1]

    def CalcAllPhysical(self, pseudos, curr_physicals):
        pos, rot = pseudos

        trans1 = self.get_trans(self.dist1, pos, rot / 1000.0)
        trans2 = self.get_trans(self.dist2, pos, rot / 1000.0)

        return (trans1, trans2)

    def CalcAllPseudo(self, physicals, curr_pseudos):
        trans1, trans2 = physicals

        pos = self.get_pos(self.dist1, self.dist2, trans1, trans2)
        rot = self.get_rot(self.dist1, self.dist2, trans1, trans2)

        return (pos, rot * 1000)


if __name__ == '__main__':

    tab_ctrl = TwoLeggedTableController('table2l_test', {'dist1': -500,
                                                         'dist2': 500})
    tab_rot_test = [-200, -100, 0, 100, 200]
    tab_pos_test = [-100, -50, 0, 50, 100]

#    print "D1: %6.3f, D2: %6.3f" %(tab_ctrl.dist1, tab_ctrl.dist2)
    for pos_test in tab_pos_test:
        for rot_test in tab_rot_test:
            t1, t2 = tab_ctrl.CalcAllPhysical([pos_test, rot_test], [])
            pos_cal, rot_cal = tab_ctrl.CalcAllPseudo([t1, t2], [])
            print("[%6.3f, %6.3f]\t[%6.3f, %6.3f]\t[%6.3f, %6.3f]"
                  % (pos_test, rot_test, t1, t2, pos_cal, rot_cal))
