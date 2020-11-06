##############################################################################
#
# This file is part of Sardana
#
# http://www.tango-controls.org/static/sardana/latest/doc/html/index.html
#
# Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
# Author: Roberto Homs
#
# Sardana is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sardana is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Sardana.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""This module contains the definition of a two-coupled pseudomotor. """


__all__ = ["TwoCoupledPseudoMotor"]

__docformat__ = 'restructuredtext'

from sardana.pool.controller import PseudoMotorController, Description, Type


class TwoCoupledPseudoMotor(PseudoMotorController):
    """First version of the two coupled pseudo motor controller.This
    pseudo motor is mapped to two identical motors. Any action applied
    to the pseudo motor (move, set, etc...) is applied to both motors
    with the same values. The position of both motors must be the same
    whithin a certain tolerance. If the tolerance is exceeded, an
    exception is raised. Nevertheless, one can unset the validation
    of the tolerance by setting the tolerance to -1."""

    gender = "Coupled"
    model = "TwoCoupled"
    organization = "Sardana Team"

    # theta = bragg
    pseudo_motor_roles = ["Pseudo"]
    motor_roles = ["master", "slave"]

    # Introduce properties here.
    ctrl_properties = {
        'tolerance': {Type: float,
                      Description: 'Tolerance is the maximum difference '
                                   'between motor positions. If it is -1, '
                                   'we will not check it'},
    }

    # Introduce attributes here.
    axis_attributes = {}

    def __init__(self, inst, props, *args, **kwargs):

        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)
        self._log.debug("Created a two-coupled PseudoMotor")

    # Calculation of input motors values.
    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):
        pass

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        # Validation of position can be included:
        pos_master = curr_physical_pos[0]
        if self.tolerance != -1:
            self._log.debug("Tolerance different from -1")
            for index, c_pos in enumerate(curr_physical_pos[1:]):
                index += 1
                diff = abs(pos_master - c_pos)
                self._log.debug("Difference %f:" % diff)
                if diff > self.tolerance:
                    slave_name = self.GetMotor(self.motor_roles[index])
                    msg = ('Tolerance has been exceeded. You must change the '
                           '%s to %f' % (slave_name, pos_master))
                    raise Exception(msg)

        pos = pseudo_pos[0]
        return pos, pos

    # Calculation of output PseudoMotor values.
    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):
        pos = physical_pos[0]

        return pos
