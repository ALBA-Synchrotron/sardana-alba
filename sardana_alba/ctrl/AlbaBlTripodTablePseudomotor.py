import math
import PyTango
from sardana.pool.controller import PseudoMotorController, Description, Type


def rotate_x(y, z, cosangle, sinangle):
    """3D rotaion around *x* (pitch). *y* and *z* are values or arrays.
    Positive rotation is for positive *sinangle*. Returns *yNew, zNew*.

    :param y: (float or list<float>) value of the y coordinate
    :param z: (float or list<float>) value of the z coordinate
    :param cosangle: (float) cosinus of the rotation angle
    :param sinangle: (float) sinus of the rotation angle

    :return: (tuple<float>) new (rotated) y and z"""
    return cosangle * y - sinangle * z, sinangle * y + cosangle * z


def rotate_y(x, z, cosangle, sinangle):
    """3D rotaion around *y* (roll). *x* and *z* are values or arrays.
    Positive rotation is for positive *sinangle*. Returns *xNew, zNew*.

    :param x: (float or list<float>) value of the x coordinate
    :param z: (float or list<float>) value of the z coordinate
    :param cosangle: (float) cosinus of the rotation angle
    :param sinangle: (float) sinus of the rotation angle

    :return: (tuple<float>) new (rotated) x and z"""
    return cosangle * x + sinangle * z, -sinangle * x + cosangle * z


def rotate_z(x, y, cosangle, sinangle):
    """3D rotaion around *z*. *x* and *y* are values or arrays.
    Positive rotation is for positive *sinangle*. Returns *xNew, yNew*.

    :param x: (float or list<float>) value of the x coordinate
    :param y: (float or list<float>) value of the y coordinate
    :param cosangle: (float) cosinus of the rotation angle
    :param sinangle: (float) sinus of the rotation angle

    :return: (tuple<float>) new (rotated) x and y"""
    return cosangle * x - sinangle * y, sinangle * x + cosangle * y


class TripodTableController(PseudoMotorController):
    """
    This is a pseudomotor controller for a three-legs table.
    It expects three physical motors: jack1, jack2, jack3 and provides 3
    pseudomotors: z, pitch and roll.
    Jack1 is the most upstream one and Jack3 is the most downstream. If two
    of the jacks have the same distance to the source the left one comes first.

    It requires definition of 4 properties (all of them are strings with
    comma separated float values representing x,y,z coordinates in global
    coordinate system e.g. "3123.09, -3232.33, 1400"):
      Jack1Coordinates, Jack2Coordinates, Jack3Coordinates, CenterCoordinates
    """

    pseudo_motor_roles = ('z', 'pitch', 'roll')
    motor_roles = ('jack1', 'jack2', 'jack3')

    ctrl_properties = {
        'Jack1Coordinates': {Type: str,
                             Description: 'jack1 coordination: x,y,z'},
        'Jack2Coordinates': {Type: str,
                             Description: 'jack2 coordination: x,y,z'},
        'Jack3Coordinates': {Type: str,
                             Description: 'jack3 coordination: x,y,z'},
        'CenterCoordinates': {Type: str,
                              Description: 'center coordination: x,y,z'},
        'CrossedPMLimitsCheck': {Type: bool,
                                 Description: 'checks the crossed PM limits'}
    }

    # This is azimuth angle for BL22-CLAESS (Synchrotron ALBA) which is 45
    # degrees indeed for your beamline change it accordingly to your azimuth
    # angle
    cosAzimuth = 0.70710681665463704
    sinAzimuth = -0.70710674571845633

    def __init__(self, inst, props, *args, **kwargs):
        PseudoMotorController.__init__(self, inst, props, *args, **kwargs)

        try:
            jack1_coord = props['Jack1Coordinates'].split(',')
            self.jack1 = [float(c) for c in jack1_coord]
            jack2_coord = props['Jack2Coordinates'].split(',')
            self.jack2 = [float(c) for c in jack2_coord]
            jack3_coord = props['Jack3Coordinates'].split(',')
            self.jack3 = [float(c) for c in jack3_coord]
            center_coord = props['CenterCoordinates'].split(',')
            self.center = [float(c) for c in center_coord]
            self.check_limits = props['CrossedPMLimitsCheck']
            self._log.debug("check limits value: %s" % self.check_limits)

            if len(self.jack1) != 3 or \
                    len(self.jack2) != 3 or \
                    len(self.jack3) != 3:
                raise ValueError("Jack1, Jack2, Jack3 and Center Coordinates "
                                 "properties must be x,y,z coordinates in "
                                 "global system")

            if not (self. jack1[2] == self.jack2[2] == self.jack3[2]):
                raise ValueError('The mirror must be initially horizontal!')

        except ValueError as e:
            self._log.error('Could not parse class properties to '
                            'generate coordinates.')
            raise e

        # self.jackToMirrorInvariant = self.center[2] - self.jack1[2]

        # jacks in local virgin system, where point (0,0,0) is a center of
        # a optical surface
        self.jack1local = [ji - ci for ji, ci in zip(self.jack1, self.center)]
        self.jack2local = [ji - ci for ji, ci in zip(self.jack2, self.center)]
        self.jack3local = [ji - ci for ji, ci in zip(self.jack3, self.center)]

        # rotating the table on z axis over azimuth angle
        for jl in [self.jack1local, self.jack2local, self.jack3local]:
            jl[0], jl[1] = rotate_z(jl[0], jl[1], self.cosAzimuth,
                                    self.sinAzimuth)

        # self.zOffset = 1400 - self.jack1[2]

        self._log.debug("jack1local: %s" % repr(self.jack1local))
        self._log.debug("jack2local: %s" % repr(self.jack2local))
        self._log.debug("jack3local: %s" % repr(self.jack3local))

    def CalcPhysical(self, axis, pseudo_pos, curr_physical_pos):
        self._log.debug("Entering calc_physical")
        ret = self.CalcAllPhysical(pseudo_pos, curr_physical_pos)[axis - 1]
        self._log.debug("Leaving calc_physical")
        return ret

    def CalcPseudo(self, axis, physical_pos, curr_pseudo_pos):
        self._log.debug("Entering calc_pseudo")
        ret = self.CalcAllPseudo(physical_pos, curr_pseudo_pos)[axis - 1]
        self._log.debug("Leaving calc_pseudo")
        return ret

    def CalcAllPhysical(self, pseudo_pos, curr_physical_pos):
        self._log.debug("Entering calc_all_physical")

        if self.check_limits:
            self._validateCurrentPositions()

        z, pitch, roll = pseudo_pos
        # Ax + By + Cz = D in local system:
        pitch = pitch / 1000
        roll = roll / 1000

        A, B, C = 0.0, 0.0, 1.0

        if roll != 0:
            cosRoll = math.cos(roll)
            sinRoll = math.sin(roll)
            A, C = rotate_y(A, C, cosRoll, sinRoll)
        if pitch != 0:
            cosPitch = math.cos(pitch)
            sinPitch = math.sin(pitch)
            B, C = rotate_x(B, C, cosPitch, sinPitch)

        # D of optical plane = 0 because (0, 0, 0) belongs to it
        D = 0
        # D of balls plane:
        # D -= self.jackToMirrorInvariant * (A ** 2 + B ** 2 + C ** 2) ** 0.5
        # but because rotations are unitary (A ** 2 + B ** 2 + C ** 2) = 1 and:
        # D -= self.jackToMirrorInvariant
        # D -= (self.center[2] - z)

        self._log.debug("Plane equation in local system A: %f, B: %f, C: "
                        "%f, D: %f" % (A, B, C, D))

        jack1_local = (D - A * self.jack1local[0] - B * self.jack1local[1]) / C
        jack2_local = (D - A * self.jack2local[0] - B * self.jack2local[1]) / C
        jack3_local = (D - A * self.jack3local[0] - B * self.jack3local[1]) / C

        self._log.debug("jack1_local: %s" % repr(jack1_local))
        self._log.debug("jack2_local: %s" % repr(jack2_local))
        self._log.debug("jack3_local: %s" % repr(jack3_local))

        jack1 = jack1_local + z  # + self.zOffset
        jack2 = jack2_local + z  # + self.zOffset
        jack3 = jack3_local + z  # + self.zOffset
        self._log.debug("Leaving calc_all_physical")
        return jack1, jack2, jack3

    def CalcAllPseudo(self, physical_pos, curr_pseudo_pos):
        self._log.debug("Entering calc_all_pseudo")
        jack1, jack2, jack3 = physical_pos

        # Ax + By + Cz = D in global system:
        A = (self.jack2[1] - self.jack1[1]) * (jack3 - jack1) \
            - (self.jack3[1] - self.jack1[1]) * (jack2 - jack1)
        B = (self.jack3[0] - self.jack1[0]) * (jack2 - jack1) \
            - (self.jack2[0] - self.jack1[0]) * (jack3 - jack1)
        C = (self.jack2[0] - self.jack1[0]) * (self.jack3[1] - self.jack1[1]) \
            - (self.jack3[0] - self.jack1[0]) * (self.jack2[1] - self.jack1[1])

        self._log.debug(" A: %f, B: %f, C: %f" % (A, B, C))
        ABCNorm = (A ** 2 + B ** 2 + C ** 2) ** 0.5
        self._log.debug("ABCNorm: %f" % (ABCNorm))
        if C < 0:
            ABCNorm *= -1  # its normal looks upwards!
        A /= ABCNorm
        B /= ABCNorm
        C /= ABCNorm
        # D of balls plane
        D = A * self.jack1[0] + B * self.jack1[1] + C * jack1

        self._log.debug("Plane equation in global system A: %f, "
                        "B: %f, C: %f, D: %f" % (A, B, C, D))
        # C is never 0, i.e. the normal to the optical element is never
        # horizontal
        z = (D - A * self.center[0] - B * self.center[1]) / C

        self._log.debug("z: %f" % z)

        # A  and B in local system (C is unchanged):
        locA, locB = rotate_z(A, B, self.cosAzimuth, self.sinAzimuth)
        self._log.debug("A, B in local subsystem (rotated on z axiz) A: %f, "
                        "locB: %f" % (locA, locB))
        tanRoll = locA / C
        roll = math.atan(tanRoll)

        tanPitch = -locB / (locA * math.sin(roll) + C * math.cos(roll))
        pitch = math.atan(tanPitch) * 1000
        roll *= 1000
        self._log.debug("Leaving calc_all_pseudo")
        return z, pitch, roll

    def _validateCurrentPositions(self):
        self._checkPseudoMotorLimits()
        try:
            for role in self.pseudo_motor_roles:
                pseudo = self.GetPseudoMotor(role)
                attr_position = PyTango.AttributeProxy(pseudo.full_name +
                                                       '/position')
                attr_position.read()
        except Exception:
            raise ValueError('Move the physical motors to a save position.')

    def _checkPseudoMotorLimits(self):

        NE = 'Not specified'
        msg = ''
        flg_ne = False

        for role in self.pseudo_motor_roles:
            pseudo = self.GetPseudoMotor(role)
            attr_position = PyTango.AttributeProxy(pseudo.full_name +
                                                   '/position')
            config = attr_position.get_config()
            max_value = config.max_value
            if max_value == NE:
                flg_ne = True
                msg += 'Set limit %s\n' % pseudo.name
                continue

            min_value = config.min_value
            if min_value == NE:
                flg_ne = True
                msg += 'Set limit %s\n' % pseudo.name

        if flg_ne:
            self._log.debug("uninitialized limits")
            raise ValueError(msg)
