import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Honeywell | Autonomous Choke Controller", layout="wide")

st.title("⛽ Autonomous Production Choke Controller for Safe Oil Well Optimization")
st.caption("Honeywell Campus Connect Hackathon — Round 2 Solution")

scenario = st.sidebar.selectbox("Select Demonstration Scenario", [
    "Scenario A: Startup to Target (120 bbl/hr)",
    "Scenario B: Dynamic Target Tracking (100 -> 145 bbl/hr)",
    "Scenario C: Infeasible Target (Safety Limited)"
])

filename = "scenario_a_results.csv" if "A" in scenario else ("scenario_b_results.csv" if "B" in scenario else "scenario_c_results.csv")
df = pd.read_csv(filename)

# Metric Summary
c1, c2, c3, c4 = st.columns(4)
c1.metric("Final Production Rate", f"{df['Actual_Q'].iloc[-1]:.1f} bbl/hr")
c2.metric("Target Production Rate", f"{df['Target_Q'].iloc[-1]:.1f} bbl/hr")
c3.metric("Min Wellhead Pressure", f"{df['WHP'].min():.1f} psi", delta="Safeguarded")
c4.metric("Final Choke Opening", f"{df['Choke_Position'].iloc[-1]:.1f}%")

st.markdown("---")

# Chart 1: Production Rate Tracking
st.subheader("1. Oil Flow Rate (Q) Target Tracking")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=df['Time_hr'], y=df['Target_Q'], name='Target Flow Rate', line=dict(dash='dash', color='orange')))
fig1.add_trace(go.Scatter(x=df['Time_hr'], y=df['Actual_Q'], name='Actual Production Rate', line=dict(color='green')))
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Operating Pressure Constraints
st.subheader("2. Pressure Envelope Limits (WHP, FLP, BHP)")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df['Time_hr'], y=df['BHP'], name='BHP (psi)'))
fig2.add_trace(go.Scatter(x=df['Time_hr'], y=df['WHP'], name='WHP (psi)'))
fig2.add_trace(go.Scatter(x=df['Time_hr'], y=df['FLP'], name='FLP (psi)'))
fig2.add_hline(y=220, line_dash="dot", line_color="red", annotation_text="Min WHP Limit (220 psi)")
st.plotly_chart(fig2, use_container_width=True)