from sardana.pool.controller import PseudoMotorController, Description, \
    Type, Memorize, Memorized, Access, DataAccess


class MoveableMask(PseudoMotorController):
    """ pseudomotor controller for Front end moveable masks"""

    pseudo_motor_roles = ['gap', 'offset']
    motor_roles = ['mask1', 'mask2']

    ctrl_attributes = {
        "aperture_origin":
            {Type: float,
             Description: 'origin in mm for the aperture real value',
             Memorize: Memorized,
             Access: DataAccess.ReadWrite,
             },
        "offset_origin":
            {Type: float,
             Description: 'origin in mm for the offset real value',
             Memorize: Memorized,
             Access: DataAccess.ReadWrite,
             },
    }

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        self.aperture_origin = 0.0  # mm (init value for Horizontal...)
        self.offset_origin = 0.0  # mm (init value for Horizontal...)

    def CalcPhysical(self, index, pseudo_pos, curr_physical_pos):

        a = self.CalcAllPhysical(pseudo_pos, curr_physical_pos)
        return a[index - 1]

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        try:

            pm_aperture = pseudo_pos[0]
            pm_offset = pseudo_pos[1]
            self._log.debug(
                "pm_aperture,pm_offset = %f,%f" % (pm_aperture, pm_offset))

            m_1 = (pm_aperture - self.aperture_origin + 2 * (
                        pm_offset - self.offset_origin)) / 2.0
            m_2 = (pm_aperture - self.aperture_origin - 2 * (
                        pm_offset - self.offset_origin)) / 2.0
            self._log.debug("m_1, m_2 = %f,%f" % (m_1, m_2))

            return [m_1, m_2]
        except Exception as e:
            self._log.error("Error in CalcAllPhysical")
            self._log.error(str(e))
            raise Exception("Error in CalcAllPhysical")

    def CalcPseudo(self, index, physical_pos, curr_pseudo_pos):

        a = self.CalcAllPseudo(physical_pos, curr_pseudo_pos)
        return a[index - 1]

    def CalcAllPseudo(self, physical_pos, curr_pseudo_pos):
        """
        From the real motor positions, we calculate the pseudomotors positions.
        """

        try:

            m_1 = physical_pos[0]
            m_2 = physical_pos[1]

            pm_aperture = (m_1 + m_2) + self.aperture_origin
            pm_offset = (m_1 - m_2) / 2.0 + self.offset_origin

            return [pm_aperture, pm_offset]
        except Exception as e:
            self._log.error("Error in CalcAllPseudo")
            self._log.error(str(e))
            raise Exception("Error in CalcAllPseudo")

    def GetCtrlPar(self, name):

        if name.lower() == "aperture_origin":
            return self.aperture_origin
        elif name.lower() == "offset_origin":
            return self.offset_origin

    def SetCtrlPar(self, name, value):
        if name.lower() == "aperture_origin":
            self.aperture_origin = value
        elif name.lower() == "offset_origin":
            self.offset_origin = value

