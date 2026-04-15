import simpy
import math

# --- CONSTANTS ---
# Speed of light in a vacuum (meters per second). 
# We use a slightly scaled down version or micro-seconds in actual network sims to avoid floating point underflow, 
# but for this architecture, we will stick to standard physics.
SPEED_OF_LIGHT = 300_000_000 

import simpy
import math

SPEED_OF_LIGHT = 300_000_000 

class SharedChannel:
    def __init__(self, env, logger=None):
        self.env = env
        self.nodes = []
        self.logger = logger # We attach Aadya's logger here to record physical results

    def register_node(self, node):
        self.nodes.append(node)

    def broadcast(self, sender, packet):
        # We comment out the physical broadcast print so the logs aren't too cluttered
        # print(f"[{self.env.now:.6f}] PHYSICAL: Node {sender.node_id} broadcasting...")
        for receiver in self.nodes:
            if receiver == sender:
                continue 
            
            distance = math.hypot(sender.x - receiver.x, sender.y - receiver.y)
            prop_delay = distance / SPEED_OF_LIGHT
            self.env.process(self._deliver_signal(receiver, packet, prop_delay))

    def _deliver_signal(self, receiver, packet, delay):
        yield self.env.timeout(delay)
        # Spawn a new process on the receiver to handle the incoming wave over time
        self.env.process(receiver.process_incoming_signal(packet))


class NetworkNode:
    def __init__(self, env, node_id, x, y, channel):
        self.env = env
        self.node_id = node_id
        self.x = x
        self.y = y
        self.channel = channel
        self.channel.register_node(self)
        self.mac_protocol = None 
        
        # --- NEW COLLISION TRACKING ---
        self.receiving_signals = 0
        self.corrupted_reception = False

    def process_incoming_signal(self, packet):
        """A SimPy process that tracks overlapping signals."""
        self.receiving_signals += 1
        
        # If we are already receiving a signal, and another one hits, it's a collision!
        if self.receiving_signals > 1:
            self.corrupted_reception = True

        # Pass it to Rajat's MAC layer so it knows the channel is busy
        if self.mac_protocol:
            self.mac_protocol.handle_incoming_signal(packet)

        # Wait for the entire packet to physically pass over the antenna
        packet_duration = (packet.size * 8) / 1_000_000 # Assuming 1 Mbps transmission rate
        yield self.env.timeout(packet_duration)

        # The packet has finished passing over the antenna
        self.receiving_signals -= 1

        # If the antenna is now quiet, check if the reception was clean
        if self.receiving_signals == 0:
            if self.corrupted_reception:
                if self.channel.logger: self.channel.logger.raw_collisions += 1
                self.corrupted_reception = False
            else:
                if self.channel.logger: self.channel.logger.raw_successful_tx += 1
                
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