#!/usr/bin/env python

from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf
from subprocess import call

def myNetwork():

    net = Mininet( topo=None,
                   build=False,
                   ipBase='10.0.0.0/8')

    info( '*** Adding controller\n' )
    info( '*** Add switches\n')
    s1 = net.addSwitch('s1', cls=OVSKernelSwitch, failMode='standalone')

    info( '*** Add hosts\n')
    server = net.addHost('server', cls=Host, ip='10.0.0.1', defaultRoute=None)
    player = net.addHost('player', cls=Host, ip='10.0.0.2', defaultRoute=None)

    info( '*** Add links\n')
    net.addLink(server, s1)
    net.addLink(s1, player)

    info( '*** Starting network\n')
    net.build()
    info( '*** Starting controllers\n')
    for controller in net.controllers:
        controller.start()

    info( '*** Starting switches\n')
    net.get('s1').start([])

    info( '*** Post configure switches and hosts\n')

    from mininet.term import makeTerm
    from mininet.log import setLogLevel
    setLogLevel('info')

    net = myNetwork()

    # Set up terminals after startup
    server = net.get('server')
    player = net.get('player')

    makeTerm(server, cmd='bash -c "cd /home/alireza/mycg/CGReplay/server; echo python3 cg_server1.py; bash"', title='Server Ready')
    makeTerm(player, cmd='bash -c "cd /home/alireza/mycg/CGReplay/player; echo python3 cg_gamer1.py; bash"', title='Player Ready')

    CLI(net)
    net.stop()

    CLI(net)
