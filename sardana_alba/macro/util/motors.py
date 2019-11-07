import PyTango

def moveToHardLim(macro, info_list):
    """From following information: motor, position to approach the limit, and limit (all in pool sense)
       it tries to reach specified limit and return list of motors which completed this task.
    :param macro: macro object which calls this method
    :param info_list: (list) of tuples where tupple has to contains 3 elements: (mot, pos, lim) 
                      mot - pool motor object
                      pos - motor position to approach the limit (in pool sense)
                      lim - positive or negative number (positive - positive limit, negative - negative limit)
   
    :return: (list) list of motor names which reached hardware limit"""
    try:
        motors    = [x[0] for x in info_list]
        positions = [x[1] for x in info_list]
        limits    = [x[2] for x in info_list]
        #Checking limits state (maybe they were already active)
        motorsOnLim = []
        for mot,lim in zip(motors,limits):
            #@TODO:remove this line when Pool bug will be fixed. (Missing state event)
            mot.getStateExObj().readValue(force=True)
            mot_alias = mot.alias()
            if lim > 0:
                if mot.Limit_switches[1]:
                    macro.debug('Motor %s is already at the positive limit.', mot_alias)
                    motorsOnLim.append(mot_alias)
            elif lim < 0:
                if mot.Limit_switches[2]:
                    macro.debug('Motor %s is already at the negative limit.', mot_alias)
                    motorsOnLim.append(mot_alias)
        if len(motorsOnLim): 
            return motorsOnLim

        for mot,pos in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', mot.alias(), pos)
        motion = macro.getMotion(motors)
        motion.move(positions)
        macro.checkPoint()
        #Checking stop code (if we reached positive limits)
        motorsWhichReachedLim = []
        for mot,lim in zip(motors,limits):
            mot_alias = mot.alias()
            macro.debug("Alias %s",mot_alias)
            if mot.Sign > 0:
                if lim > 0 and mot.StatusStopCode == 'Limit+ reached':
                    macro.debug('Motor %s reached its positive limit.', mot_alias)
                    motorsWhichReachedLim.append(mot_alias)
                if lim < 0 and mot.StatusStopCode == 'Limit- reached':
                    macro.debug('Motor %s reached its negative limit.', mot_alias)
                    motorsWhichReachedLim.append(mot_alias)
            #here we are swapping status stop codes to consider pool sense
            if mot.Sign < 0:
                if lim > 0 and mot.StatusStopCode == 'Limit- reached':
                    macro.debug('Motor %s reached its positive limit.', mot_alias)
                    motorsWhichReachedLim.append(mot_alias)
                if lim < 0 and mot.StatusStopCode == 'Limit+ reached':
                    macro.debug('Motor %s reached its negative limit.', mot_alias)
                    motorsWhichReachedLim.append(mot_alias)
        return motorsWhichReachedLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s was interupted.', repr(motors))
        raise e

def moveToPosHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        #Checking positive limits state (maybe they were already active)
        motorsOnPosLim = []
        for m in motors:
            #@TODO:remove this line when Pool bug will be fixed. (Missing state event)
            m.getStateExObj().readValue(force=True)
            if m.Limit_switches[1]:
                macro.debug('Motor %s is already at the positive limit.', m.alias())
                motorsOnPosLim.append(m)
        if len(motorsOnPosLim): return motorsOnPosLim
        macro.debug('Moving motors: %s towards positive limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        motion = macro.getMotion(motors)
        motion.move(positions)
        macro.checkPoint()
        #Checking stop code (if we reached positive limits)
        motorsWhichReachedPosLim = []
        for m in motors:
            if m.StatusStopCode == 'Limit+ reached':
                macro.debug('Motor %s reached its positive limit.', m.alias())
                motorsWhichReachedPosLim.append(m)
        return motorsWhichReachedPosLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s to positive limits was interupted.', repr(motors))
        raise e
        
def moveToNegHardLim(macro, motors_pos_dict):
    try:
        motors = motors_pos_dict.keys()
        positions = motors_pos_dict.values()
        #Checking negative limits state (maybe they were already active)
        motorsOnNegLim = []
        for m in motors:
            #@TODO:remove this line when Pool bug will be fixed. (Missing state event)
            m.getStateExObj().readValue(force=True)
            #macro.output(type(m.getAttribute('StatusLim-')))
            if m.Limit_Switches[2]:
                macro.debug('Motor %s is already at the negative limit.', m.alias())
                motorsOnNegLim.append(m)
        if len(motorsOnNegLim): return motorsOnNegLim
        macro.debug('Moving motors: %s towards negative limit...', 
                   repr([m.alias() for m in motors_pos_dict.keys()]))
        for m,p in zip(motors,positions):
            macro.debug('Moving motor %s to position: %f).', m.alias(), p)
        macro.debug('Before getting motion object motion object.')
        motion = macro.getMotion(motors)
        macro.debug('After getting motion object motion object.')
        macro.debug("Motion: %s, Positions: %s", motion, positions)
        motion.move(positions)
        macro.debug('After move command to motion object.')
        macro.checkPoint()
        #Checking stop code (if we reached negative limits)
        motorsWhichReachedNegLim = []
        for m in motors:
            if m.StatusStopCode == 'Limit- reached':
                macro.debug('Motor %s reached its negative limit.', m.alias())
                motorsWhichReachedNegLim.append(m)
        return motorsWhichReachedNegLim
    except PyTango.DevFailed, e: 
        macro.error(repr(e))
        macro.error('Moving motors: %s to negative limits was interupted.', repr(motors))
        raise e  

def moveToReadPos(macro, motors):
    """This function reads current user position of motors passed as an argument and move motors to these positions.
    :param macro: macro object which calls this method
    :param motors: (list) motors to be moved
    """
    positions = []
    for mot in motors:
        positions.append(mot.getPosition(force=True))
    macro.debug("Current read positions: %s", repr(zip(motors,positions)))
    motion = macro.getMotion(motors)
    motion.move(positions)