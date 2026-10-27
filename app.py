
import streamlit as st

st.set_page_config(
    page_title="Dad's Business Manager",
    page_icon="🚛",
    layout="centered"
)

st.title("🚛 Dad's Business Manager")
st.caption("Waste Collection Business")

st.divider()

st.subheader("Business Overview")

col1, col2 = st.columns(2)

with col1:
    st.metric("Income Charged", "RM 0.00")
    st.metric("Business Expenses", "RM 0.00")

with col2:
    st.metric("Money Received", "RM 0.00")
    st.metric("Outstanding Bills", "RM 0.00")

st.divider()

st.subheader("Business Sections")

st.write("🚛 Vehicles — 3 lorries, 2 Hilux, 1 car")
st.write("📋 Customer Collections")
st.write("🗑️ Bin Management")
st.write("⛽ Fuel and Repairs")
st.write("👷 Workers and Drivers")
st.write("💰 Monthly Salaries")
st.write("📊 Monthly Reports")

st.info(
    "First version: dashboard layout only. "
    "Shared database and secure login will be added next."
)
