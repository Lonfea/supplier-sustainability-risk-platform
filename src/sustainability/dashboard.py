import streamlit as st

from sustainability.engine import demo_engine

st.set_page_config(page_title="Supplier Sustainability", layout="wide")
engine = demo_engine()
queue = engine.action_queue()
st.title("Supplier Sustainability Risk Platform")
st.caption("Synthetic data | explainable prioritization | human review required")
c1, c2, c3 = st.columns(3)
c1.metric("Suppliers", len(queue))
c2.metric("Critical / high", sum(row["priority_band"] in {"critical", "high"} for row in queue))
c3.metric("Estimated footprint", f"{engine.scenario(0)['baseline_kgco2e']:,.0f} kgCO2e")
st.subheader("Prioritized remediation queue")
st.dataframe(queue, use_container_width=True)
uplift = st.slider("Renewable electricity uplift", 0, 100, 25) / 100
st.subheader("Scenario")
st.json(engine.scenario(uplift))

