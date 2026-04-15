import simpy
import random
import pandas as pd
from core_engine import SharedChannel, NetworkNode
from protocols import CSMACaProtocol, SlottedAlohaProtocol, Packet
from ml_pipeline import predict_optimal_protocol

class DataLogger:
    def __init__(self, env, num_nodes):
        self.env = env
        self.num_nodes = num_nodes
        self.total_generated = 0
        
        # We only initialize the RAW trackers here now
        self.raw_successful_tx = 0  
        self.raw_collisions = 0     

    # These properties calculate the true numbers on the fly
    @property
    def successful_tx(self):
        return self.raw_successful_tx // max(1, (self.num_nodes - 1))

    @property
    def collisions(self):
        return self.raw_collisions // max(1, (self.num_nodes - 1))

    def calculate_metrics(self, duration):
        throughput = self.successful_tx / duration
        collision_rate = self.collisions / max(1, self.total_generated)
        return throughput, collision_rate

def bursty_traffic_generator(env, node, base_rate, logger):
    """
    Markov Modulated Poisson Process (MMPP) as defined in IEEE paper.
    """
    packet_id_counter = 0
    is_burst_state = False
    
    while True:
        if random.random() < 0.10:
            is_burst_state = not is_burst_state
            
        current_rate = base_rate * 5 if is_burst_state else base_rate * 0.5
        yield env.timeout(random.expovariate(current_rate))
        
        packet_id_counter += 1
        logger.total_generated += 1
        pkt_name = f"N{node.node_id}_P{packet_id_counter}"
        
        new_packet = Packet(sender=node, dest=None, packet_id=pkt_name, size=250)
        node.mac_protocol.attempt_transmission(new_packet)

def run_simulation_scenario(scenario_name, num_nodes, arrival_rate, sim_time=1.0):
    print(f"\n{'='*50}")
    print(f" SCENARIO: {scenario_name}")
    print(f" Nodes: {num_nodes} | Target Arrival Rate: {arrival_rate}")
    print(f"{'='*50}")
    
    env = simpy.Environment()
    logger = DataLogger(env, num_nodes)
    channel = SharedChannel(env, logger=logger)
    nodes = []
    
    # Initialize with Slotted ALOHA
    for i in range(num_nodes):
        x_pos = random.randint(0, 500)
        y_pos = random.randint(0, 500)
        new_node = NetworkNode(env, node_id=str(i), x=x_pos, y=y_pos, channel=channel)
        new_node.mac_protocol = SlottedAlohaProtocol(new_node) 
        nodes.append(new_node)
        env.process(bursty_traffic_generator(env, new_node, arrival_rate, logger))
    
    # 1. Baseline Probe
    print("[PHASE 1] Baseline Probe (Slotted ALOHA)...")
    env.run(until=0.1)
    _, current_col_rate = logger.calculate_metrics(0.1)
    
    # 2. ML Inference
    print("\n[PHASE 2] ML Inference & Protocol Switching...")
    state = {
        'nodes': num_nodes,
        'arrival_rate': arrival_rate,
        'collision_rate': current_col_rate,
        'delay': 0.1, 
        'queue_variance': 5.0
    }
    best_protocol = predict_optimal_protocol(state)
    print(f"--> XGBoost / Random Forest Decision: {best_protocol}")
    
    if best_protocol == "CSMA/CA":
        print("--> Dynamic Swap: Applying CSMA/CA to all nodes...")
        for node in nodes:
            node.mac_protocol = CSMACaProtocol(node)
            
    # 3. Resume
    print(f"\n[PHASE 3] Resuming simulation to resolve traffic for {sim_time} seconds...")
    env.run(until=sim_time)
    
    # 4. Results
    throughput, col_rate = logger.calculate_metrics(sim_time)
    print("\n--- FINAL METRICS ---")
    print(f"Packets Generated: {logger.total_generated}")
    print(f"Successful Deliveries (Throughput): {logger.successful_tx}")
    print(f"Collisions: {logger.collisions}")
    print(f"Collision Rate: {col_rate:.2%}")
    return logger

if __name__ == "__main__":
    # SCENARIO 1: Moderate Load
    run_simulation_scenario(
        scenario_name="GRAPH VALIDATION (Moderate Load)", 
        num_nodes=50, 
        arrival_rate=20,
        sim_time=1.0
    )
    
    # SCENARIO 2: The Golden Demo (3x Saturated Capacity)
    # 30 nodes * 50 pkts/s = 1500 packets/sec offered load.
    # New packet size (250 bytes) = max physical capacity of 500 packets/sec.
    run_simulation_scenario(
        scenario_name="HIGH STRESS TEST (Demonstrating Concrete Data Flow)", 
        num_nodes=30, 
        arrival_rate=50,
        sim_time=4.0  # Let it run for 4 seconds to build up massive delivery numbers
    )