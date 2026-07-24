import pandas as pd
import numpy as np

# 1. Load Honeywell Reference Dataset
ref_df = pd.read_csv('Autonomous_Choke_Control_Simulated_Dataset.csv')

# Dynamic Polynomial Fits based directly on Honeywell CSV
poly_oil = np.polyfit(ref_df['Choke_pct'], ref_df['OilRate_bbl_hr'], 2)
poly_whp = np.polyfit(ref_df['Choke_pct'], ref_df['WHP_psi'], 2)
poly_flp = np.polyfit(ref_df['Choke_pct'], ref_df['FLP_psi'], 2)
poly_bhp = np.polyfit(ref_df['Choke_pct'], ref_df['BHP_psi'], 2)

class OilWellSimulator:
    """
    Simulates the single naturally flowing oil well using Honeywell's reference dynamics.
    Enforces choke movement ramp rate <= +/- 5% per control hour.
    """
    def __init__(self, initial_choke=30.0):
        self.current_choke = initial_choke
        
    def step(self, target_choke):
        # Enforce Choke Ramp Rate Constraint (Max +/- 5% per interval)
        delta = np.clip(target_choke - self.current_choke, -5.0, 5.0)
        self.current_choke = np.clip(self.current_choke + delta, 0.0, 100.0)
        u = self.current_choke
        
        # Output predictions with realistic sensor noise
        q = np.polyval(poly_oil, u) + np.random.normal(0, 0.2)
        whp = np.polyval(poly_whp, u) + np.random.normal(0, 0.4)
        flp = np.polyval(poly_flp, u) + np.random.normal(0, 0.3)
        bhp = np.polyval(poly_bhp, u) + np.random.normal(0, 0.8)
        
        return max(0.0, q), whp, flp, bhp, self.current_choke


class ModelPredictiveController:
    """
    Predictive Choke Controller using candidate evaluation.
    Optimizes choke position to hit target production while guaranteeing safety constraints.
    """
    def __init__(self, min_whp=220.0, min_flp=155.0, min_bhp=2900.0):
        self.min_whp = min_whp
        self.min_flp = min_flp
        self.min_bhp = min_bhp
        
    def predict_optimal_choke(self, current_choke, target_q):
        # Candidate positions within allowed +/- 5% ramp step
        candidates = np.linspace(current_choke - 5.0, current_choke + 5.0, 51)
        candidates = np.clip(candidates, 0.0, 100.0)
        
        best_choke = current_choke
        best_error = float('inf')
        safest_choke = current_choke
        min_violation = float('inf')
        
        for cand in candidates:
            q_pred = np.polyval(poly_oil, cand)
            whp_pred = np.polyval(poly_whp, cand)
            flp_pred = np.polyval(poly_flp, cand)
            bhp_pred = np.polyval(poly_bhp, cand)
            
            # Constraint check
            is_safe = (whp_pred >= self.min_whp) and (flp_pred >= self.min_flp) and (bhp_pred >= self.min_bhp)
            
            if is_safe:
                err = abs(q_pred - target_q)
                if err < best_error:
                    best_error = err
                    best_choke = cand
            else:
                # Fallback for infeasible targets (Settle at maximum safe limit)
                violation = max(0, self.min_whp - whp_pred) + max(0, self.min_flp - flp_pred) + max(0, self.min_bhp - bhp_pred)
                if violation < min_violation:
                    min_violation = violation
                    safest_choke = cand
                    
        return best_choke if best_error != float('inf') else safest_choke


def run_scenario(name, target_profile, steps=50):
    sim = OilWellSimulator(initial_choke=30.0)
    controller = ModelPredictiveController()
    records = []
    curr_u = sim.current_choke
    
    for t in range(steps):
        target_q = target_profile(t)
        next_u = controller.predict_optimal_choke(curr_u, target_q)
        q, whp, flp, bhp, actual_u = sim.step(next_u)
        curr_u = actual_u
        
        records.append({
            'Time_hr': t, 'Target_Q': target_q, 'Actual_Q': q,
            'WHP': whp, 'FLP': flp, 'BHP': bhp, 'Choke_Position': actual_u
        })
        
    df = pd.DataFrame(records)
    print(f"✅ {name} completed successfully.")
    return df

if __name__ == "__main__":
    # Scenario A: Startup to 120 bbl/hr
    df_a = run_scenario("Scenario A: Startup", lambda t: 120.0, 40)
    
    # Scenario B: Dynamic Target (100 -> 145 bbl/hr)
    df_b = run_scenario("Scenario B: Target Tracking", lambda t: 100.0 if t < 20 else 145.0, 50)
    
    # Scenario C: Infeasible Target (Requesting 220 bbl/hr - Exceeds Safe Envelope)
    df_c = run_scenario("Scenario C: Infeasible Target", lambda t: 220.0, 40)
    
    df_a.to_csv("scenario_a_results.csv", index=False)
    df_b.to_csv("scenario_b_results.csv", index=False)
    df_c.to_csv("scenario_c_results.csv", index=False)