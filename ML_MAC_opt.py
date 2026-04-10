import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from collections import deque

np.random.seed(42)
 
# --- PACKET CLASS ---
class Packet:
    """ Represents a data packet with an arrival timestamp."""
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time

# --- MAC SIMULATOR ---
class MACSimulator:
    """ Simulates MAC protocols under varying network loads and node counts."""
    def __init__(self, num_nodes, arrival_rate, protocol, sim_time=1000):
        self.num_nodes = num_nodes
        self.arrival_rate = arrival_rate
        self.protocol = protocol
        self.sim_time = sim_time
        self.queues = [deque() for _ in range(num_nodes)]
        self.backoff = [0] * num_nodes
        
        self.successful_packets = 0
        self.collisions = 0
        self.total_delay = 0
        self.total_generated = 0
        self.delay_log = [] # Stores individual packet delays for distribution analysis

    def run(self):
        for t in range(self.sim_time):

            # Step 1: Dynamic Traffic Generation (MMPP Model)
            # Simulates bursty traffic behavior common in real-world networks
            for i in range(self.num_nodes):
                is_burst = np.random.random() < 0.2 
                current_rate = self.arrival_rate * 5 if is_burst else self.arrival_rate * 0.5
                
                arrivals = np.random.poisson(current_rate)
                for _ in range(arrivals):
                    self.queues[i].append(Packet(t))
                    self.total_generated += 1

            transmitting_nodes = []

            # Step 2: Protocol-specific Transmission Logic
            for i in range(self.num_nodes):
                if len(self.queues[i]) == 0:
                    continue
                
                if self.backoff[i] > 0:
                    self.backoff[i] -= 1
                    continue

                if self.protocol == "PureALOHA":
                    transmitting_nodes.append(i)
                elif self.protocol == "SlottedALOHA":
                    if t % 5 == 0: # Slot synchronization
                        transmitting_nodes.append(i)
                elif self.protocol == "CSMA":
                    # Simplified Carrier Sense logic
                    transmitting_nodes.append(i)

            # Step 3: Collision Detection and Success Handling
            if len(transmitting_nodes) == 1:
                node_idx = transmitting_nodes[0]
                packet = self.queues[node_idx].popleft()
                
                self.successful_packets += 1
                delay = t - packet.arrival_time
                self.total_delay += delay
                self.delay_log.append(delay)

            elif len(transmitting_nodes) > 1:
                self.collisions += 1
                # Exponential backoff simulation
                for node in transmitting_nodes:
                    self.backoff[node] = np.random.randint(1, 5)

        # Performance Metrics Calculation
        throughput = self.successful_packets / self.sim_time
        collision_rate = self.collisions / max(1, self.total_generated)
        avg_delay = self.total_delay / max(1, self.successful_packets)

        return {
            "nodes": self.num_nodes,
            "arrival_rate": self.arrival_rate,
            "throughput": throughput,
            "collision_rate": collision_rate,
            "delay": avg_delay
        }

# --- DATASET GENERATION ---
def generate_dataset():
    """Iterates through protocol configurations to build a training dataset."""
    data = []
    protocols = ["PureALOHA", "SlottedALOHA", "CSMA"]
    print("Executing simulation batches...")
    for protocol in protocols:
        for nodes in range(10, 110, 10):
            for load in np.linspace(0.1, 1.0, 10):
                sim = MACSimulator(nodes, load, protocol)
                result = sim.run()
                result["protocol"] = protocol
                data.append(result)
    return pd.DataFrame(data)

df = generate_dataset()

# --- ML MODEL TRAINING ---
features = ["nodes", "arrival_rate", "collision_rate", "delay"]
target = "throughput"
models = {}

for protocol in df["protocol"].unique():
    subset = df[df["protocol"] == protocol]
    X = subset[features]
    y = subset[target]
    model = LinearRegression()
    model.fit(X, y)
    models[protocol] = model

# --- DYNAMIC PROTOCOL SELECTION ---
def select_optimal_protocol(nodes, arrival_rate):
    """ Predicts the best protocol based on trained regression models."""
    temp_sim = MACSimulator(nodes, arrival_rate, "PureALOHA")
    base_metrics = temp_sim.run()
    input_features = [nodes, arrival_rate, base_metrics["collision_rate"], base_metrics["delay"]]
    input_df = pd.DataFrame([input_features], columns=features)
    
    predictions = {}
    for protocol, model in models.items():
        pred = model.predict(input_df)[0]
        predictions[protocol] = max(0, pred)

    best_protocol = max(predictions, key=predictions.get)
    return best_protocol, predictions

# --- DATA VISUALIZATION MODULE ---
def plot_network_performance(dataframe):
    """ Generates comparative performance analysis graphs."""
    print("\nVisualizing Results...")
    plt.figure(figsize=(14, 6))

    # Subplot 1: Throughput Analysis
    plt.subplot(1, 2, 1)
    for proto in dataframe['protocol'].unique():
        subset = dataframe[dataframe['protocol'] == proto]
        avg_thru = subset.groupby('arrival_rate')['throughput'].mean()
        plt.plot(avg_thru.index, avg_thru.values, marker='o', label=proto)
    plt.title("Throughput vs Offered Load (Bursty Traffic)")
    plt.xlabel("Arrival Rate (G)")
    plt.ylabel("System Throughput (S)")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    # Subplot 2: Collision Analysis
    plt.subplot(1, 2, 2)
    for proto in dataframe['protocol'].unique():
        subset = dataframe[dataframe['protocol'] == proto]
        avg_coll = subset.groupby('arrival_rate')['collision_rate'].mean()
        plt.plot(avg_coll.index, avg_coll.values, marker='x', label=proto)
    plt.title("Collision Rate Trends")
    plt.xlabel("Arrival Rate (G)")
    plt.ylabel("Collision Probability")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    plt.savefig("performance_analysis_plot.png")
    plt.show()

# --- EXECUTION ---
best_choice, predictions = select_optimal_protocol(50, 0.7)

print("\n--- Protocol Performance Predictions ---")
for proto, val in predictions.items():
    print(f"{proto}: {val:.4f} throughput")

print(f"\nDecision Engine Selection: {best_choice}")

# Generate and display analytical plots
plot_network_performance(df)
