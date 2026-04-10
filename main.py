import simpy
import random
import pandas as pd
from core_engine import SharedChannel, NetworkNode
from protocols import CSMACaProtocol, SlottedAlohaProtocol, Packet

class DataLogger:
    """Aadya's module to collect metrics during the simulation."""
    def __init__(self, env):
        self.env = env
        self.total_generated = 0
        self.successful_tx = 0
        self.collisions = 0

    def calculate_metrics(self, duration):
        throughput = self.successful_tx / duration
        collision_rate = self.collisions / max(1, self.total_generated)
        return throughput, collision_rate

def bursty_traffic_generator(env, node, base_rate, logger):
    """
    Aadya's Markov Modulated Poisson Process (MMPP).
    Simulates real-world bursty traffic (like suddenly streaming a video).
    """
    packet_id_counter = 0
    is_burst_state = False
    
    while True:
        # 10% chance to flip between Normal and Burst state after every packet
        if random.random() < 0.10:
            is_burst_state = not is_burst_state
            
        # Burst state generates packets 5x faster
        current_rate = base_rate * 5 if is_burst_state else base_rate * 0.5
        
        # Wait for the Poisson inter-arrival time
        yield env.timeout(random.expovariate(current_rate))
        
        packet_id_counter += 1
        logger.total_generated += 1
        
        # Create packet and hand to MAC layer
        pkt_name = f"N{node.node_id}_P{packet_id_counter}"
        new_packet = Packet(sender=node, dest=None, packet_id=pkt_name, size=1500)
        
        # print(f"[{env.now:.6f}] APP: Node {node.node_id} generated {pkt_name} (Burst: {is_burst_state})")
        node.mac_protocol.attempt_transmission(new_packet)

# --- MASTER SIMULATION BOOTSTRAP ---
if __name__ == "__main__":
    print("Initializing Research Simulator (Scale Test)...")
    env = simpy.Environment()
    channel = SharedChannel(env)
    logger = DataLogger(env)
    
    # 1. Deploy a network of 10 nodes randomly placed in a 500x500 meter grid
    nodes = []
    NUM_NODES = 10
    BASE_ARRIVAL_RATE = 200 # Packets per second
    
    for i in range(NUM_NODES):
        x_pos = random.randint(0, 500)
        y_pos = random.randint(0, 500)
        
        new_node = NetworkNode(env, node_id=str(i), x=x_pos, y=y_pos, channel=channel)
        
        # ASSIGN PROTOCOL HERE (Swap between CSMACaProtocol and SlottedAlohaProtocol to test)
        new_node.mac_protocol = CSMACaProtocol(new_node) 
        nodes.append(new_node)
        
        # Start traffic generator for EVERY node
        env.process(bursty_traffic_generator(env, new_node, BASE_ARRIVAL_RATE, logger))
    
    # Run simulation for 1 full second
    sim_duration = 1.0
    env.run(until=sim_duration)
    
    # Print Aadya's Metrics
    throughput, col_rate = logger.calculate_metrics(sim_duration)
    print("\n--- SIMULATION RESULTS ---")
    print(f"Total Nodes: {NUM_NODES}")
    print(f"Protocol: {type(nodes[0].mac_protocol).__name__}")
    print(f"Packets Generated: {logger.total_generated}")
    print("--------------------------")
    print(f"Throughput (Pkts/sec): {throughput:.2f}")
    print(f"Collision Rate: {col_rate:.2%}")
    print("Note: Success/Collision tracking needs to be wired into physical antenna logic next.")