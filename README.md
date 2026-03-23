# ML-Enhanced Dynamic MAC Protocol Optimization

Simulates Pure ALOHA, Slotted ALOHA, and CSMA/CD, then trains a small ML model to pick whichever protocol performs best for the current network conditions.

**Team:** Mayank Malik (Lead) · Kanusha Sharma · Rajat Sharma · Aadya Vaid · Ananya Alagh  
**Course:** Data Communication & Networks (DCN)

---

## What This Does

Running one MAC protocol regardless of traffic conditions is wasteful. Under light load, CSMA's carrier-sense overhead adds latency for no reason. Under heavy load, ALOHA's random access turns into a collision storm.

This project runs all three protocols across a range of node counts and traffic loads, collects throughput/collision/delay data, and fits a regression model per protocol. Given current conditions, it predicts throughput for each one and returns the best.

Quick example — 50 nodes, 70% arrival rate:

```
Predictions:
PureALOHA    0.0019
SlottedALOHA 0.0
CSMA         1.0

Best Protocol: CSMA
```

At that load ALOHA variants collapse. CSMA handles it.

---

## Code Structure

```
.
├── mac_simulator.py     # Everything: simulation, dataset gen, ML, prediction
└── README.md
```

**`Packet`** holds an arrival timestamp. That's it.

**`MACSimulator`** runs the actual simulation. Each time slot:
1. Packets arrive per node via Poisson process
2. Each node with queued data decides whether to transmit based on its protocol
3. One transmitter → success. Multiple → collision, random backoff (1–4 slots)

**`generate_dataset()`** runs 300 simulations: 3 protocols × 10 node counts (10–100) × 10 load levels (0.1–1.0).

**`select_best_protocol(nodes, arrival_rate)`** runs a quick baseline sim to get collision and delay features, runs those through all three trained models, and returns the one predicting highest throughput.

---

## Protocol Summary

| Protocol | When it transmits | Theoretical max throughput |
|---|---|---|
| Pure ALOHA | Whenever it wants | ~18.4% |
| Slotted ALOHA | Every 5th slot | ~36.8% |
| CSMA | When channel is idle | Load-dependent |

---

## The ML Part

Three separate `LinearRegression` models — one per protocol. Features: `[nodes, arrival_rate, collision_rate, delay]`. Target: `throughput`.

One model for all three protocols would just average across their different throughput curves and miss the crossover points. Separate models let the selector catch, for instance, that Slotted ALOHA is better than CSMA at low load even though CSMA dominates at high load.

---

## Running It

```bash
pip install numpy pandas scikit-learn
python ML_MAC_opt.py
```

Dataset generation takes around 30 seconds (300 sims × 1000 slots each), then trains and prints predictions.

---

## References

1. Abramson, N. — *The ALOHA System: Another Alternative for Computer Communications* (1970)
2. Metcalfe, R. M. & Boggs, D. R. — *Ethernet: Distributed Packet Switching for Local Computer Networks* (1976)
3. *Automatic MAC Protocol Selection in Wireless Networks Based on Reinforcement Learning* — ResearchGate (2020)
4. [georgevangelou/aloha_protocol_simulator](https://github.com/georgevangelou/aloha_protocol_simulator)
5. [yokaiAG/ALOHA-course](https://github.com/yokaiAG/ALOHA-course)
6. [mindt102/csma-ca-simulation](https://github.com/mindt102/csma-ca-simulation)
