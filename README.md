# ML-Enhanced Dynamic MAC Protocol Optimization

A continuous-time, physics-aware Discrete-Event Simulation (DES) framework that models MAC-layer protocols (Slotted ALOHA, CSMA/CA) and utilizes an ensemble Machine Learning classifier to dynamically optimize protocol selection in real-time based on varying network loads.

**Team:** Mayank Malik (Lead) · Kanusha Sharma · Rajat Sharma · Aadya Vaid · Ananya Alagh  
**Course:** Data Communication & Networks (DCN)

---

## 📌 What This Does

Running a static MAC protocol regardless of traffic conditions is highly inefficient. Under light traffic, the carrier-sensing overhead of CSMA adds unnecessary latency. Under heavy, bursty traffic, ALOHA's random access mechanism collapses into a catastrophic broadcast storm of collisions.

This project solves this by treating protocol selection as an AI classification problem. We built a custom **SimPy-based Discrete-Event Simulator** that models physical RF propagation delay, spatial node distribution, and bursty traffic (Markov Modulated Poisson Process). 

Instead of guessing the theoretical throughput, a **Random Forest Classifier** constantly monitors network metrics (Node Count, Arrival Rate, Collision Probability) and predicts the optimal protocol. When the network crosses the saturation threshold, the AI dynamically swaps the entire network's MAC protocol on the fly to prevent gridlock. 

**Performance Highlight:** In a stress-test scenario (50 nodes, 400 pkts/sec base rate) generating 17,465 packets in one second, the ML engine autonomously transitioned the network to CSMA/CA. The binary exponential backoff algorithm restricted the collision rate to just **0.29%**, successfully averting a broadcast storm.

---

## 🏗️ Architecture & Code Structure

The monolithic time-stepped loop has been entirely replaced by a modular, continuous-time DES architecture.

```text
.
├── core_engine.py       # SimPy physics engine, physical RF propagation delay (d/c), receiver collision logic
├── protocols.py         # MAC state machines (Slotted ALOHA synchronisation, CSMA/CA with Binary Exponential Backoff)
├── generate_dataset.py  # Automated offline data generation across hundreds of random network seeds
├── ml_pipeline.py       # Random Forest classifier training, feature extraction, and real-time inference
├── main.py              # The master simulation loop demonstrating dynamic ML protocol swapping
├── plot_results.py      # Seaborn visualization module (95% CI graphs, Decision Boundary Heatmaps)
└── README.md

### The Physics Engine (`core_engine.py`)
Unlike basic simulators that assume instant communication, this engine assigns `(X, Y)` coordinates to nodes and calculates exact propagation delays using the speed of light. Receiver antennas dynamically track overlapping RF waves to calculate true physical collisions, accurately simulating the Hidden Terminal Problem.

### The ML Pipeline (`ml_pipeline.py`)
Upgraded from basic Linear Regression to a **Random Forest Classifier**. Instead of calculating continuous throughput values, the model learns the non-linear "decision boundaries" where ALOHA's throughput violently collapses, classifying the `optimal_protocol_id` and saving the intelligence as a `.pkl` file for live deployment.

---

## 📊 Protocol Summary

| Protocol | Transmission Logic | Ideal Use Case |
|---|---|---|
| **Slotted ALOHA** | Synchronizes to strict time boundaries. No carrier sensing. | Highly efficient for sparse networks with low traffic load. |
| **CSMA/CA** | Listens before transmitting (DIFS). Uses Binary Exponential Backoff on collision. | Mandatory for dense networks and bursty traffic to prevent storms. |

---

## 🚀 Running It

**1. Install Dependencies**
```bash
pip install numpy pandas scikit-learn simpy matplotlib seaborn
```

**2. Generate the Physics Dataset (Offline Phase)**
Simulates hundreds of network configurations to generate `real_network_data.csv`.
```bash
python generate_dataset.py
```

**3. Train the AI Model**
Consumes the CSV, trains the Random Forest classifier, and exports `mac_protocol_selector.pkl`.
```bash
python ml_pipeline.py
```

**4. Run the Live Simulation**
Starts a high-load network, pauses to let the ML model analyze the collision metrics, dynamically swaps the protocol, and logs the final performance.
```bash
python main.py
```

**5. Generate Research Graphs**
Creates publication-ready IEEE-formatted graphs (Throughput vs. Load, Collision Rate, and AI Decision Heatmaps) with 95% Confidence Intervals.
```bash
python plot_results.py
```

---

## 📚 References

1. Abramson, N. — *The ALOHA System: Another Alternative for Computer Communications* (1970)
2. Metcalfe, R. M. & Boggs, D. R. — *Ethernet: Distributed Packet Switching for Local Computer Networks* (1976)
3. *Automatic MAC Protocol Selection in Wireless Networks Based on Reinforcement Learning* — ResearchGate (2020)
4. [georgevangelou/aloha_protocol_simulator](https://github.com/georgevangelou/aloha_protocol_simulator)
5. [yokaiAG/ALOHA-course](https://github.com/yokaiAG/ALOHA-course)
6. [mindt102/csma-ca-simulation](https://github.com/mindt102/csma-ca-simulation)
```