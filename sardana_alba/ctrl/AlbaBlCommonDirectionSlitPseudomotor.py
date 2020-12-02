from sardana.pool.controller import PseudoMotorController, Description, \
    Type, DefaultValue


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

    ctrl_properties = {
        'sign': {Type: float,
                 Description: 'Gap = sign * calculated gap\n'
                              'Offset = sign * calculated offset',
                 DefaultValue: 1},
    }

    def CalcPhysical(self, index, pseudo_pos, curr_physicals):
        half_gap = pseudo_pos[0] / 2.0
        if index == 1:
            ret = self.sign * (pseudo_pos[1] + half_gap)
        else:
            ret = self.sign * (pseudo_pos[1] - half_gap)
        return ret

    def CalcPseudo(self, index, physical_pos, curr_pseudos):
        gap = physical_pos[0] - physical_pos[1]
        if index == 1:
            ret = self.sign * gap
        else:
            ret = self.sign * (physical_pos[0] - gap / 2.0)
        return ret

    def CalcAllPseudo(self, physical_pos, curr_pseudos):
        """Calculates the positions of all pseudo motors that belong to the
           pseudo motor system from the positions of the physical motors."""
        gap = physical_pos[0] - physical_pos[1]
        return (self.sign * gap,
                self.sign * (physical_pos[0] - gap / 2.0))

    def CalcAllPhysical(self, pseudo_pos, curr_physicals):
        """Calculates the positions of all motors that belong to the pseudo
           motor system from the positions of the pseudo motors."""
        half_gap = pseudo_pos[0] / 2.0
        return (self.sign * (pseudo_pos[1] + half_gap),
                self.sign * (pseudo_pos[1] - half_gap))
