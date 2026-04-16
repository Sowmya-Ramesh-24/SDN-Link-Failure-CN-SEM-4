#!/usr/bin/env python3
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.link import TCLink

class TriangleTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')

        # Host-switch links
        self.addLink(h1, s1)
        self.addLink(h2, s3)
        self.addLink(h3, s2)

        # Switch-switch links (triangle topology)
        self.addLink(s1, s2)  # Primary path
        self.addLink(s2, s3)  # Primary path
        self.addLink(s1, s3)  # Backup path

def run():
    setLogLevel('info')
    topo = TriangleTopo()
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(
            name, ip='127.0.0.1', port=6633),
        link=TCLink,
        autoSetMacs=True
    )
    net.start()
    print("\n=== Network Started ===")
    print("  h1 -- s1 -- s2 -- h3")
    print("         |    |")
    print("         s3 --+")
    print("         |")
    print("        h2")
    print("\nPrimary path h1->h2: s1->s2->s3")
    print("Backup  path h1->h2: s1->s3")
    print("==============================\n")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    run()
