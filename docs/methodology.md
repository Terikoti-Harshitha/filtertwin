# FilterTwin Mathematical Methodology & Machine Learning

## 1. Mathematical Degradation Models

Filter degradation is modeled via an internal dimensionless hidden degradation index:
$$D(t) \in [0.0, 1.0]$$
where $D=0$ represents a fresh cartridge and $D=1$ denotes the end-of-life (EOL) criterion.

### A. Linear Degradation
$$D(t) = \min\left(1.0, \frac{t}{T}\right)$$
where $T$ is the nominal filter lifespan in days.

### B. Exponential Degradation
$$D(t) = \min\left(1.0, \frac{e^{kt} - 1}{e^{kT} - 1}\right)$$
where $k$ controls the curvature rate ($k \approx 0.015 - 0.025$).

### C. Nonlinear Power-Law Degradation
$$D(t) = \min\left(1.0, \left(\frac{t}{T}\right)^p\right)$$
where $p > 1$ (e.g. $p=1.8 - 2.2$) creates an accelerated concave wear dynamic.

### D. Abrupt Step-Change Fault
$$D(t) = \begin{cases} D_{\text{base}}(t) & t < t_f \\ \min(1.0, D_{\text{base}}(t) + \Delta) & t \ge t_f \end{cases}$$
where $t_f$ is the fault trigger day and $\Delta$ is the fault jump magnitude.

---

## 2. Sensor Physical Observation Models

### Flow Rate Model
$$Q(t) = \max\left(0.0, Q_0 (1 - \alpha D(t)) + \delta_q(t) + \epsilon_q(t)\right)$$
- $Q_0$: Initial clean filter flow rate (L/min)
- $\alpha$: Hydraulic restriction coefficient ($\approx 0.55$)
- $\delta_q(t)$: Progressive calibration drift
- $\epsilon_q(t) \sim \mathcal{N}(0, \sigma_q^2)$: Gaussian measurement noise

### Rejection Ratio & Outlet TDS Model
$$R(t) = \text{clamp}(R_0 - \beta D(t), 0.0, 0.999)$$
$$\text{TDS}_{\text{out}}(t) = \max\left(0.0, \min(\text{TDS}_{\text{in}}(t), \text{TDS}_{\text{in}}(t)(1 - R(t)) + \delta_{\text{tds}}(t) + \epsilon_{\text{tds}}(t))\right)$$
$$\text{Rejection \%} = \frac{\text{TDS}_{\text{in}} - \text{TDS}_{\text{out}}}{\text{TDS}_{\text{in}}} \times 100$$

---

## 3. Machine Learning Models for RUL

### Model 1: Fixed-Volume Baseline Heuristic
$$\text{RUL}_{\text{litres}} = \max(0, \text{Capacity} - V_t)$$
$$\text{RUL}_{\text{days}} = \frac{\text{RUL}_{\text{litres}}}{\text{Daily Use (L/day)}}$$

### Model 2: Multivariable Linear Regression
Extracted operational features:
1. Cumulative Volume ($V_t$)
2. Total Dissolved Solids Load: $L_{\text{TDS}} = \sum \text{TDS}_{\text{in}, i} \Delta V_i$
3. Flow Ratio: $F_r = Q_t / Q_0$
4. Rejection Trend: $\Delta R = R_t - R_0$
5. Filter Age (Days)
6. Average Daily Consumption (L/day)
7. Rolling Window 7-day Flow Rate (LPM)

Prediction and coefficient explainability:
$$\hat{y} = \beta_0 + \sum_{j=1}^m \beta_j \left(\frac{x_j - \mu_j}{\sigma_j}\right)$$

### Model 3: Gradient Boosted Decision Trees
HistGradientBoostingRegressor trained on multi-signal features with early stopping and depth control to capture non-additive interactions.

---

## 4. Quantile Uncertainty Intervals

Three quantile models are trained with pinball quantile loss:
- $Q_{10}(x)$: 10th percentile ($\alpha = 0.10$)
- $Q_{50}(x)$: 50th percentile (Median, $\alpha = 0.50$)
- $Q_{90}(x)$: 90th percentile ($\alpha = 0.90$)

Prediction interval:
$$I_{80}(x) = [\hat{Q}_{10}(x), \hat{Q}_{90}(x)]$$

Coverage is verified via Prediction Interval Coverage Probability (PICP):
$$\text{PICP} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(y_i \in I_{80}(x_i)) \times 100\%$$
Average Interval Width:
$$\text{Width} = \frac{1}{N} \sum_{i=1}^N (\hat{Q}_{90}(x_i) - \hat{Q}_{10}(x_i))$$

---

## 5. Anomaly Detection Classification

1. **Gate 1 - Quality**: Missing values, disconnected signals, or $<3$ readings $\to$ `INSUFFICIENT_DATA`. Suppresses RUL.
2. **Gate 2 - Sudden Change**:
   $$\text{Drop Ratio} = \frac{\bar{Q}_{\text{hist}} - Q_t}{\bar{Q}_{\text{hist}}} > 0.35 \quad \text{or} \quad Z_q < -3.0 \to \text{ABRUPT ANOMALY (FLOW DROP)}$$
   $$\text{TDS Jump} = \frac{\text{TDS}_{\text{out}, t} - \bar{\text{TDS}}_{\text{out}}}{\text{TDS}_{\text{in}}} > 0.40 \quad \text{or} \quad Z_{\text{tds}} > 3.0 \to \text{ABRUPT ANOMALY (TDS SPIKE)}$$
3. **Gate 3 - Gradual Wear**:
   Flow ratio $< 0.70$ or $\Delta R < -12\%$ or $V_t > 0.85 \times \text{Capacity} \to \text{GRADUAL WEAR}$.
4. **Gate 4 - Normal**: Healthy baseline state without alerts.
