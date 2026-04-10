import simpy
import random
import pandas as pd
from core_engine import SharedChannel, NetworkNode
from protocols import CSMACaProtocol, SlottedAlohaProtocol, Packet
from ml_pipeline import predict_optimal_protocol

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
    print("Initializing Research Simulator with ML Control...")
    env = simpy.Environment()
    logger = DataLogger(env)
    channel = SharedChannel(env, logger=logger)
    
    nodes = []
    NUM_NODES = 50          # High load scenario
    BASE_ARRIVAL_RATE = 400 # High traffic
    
    print("\n[PHASE 1] Starting network with baseline protocol (PureALOHA)...")
    for i in range(NUM_NODES):
        x_pos = random.randint(0, 500)
        y_pos = random.randint(0, 500)
        
        new_node = NetworkNode(env, node_id=str(i), x=x_pos, y=y_pos, channel=channel)
        # We purposely start with a bad protocol for high load
        new_node.mac_protocol = SlottedAlohaProtocol(new_node) 
        nodes.append(new_node)
        
        env.process(bursty_traffic_generator(env, new_node, BASE_ARRIVAL_RATE, logger))
    
    # Run the simulation for just 0.2 seconds to gather baseline stats
    env.run(until=0.2)
    
    # Ask Aadya's logger how the network is doing
    current_throughput, current_collision_rate = logger.calculate_metrics(0.2)
    print(f"--> Baseline Collision Rate: {current_collision_rate:.2%}")
    
    # --- ML INTERVENTION POINT ---
    print("\n[PHASE 2] Pausing simulation. Asking ML Classifier for optimal protocol...")
    current_network_state = {
        'nodes': NUM_NODES,
        'arrival_rate': BASE_ARRIVAL_RATE,
        'collision_rate': current_collision_rate,
        'delay': 0.1,        # Placeholder until delay tracking is added
        'queue_variance': 5.0 # Placeholder
    }
    
    best_protocol_name = predict_optimal_protocol(current_network_state)
    print(f"--> ML Model Decision: Switch entire network to {best_protocol_name}")
    
    # Apply the AI's decision
    if best_protocol_name == "CSMA/CA":
        print("--> Executing Dynamic Protocol Swap to CSMA/CA...")
        for node in nodes:
            node.mac_protocol = CSMACaProtocol(node)
    
    # --- RESUME SIMULATION ---
    print("\n[PHASE 3] Resuming simulation with new protocol...")
    env.run(until=1.0) # Run for the remaining 0.8 seconds
    
    # Final Results
    final_throughput, final_col_rate = logger.calculate_metrics(1.0)
    print("\n--- FINAL SIMULATION RESULTS ---")
    print(f"Packets Generated: {logger.total_generated}")
    print(f"Successful Deliveries: {logger.successful_tx}")
    print(f"Collisions: {logger.collisions}")
    print("--------------------------")
    print(f"Final Collision Rate: {final_col_rate:.2%}")