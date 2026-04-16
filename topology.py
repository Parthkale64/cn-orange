from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

def run_network():
    print("Starting Mininet Topology for POX Controller...")
    # Initialize network with a Remote Controller
    net = Mininet(controller=RemoteController, switch=OVSSwitch)
    
    # Add the remote POX Controller (Port 6633 is crucial for POX)
    c0 = net.addController('c0', port=6633)
    
    # Add a single switch (OpenFlow 1.0 default)
    s1 = net.addSwitch('s1')
    
    # Add 3 hosts
    h1 = net.addHost('h1', mac='00:00:00:00:00:01', ip='10.0.0.1/24')
    h2 = net.addHost('h2', mac='00:00:00:00:00:02', ip='10.0.0.2/24')
    h3 = net.addHost('h3', mac='00:00:00:00:00:03', ip='10.0.0.3/24')
    
    # Create links
    net.addLink(h1, s1)
    net.addLink(h2, s1)
    net.addLink(h3, s1)
    
    # Start the network
    net.start()
    
    # Open Mininet Command Line Interface
    CLI(net)
    
    # Cleanup after exiting CLI
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run_network()
