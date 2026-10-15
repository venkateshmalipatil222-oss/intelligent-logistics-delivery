# AI, Routing & Optimization Architecture Design

---

## 1. Overview
The **Intelligence Tier** of the Intelligent Logistics & Delivery Optimization Platform (ILDO) provides pure, deterministic, and explainable decision algorithms for:
1. **Intelligent Driver Assignment**: Constraint-driven multi-factor driver scoring.
2. **Dijkstra Urban Shortest-Path Routing**: Graph-based shortest path with bypass and arterial waypoint generation.
3. **Multi-Stop Batch Tour Optimization**: Nearest-Neighbor Traveling Salesperson (TSP) heuristic with priority bias.
4. **Transparent Operating Cost Estimation**: Itemized costing covering energy consumption, driver labor hours, fleet depreciation, and taxes.

---

## 2. Multi-Factor Driver Assignment Engine

### 2.1 Constraint Satisfaction (Hard Filters)
Before computing scores, every candidate driver must satisfy all operational constraints. If any constraint fails, the driver is disqualified with a documented rejection reason:
1. **Status Feasibility**: Driver status $\notin \{\text{OFFLINE}, \text{UNAVAILABLE}\}$.
2. **Vehicle Assignment**: Driver must have an active vehicle assigned, and vehicle status $\neq \text{MAINTENANCE}$.
3. **Payload Weight Limit**: $\text{Package Weight (kg)} \le \text{Vehicle Maximum Payload (kg)}$.
4. **Payload Volume Limit**: $\text{Package Volume (m³)} \le \text{Vehicle Maximum Cargo Volume (m³)}$.
5. **Workload Saturation**: $\text{Active Deliveries Count} < \text{Maximum Concurrent Cap (3)}$.

### 2.2 Mathematical Scoring Formulation
For all eligible candidates, an aggregate match score $S \in [0.0, 100.0]$ is computed:

$$S = w_{\text{prox}} \cdot S_{\text{prox}} + w_{\text{work}} \cdot S_{\text{work}} + w_{\text{perf}} \cdot S_{\text{perf}} + w_{\text{veh}} \cdot S_{\text{veh}}$$

| Factor | Weight ($w_i$) | Component | Scoring Function ($S_i \in [0, 100]$) |
|---|:---:|---|---|
| **Proximity** | `0.35` | Distance from driver's GPS coordinates to pickup warehouse | $S_{\text{prox}} = \max\left(0, \min(100, 100 - (\text{dist\_km} \times 3.0))\right)$ |
| **Workload** | `0.25` | Current active delivery queue | $S_{\text{work}} = \max\left(0, 100 - (\text{active\_deliveries} \times 35.0)\right)$ |
| **Performance** | `0.20` | Rating and historical delivery success ratio | $S_{\text{perf}} = 0.60 \cdot (\text{Rating} \times 20) + 0.40 \cdot \left(\frac{\text{Completed}}{\text{Total}} \times 100\right)$ |
| **Vehicle Fit** | `0.20` | Zero-emission EV bonus & payload right-sizing | Base $50 + 20 \text{ (EV)} + 25 \text{ (Optimal Size Category)}$ |

---

## 3. Route Optimization & Multi-Stop TSP

### 3.1 Dijkstra Shortest Path on Urban Waypoint Graph
- Built on `networkx.Graph`, modeling arterial corridors, bypass flyovers, and depot junctions.
- Road circuity factor $\gamma = 1.28$ converts great-circle Haversine distances to realistic road kilometers:
  $$d_{\text{road}} = \gamma \cdot d_{\text{haversine}}$$
- Exact Dijkstra shortest path minimizes cumulative edge weights while avoiding congested city nodes where bypasses exist.

### 3.2 Nearest-Neighbor TSP Heuristic with Priority Bias
For multi-stop delivery batches originating from a central fulfillment hub:
1. Start at warehouse depot $D_0 = (\text{lat}_0, \text{lon}_0)$.
2. Iteratively select next unvisited stop $S^* = \arg\min_{S \in \mathcal{U}} \left( d(S_t, S) \cdot \beta(S) \right)$ where:
   - $\beta(\text{URGENT}) = 0.70$ (prioritized earlier in sequence)
   - $\beta(\text{HIGH}) = 0.85$
   - $\beta(\text{MEDIUM/LOW}) = 1.00$
3. Compute total optimized route kilometers and compare with naive FIFO sequence to report explicit distance and fuel savings.

---

## 4. Transparent Operating Cost Model

Each delivery quote is itemized down to unit economic drivers:
1. **Base Dispatch Fee**: Flat terminal handling fee ($₹40.00$).
2. **Fuel / Energy Consumption**:
   $$\text{Fuel Expense} = \left(\frac{\text{Distance (km)}}{\text{Efficiency (km/L or km/kWh)}}\right) \times \text{Unit Fuel Price}$$
   - *Diesel:* ₹92.50/L (Typical Van: 12 km/L, Truck: 7.5 km/L)
   - *EV Charging:* ₹8.80/kWh (Electric Van: 16 km/kWh)
   - *Petrol:* ₹101.20/L (Courier Bike: 38 km/L)
3. **Driver Labor Hours**:
   $$\text{Labor} = \left(\frac{\text{Distance}}{30 \text{ km/h}} + \frac{15 \text{ mins handling}}{60}\right) \times ₹130.00/\text{hr}$$
4. **Fleet Wear & Depreciation**: $\text{Distance} \times ₹3.20/\text{km}$.
5. **Special Surcharges**:
   - Heavy Weight ($> 15\text{ kg}$): $(\text{Weight} - 15) \times ₹4.50/\text{kg}$.
   - Cold Chain Refrigeration: Flat ₹65.00 + ₹2.00/kg.
   - Urgent / High Priority: $+35\%$ / $+18\%$ operating margin.
6. **GST**: $18\%$ statutory tax on freight logistics services.
