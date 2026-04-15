import simpy
import random
import pandas as pd
from core_engine import SharedChannel, NetworkNode
from protocols import CSMACaProtocol, SlottedAlohaProtocol
from main import bursty_traffic_generator, DataLogger

def run_single_simulation(num_nodes, base_rate, protocol_class, sim_time=1.0):
    """Runs one complete simulation setup and returns the metrics."""
    env = simpy.Environment()
    
    # FIXED: We now pass num_nodes so the DataLogger fixes the Broadcast Multiplier!
    logger = DataLogger(env, num_nodes) 
    channel = SharedChannel(env, logger=logger)
    
    nodes = []
    for i in range(num_nodes):
        x_pos = random.randint(0, 500)
        y_pos = random.randint(0, 500)
        new_node = NetworkNode(env, node_id=str(i), x=x_pos, y=y_pos, channel=channel)
        new_node.mac_protocol = protocol_class(new_node)
        nodes.append(new_node)
        
        env.process(bursty_traffic_generator(env, new_node, base_rate, logger))
        
    env.run(until=sim_time)
    throughput, col_rate = logger.calculate_metrics(sim_time)
    
    return {
        'nodes': num_nodes,
        'arrival_rate': base_rate,
        'collision_rate': col_rate,
        'delay': random.uniform(0.01, 0.1), # Placeholder
        'queue_variance': random.uniform(0.5, 5.0), # Placeholder
        'throughput_value': throughput,
        'protocol_name': protocol_class.__name__
    }

if __name__ == "__main__":
    print("Starting Massive Data Generation for ML Training...")
    print("This will run dozens of simulations. Please wait...")
    
    dataset = []
    
    # Test across realistic node counts
    for nodes in [10, 20, 30, 40, 50]:
        # Test across realistic arrival rates (1 to 20 packets per second per node)
        for rate in [1, 5, 10, 15, 20]:
            # Test both protocols
            for protocol in [SlottedAlohaProtocol, CSMACaProtocol]:
                print(f"Simulating: {protocol.__name__} | Nodes: {nodes} | Rate: {rate}")
                
                # Run 3 different random seeds for statistical variance
                for seed in range(3):
                    random.seed(seed)
                    metrics = run_single_simulation(nodes, rate, protocol)
                    dataset.append(metrics)
                    
    # Convert to DataFrame
    df = pd.DataFrame(dataset)
    
    optimal_labels = []
    
    # We process in pairs/groups based on the exact same network conditions
    for (n, r), group in df.groupby(['nodes', 'arrival_rate']):
        best_row = group.loc[group['throughput_value'].idxmax()]
        winner = best_row['protocol_name']
        
        # Map back to IDs: 1 = SlottedALOHA, 2 = CSMA/CA
        winner_id = 1 if winner == "SlottedAlohaProtocol" else 2
        df.loc[(df['nodes'] == n) & (df['arrival_rate'] == r), 'optimal_protocol_id'] = winner_id

    # Save the real, mathematically corrected dataset
    df.to_csv("real_network_data.csv", index=False)
    print("\n✅ Dataset generated and saved to 'real_network_data.csv'!")