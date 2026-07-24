import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class OilWellSimulator:
    """
    Simulates a single naturally flowing oil well.
    Choke opening (u) in % [0 to 100].
    Returns Q (bbl/hr), WHP (psi), FLP (psi), BHP (psi).
    """
    def __init__(self):
        self.current_choke = 10.0 # start at 10%
        self.res_pressure = 3500.0 # Reservoir pressure (psi)
        
    def step(self, choke_position):
        # Constrain ramp rate to max +/- 5% per hour
        choke_position = np.clip(choke_position, 0.0, 100.0)
        delta = np.clip(choke_position - self.current_choke, -5.0, 5.0)
        self.current_choke += delta
        u = self.current_choke
        
        # Well Physics Equations
        # As choke opens: Flow (Q) increases, Pressures (WHP, FLP, BHP) drop
        Q = 2.5 * u * (1 + 0.02 * u**0.5) + np.random.normal(0, 0.5)
        WHP = max(200.0, 1800.0 - 12.0 * u - 0.05 * u**2 + np.random.normal(0, 1.0))
        FLP = max(100.0, 800.0 - 5.0 * u - 0.02 * u**2 + np.random.normal(0, 0.5))
        BHP = max(500.0, 3200.0 - 15.0 * u - 0.08 * u**2 + np.random.normal(0, 1.0))
        
        return max(0.0, Q), WHP, FLP, BHP, self.current_choke

class AutonomousChokeController:
    """
    Predictive Controller that evaluates candidate choke positions (+/- 5%)
    to hit Target Flow Rate Q while maintaining safety limits on WHP, FLP, BHP.
    """
    def __init__(self, min_whp=500.0, min_flp=200.0, min_bhp=1200.0):
        self.min_whp = min_whp
        self.min_flp = min_flp
        self.min_bhp = min_bhp
        
    def predict_next_choke(self, current_choke, target_Q, sim_function):
        # Candidate choke positions respecting the +/- 5% max ramp constraint
        candidates = np.linspace(current_choke - 5.0, current_choke + 5.0, 21)
        candidates = np.clip(candidates, 0.0, 100.0)
        
        best_choke = current_choke
        best_error = float('inf')
        
        for cand in candidates:
            # Predict outcome for this candidate
            Q_pred, whp_pred, flp_pred, bhp_pred, _ = sim_function(cand)
            
            # Check safety constraints
            if whp_pred >= self.min_whp and flp_pred >= self.min_flp and bhp_pred >= self.min_bhp:
                error = abs(Q_pred - target_Q)
                if error < best_error:
                    best_error = error
                    best_choke = cand
                    
        return best_choke

def run_scenario(scenario_name, target_profile, steps=50):
    sim = OilWellSimulator()
    controller = AutonomousChokeController()
    
    records = []
    current_u = sim.current_choke
    
    for t in range(steps):
        target_q = target_profile(t)
        
        # Controller decides next choke move
        next_u = controller.predict_next_choke(current_u, target_q, sim.step)
        
        # Step simulator
        q, whp, flp, bhp, actual_u = sim.step(next_u)
        current_u = actual_u
        
        records.append({
            'Hour': t,
            'Target_Q': target_q,
            'Actual_Q': q,
            'WHP': whp,
            'FLP': flp,
            'BHP': bhp,
            'Choke_Position': actual_u
        })
        
    df = pd.DataFrame(records)
    print(f"--- Completed {scenario_name} ---")
    return df

if __name__ == "__main__":
    # Scenario A: Startup to Target (120 bbl/hr)
    df_a = run_scenario("Scenario A: Startup", lambda t: 120.0)
    
    # Scenario B: Dynamic Target Tracking (80 -> 160 bbl/hr)
    df_b = run_scenario("Scenario B: Target Tracking", lambda t: 80.0 if t < 25 else 160.0)
    
    # Scenario C: Infeasible Target (Requesting 350 bbl/hr - Unsafe)
    df_c = run_scenario("Scenario C: Infeasible Target", lambda t: 350.0)
    
    # Save results to CSV for dashboard
    df_a.to_csv("scenario_a.csv", index=False)
    df_b.to_csv("scenario_b.csv", index=False)
    df_c.to_csv("scenario_c.csv", index=False)
    print("Scenarios saved to CSV files.")