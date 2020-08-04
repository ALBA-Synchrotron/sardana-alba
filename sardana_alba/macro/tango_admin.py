import logging
import functools

import tangoctl

from sardana.macroserver.macro import macro, Type, Optional

from sardana_alba.macro.util.log import MacroOutputLogHandler

Servers = [
    'servers', [["server", Type.String, None, "server expression"]],
    None, "list of servers (accepts server expression ex: Ni660x/*)"
]

OptionalServers = [
    'servers', [["server", Type.String, Optional, "server expression"]],
    Optional, "optional list of servers (accepts server expression ex: Ni660x/*)"
]

log_output = functools.partial(MacroOutputLogHandler, logger=tangoctl.log, level=logging.INFO)


@macro([Servers])
def ds_start(self, servers):
    """Start the device server(s)"""
    with log_output(self):
        tangoctl.starter_start_servers(server_name=servers)


@macro([Servers])
def ds_stop(self, servers):
    """Stop the device server(s)"""
    with log_output(self):
        tangoctl.starter_stop_servers(server_name=servers)


@macro([Servers])
def ds_restart(self, servers):
    """Restart the device server(s)"""
    with log_output(self):
        tangoctl.starter_restart_servers(server_name=servers)


@macro([OptionalServers])
def ds_tree(self, servers):
    """
    Display tree of servers. The given servers represent a filter. Example:

    Door1 [1]: treeDS TangoTest/* *Tornado*

    controls05.cells.es:10000
    |-- TangoTest
    │   |-- tcoutinho1
    │   │   +-- sys/tg_test/tc1 (TangoTest)
    │   |-- tcoutinho2
    │   │   +-- sys/tg_test/tc2 (TangoTest)
    │   +-- test
    │       +-- sys/tg_test/1 (TangoTest)
    +-- WebTornadoDS
        +-- vacuum
            +-- web/tornado/vacuum (WebTornadoDS4Impl)
    """
    if servers == [None]:
        servers = None
    tree = tangoctl.server_tree(server_name=servers)
    text = tree.show(line_type="ascii", stdout=False)
    for line in text.split("\n"):
        self.output(line)


@macro([OptionalServers])
def starter_tree(self, servers):
    """
    Display tree of starters. The given servers represent a filter. Example:

    Door1 [1]: starter_tree TangoTest/*
    controls05.cells.es:10000
    |-- controls05
    |   |-- level 1
    |   |   +-- TangoTest/test
    |   |-- level 2
    |   |   +-- TangoTest/tcoutinho1
    |   +-- level 3
    |       +-- TangoTest/tcoutinho2
    |-- ibl1301
    +-- ibl1302
    """
    if servers == [None]:
        servers = None
    tree = tangoctl.starter_tree(server_name=servers)
    text = tree.show(line_type="ascii", stdout=False)
    for line in text.split("\n"):
        self.output(line)


startDS = ds_start
