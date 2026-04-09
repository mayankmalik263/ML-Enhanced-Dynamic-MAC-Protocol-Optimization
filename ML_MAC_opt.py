import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from collections import deque
np.random.seed(42)
 
# PACKET CLASS

class Packet:
    def __init__(self, arrival_time):
        self.arrival_time = arrival_time


 
# MAC SIMULATOR
class MACSimulator:
    def __init__(self, num_nodes, arrival_rate, protocol, sim_time=1000):
        self.num_nodes = num_nodes
        self.arrival_rate = arrival_rate
        self.protocol = protocol
        self.sim_time = sim_time
        
        self.queues = [[] for _ in range(num_nodes)]
        self.backoff = [0] * num_nodes
        
        self.successful_packets = 0
        self.collisions = 0
        self.total_delay = 0
        self.total_generated = 0

    def run(self):
        for t in range(self.sim_time):

            # Step 1: Packet arrivals (Poisson)
            for i in range(self.num_nodes):
                arrivals = np.random.poisson(self.arrival_rate)
                for _ in range(arrivals):
                    self.queues[i].append(Packet(t))

            transmitting_nodes = []

            # Step 2: Decide who transmits
            for i in range(self.num_nodes):
                if len(self.queues[i]) == 0:
                    continue
                
                if self.backoff[i] > 0:
                    self.backoff[i] -= 1
                    continue

                if self.protocol == "PureALOHA":
                    transmitting_nodes.append(i)

                elif self.protocol == "SlottedALOHA":
                    if t % 5 == 0:  # better slot modeling
                        transmitting_nodes.append(i)

                elif self.protocol == "CSMA":
                    # sense channel (approx)
                    channel_busy = False
                    for i in range(self.num_nodes):
                        if len(self.queues[i]) == 0:
                            continue

                        if self.backoff[i] > 0:
                            self.backoff[i] -= 1
                            continue

                        if self.protocol == "CSMA":
                            if not channel_busy:
                                transmitting_nodes.append(i)
                                channel_busy = True

            # Step 3: Transmission outcome
            if len(transmitting_nodes) == 1:
                # node = transmitting_nodes[0]
                self.queues = [deque() for _ in range(self.num_nodes)]
                packet = self.queues[node].popleft()
                
                self.successful_packets += 1
                self.total_delay += (t - packet.arrival_time)

            elif len(transmitting_nodes) > 1:
                self.collisions += 1

                # Backoff mechanism
                for node in transmitting_nodes:
                    self.backoff[node] = np.random.randint(1, 5)

        # Metrics
        throughput = self.successful_packets / self.sim_time
        collision_rate = self.collisions / max(1, self.total_generated)
        avg_delay = self.total_delay / max(1, self.successful_packets)
        utilization = throughput  # approximation

        return {
            "nodes": self.num_nodes,
            "arrival_rate": self.arrival_rate,
            "throughput": throughput,
            "collision_rate": collision_rate,
            "delay": avg_delay,
            "utilization": utilization
        }


 
# DATASET GENERATION
 
def generate_dataset():
    data = []
    protocols = ["PureALOHA", "SlottedALOHA", "CSMA"]

    for protocol in protocols:
        for nodes in range(10, 110, 10):
            for load in np.linspace(0.1, 1.0, 10):
                sim = MACSimulator(nodes, load, protocol)
                result = sim.run()
                result["protocol"] = protocol
                data.append(result)

    return pd.DataFrame(data)


df = generate_dataset()

 
# TRAIN ML MODELS
 
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


 
# PREDICTION
 
def select_best_protocol(nodes, arrival_rate):
    temp_sim = MACSimulator(nodes, arrival_rate, "PureALOHA")
    base_metrics = temp_sim.run()

    input_features = [
        nodes,
        arrival_rate,
        base_metrics["collision_rate"],
        base_metrics["delay"]
    ]

    input_df = pd.DataFrame([input_features], columns=features)

    predictions = {}

    for protocol, model in models.items():
        pred = model.predict(input_df)[0]
        predictions[protocol] = pred

    best_protocol = max(predictions, key=predictions.get)
    return best_protocol, predictions


 
# TEST
 
best, preds = select_best_protocol(50, 0.7)

print("Predictions:")
for p, v in preds.items():
    print(p, round(v, 4))

print("\nBest Protocol:", best)