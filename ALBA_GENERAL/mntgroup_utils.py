from sardana.macroserver.macro import Macro, Type, ParamRepeat


def filterMntChannels(mntGrp, channelsList):
    # Check if the channels exit in the mntGrp
    elements = mntGrp.getCounterNames()
    chs = []
    chs_to_skip = []
    for ch in channelsList:
        # check if exit in the mntGrp
        if ch.name in elements:
            # list of channels to config
            chs.append(ch.name)
        else:
            # list of channels skipped
            chs_to_skip.append(ch.name)
    return chs, chs_to_skip


class select_mntGrp(Macro):
    param_def = [
       ['mntGrp', Type.MeasurementGroup, None, 'mntGroup name']]

    def run(self, mntGrp):
        self.setEnv('ActiveMntGrp', str(mntGrp))
        self.info("Active Measurement Group : %s" % str(mntGrp))


class meas_enable_ch(Macro):
    """
    Enable the Counter Timers selected

    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState',
         ParamRepeat(['channel', Type.CTExpChannel, None, 'Channel to change '
                                                          'state'], min=1),
         None, 'List of channels to Enable'],
    ]

    def run(self, mntGrp, channels):
        ch, ch_to_skip = filterMntChannels(mntGrp=mntGrp,
                                           channelsList=channels)
        mntGrp.enableChannels(ch)
        self.info("Enabled %r channels in %r" % (ch, str(mntGrp)))
        if len(ch_to_skip) > 0:
            msg = "Skipped %r, not founds in %r" % (ch_to_skip, str(mntGrp))
            self.warning(msg)


class meas_disable_ch(Macro):
    """
    Disable the Counter Timers selected
    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None,
         "Measurement Group to work"],
        ['ChannelState', ParamRepeat(['channel', Type.CTExpChannel, None,
                                      'Channel to change state'], min=1),
         None, 'List of channels to Disable'],
    ]

    def run(self, mntGrp, channels):

        ch, ch_to_skip = filterMntChannels(mntGrp=mntGrp,
                                           channelsList=channels)
        mntGrp.disableChannels(ch)
        self.info("Disabled %r channels in %r" % (ch, str(mntGrp)))
        if len(ch_to_skip) > 0:
            msg = "Skipped %r, not founds in %r" % (ch_to_skip, str(mntGrp))
            self.warning(msg)


class meas_enable_all(Macro):
    """
    Enable all counter channels of the measurement group
    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None, "Measurement"], ]

    def run(self, mntGrp):
        elem = mntGrp.getCounterNames()
        mntGrp.enableChannels(elem)
        self.info("Enabled %r channels in %r" % (elem, str(mntGrp)))


class meas_disable_all(Macro):
    """
    Disable all counter channels of the measurement Group
    """

    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None, "Measurement"], ]

    def run(self, mntGrp):
        elem = mntGrp.getCounterNames()
        mntGrp.disableChannels(elem)
        self.info("Disabled %r channels in %r" % (elem, str(mntGrp)))


class meas_status(Macro):
    """
    Shows the current configuration of the measurementGroup,
    if the parameter is empty it shows the state of the ActiveMeasurementGroup
    """
    param_def = [
        ['MeasurementGroup', Type.MeasurementGroup, None, "mntGrp Name"],
    ]

    def run(self, mntGrp):
        if mntGrp is None:
            self.info('entering')
            mntGrp = self.getEnv('ActiveMntGrp')
            mntGrp = self.getObj(mntGrp, type_class=Type.MeasurementGroup)
            self.info(
                "No measurement Group given so take active one %s" % mntGrp)
        val = 'Channel', 'Enabled', 'Plot_type', 'Plot axes', 'Output'
        self.warning("%10s %10s %10s %10s %10s" % val)
        for channel in mntGrp.getChannels():
            val = (channel['name'], channel['enabled'], channel['plot_type'],
                   channel['plot_axes'], channel['output'])
            self.warning("%10s %10s %10s %10s %10s" % val)
