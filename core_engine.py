import simpy
import math

# --- CONSTANTS ---
# Speed of light in a vacuum (meters per second). 
# We use a slightly scaled down version or micro-seconds in actual network sims to avoid floating point underflow, 
# but for this architecture, we will stick to standard physics.
SPEED_OF_LIGHT = 300_000_000 

class SharedChannel:
    """
    Represents the physical air/medium that carries RF signals.
    """
    def __init__(self, env):
        self.env = env
        self.nodes = []  # List to keep track of all nodes in the network

    def register_node(self, node):
        """Attaches a node to the physical environment."""
        self.nodes.append(node)

    def broadcast(self, sender, packet):
        """
        Simulates the physical transmission of a signal across space.
        When a node transmits, the signal travels to EVERY other node, but it arrives at different times.
        """
        print(f"[{self.env.now:.6f}] PHYSICAL: Node {sender.node_id} broadcasting packet {packet.packet_id}...")
        
        for receiver in self.nodes:
            if receiver == sender:
                continue # Don't send the signal to yourself
            
            # 1. Calculate Euclidean distance (d)
            distance = math.hypot(sender.x - receiver.x, sender.y - receiver.y)
            
            # 2. Calculate propagation delay (t = d/c)
            prop_delay = distance / SPEED_OF_LIGHT
            
            # 3. Schedule the packet to hit the receiver's antenna in the future
            self.env.process(self._deliver_signal(receiver, packet, prop_delay))

    def _deliver_signal(self, receiver, packet, delay):
        """A SimPy process that waits for the delay, then triggers the receiver."""
        yield self.env.timeout(delay)
        receiver.receive_signal(packet)


class NetworkNode:
    """
    Represents a hardware device with an antenna and coordinates.
    """
    def __init__(self, env, node_id, x, y, channel):
        self.env = env
        self.node_id = node_id
        
        # Spatial Coordinates (Meters)
        self.x = x
        self.y = y
        
        # Attach to the physical channel
        self.channel = channel
        self.channel.register_node(self)

        # Placeholder for Rajat's MAC Protocol State Machine
        self.mac_protocol = None 
        
        # Placeholder for Aadya's Traffic Generator Queue
        self.transmit_queue = []

    def receive_signal(self, packet):
        """
        Triggered by the SharedChannel when RF energy hits this node's antenna.
        """
        # We just pass the physical signal up to the MAC layer (Rajat's code)
        if self.mac_protocol:
            self.mac_protocol.handle_incoming_signal(packet)
        else:
            print(f"[{self.env.now:.6f}] PHYSICAL: Node {self.node_id} received signal from {packet.sender_id}, but has no MAC protocol to process it.")


class DummyPacket:
    """Temporary packet class until Rajat/Aadya build theirs."""
    def __init__(self, sender_id, packet_id):
        self.sender_id = sender_id
        self.packet_id = packet_id

# --- TESTING BLOCK ---
if __name__ == "__main__":
    env = simpy.Environment()
    channel = SharedChannel(env)
    
    # Place Node 0 at (0, 0)
    node_0 = NetworkNode(env, node_id=0, x=0, y=0, channel=channel)
    
    # Place Node 1 300 meters away at (300, 0)
    # Light takes exactly 1 microsecond (0.000001 sec) to travel 300 meters.
    node_1 = NetworkNode(env, node_id=1, x=300, y=0, channel=channel)
    
    # Test a physical broadcast
    test_packet = DummyPacket(sender_id=0, packet_id="TEST_01")
    
    # Have Node 0 transmit at exactly T=0
    channel.broadcast(sender=node_0, packet=test_packet)
    
    env.run(until=1.0) # Run for 1 second