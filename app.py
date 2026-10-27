
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Dad's Business Manager",
    page_icon="🚛",
    layout="centered"
)

if "trips" not in st.session_state:
    st.session_state.trips = []

st.title("🚛 Dad's Business Manager")
st.caption("Waste Collection Business")

page = st.sidebar.selectbox(
    "Menu",
    ["Dashboard", "Add Trip", "View / Edit Trips"]
)

if page == "Dashboard":
    st.subheader("Business Overview")

    total_charged = sum(
        t["trips"] * t["charge"] for t in st.session_state.trips
    )
    total_received = sum(
        t["received"] for t in st.session_state.trips
    )

    col1, col2 = st.columns(2)
    col1.metric("Income Charged", f"RM {total_charged:.2f}")
    col2.metric("Money Received", f"RM {total_received:.2f}")

    col3, col4 = st.columns(2)
    col3.metric(
        "Outstanding Bills",
        f"RM {total_charged - total_received:.2f}"
    )
    col4.metric("Business Expenses", "RM 0.00")

    st.subheader("Business Sections")
    st.write("🚛 Vehicles — 3 lorries, 2 Hilux, 1 car")
    st.write("📋 Customer Collections")
    st.write("🗑️ Bin Management")
    st.write("⛽ Fuel and Repairs")
    st.write("👷 Workers and Drivers")
    st.write("💰 Monthly Salaries")
    st.write("📊 Monthly Reports")

elif page == "Add Trip":
    st.subheader("📋 Add Customer Trip")

    with st.form("trip_form"):
        trip_date = st.date_input("Date", value=date.today())
        lorry = st.selectbox(
            "Lorry",
            ["Lorry 1", "Lorry 2", "Lorry 3"]
        )
        registration = st.text_input("Vehicle Registration")
        company = st.text_input("Customer / Company")
        trip_count = st.number_input(
            "Number of Trips", min_value=1, step=1
        )
        charge = st.number_input(
            "Charge per Trip (RM)", min_value=0.0, step=10.0
        )
        received = st.number_input(
            "Money Received (RM)", min_value=0.0, step=10.0
        )
        notes = st.text_input("Notes")

        submitted = st.form_submit_button("Save Trip")

        if submitted:
            if not company.strip():
                st.error("Please enter a customer or company name.")
            elif received > trip_count * charge:
                st.error("Received amount cannot exceed the trip charge.")
            else:
                st.session_state.trips.append({
                    "date": str(trip_date),
                    "lorry": lorry,
                    "registration": registration,
                    "company": company,
                    "trips": trip_count,
                    "charge": charge,
                    "received": received,
                    "notes": notes
                })
                st.success("Trip added for this demo session.")

elif page == "View / Edit Trips":
    st.subheader("📝 View / Edit Trips")

    if not st.session_state.trips:
        st.info("No trips recorded yet. Open Add Trip to enter one.")
    else:
        selected = st.selectbox(
            "Choose a trip",
            range(len(st.session_state.trips)),
            format_func=lambda i: (
                f'{st.session_state.trips[i]["date"]} — '
                f'{st.session_state.trips[i]["company"]}'
            )
        )

        trip = st.session_state.trips[selected]

        with st.form("edit_trip_form"):
            trip_date = st.date_input(
                "Date", value=date.fromisoformat(trip["date"])
            )
            lorry = st.selectbox(
                "Lorry",
                ["Lorry 1", "Lorry 2", "Lorry 3"],
                index=["Lorry 1", "Lorry 2", "Lorry 3"].index(trip["lorry"])
            )
            registration = st.text_input(
                "Vehicle Registration", value=trip["registration"]
            )
            company = st.text_input(
                "Customer / Company", value=trip["company"]
            )
            trip_count = st.number_input(
                "Number of Trips", min_value=1, step=1,
                value=int(trip["trips"])
            )
            charge = st.number_input(
                "Charge per Trip (RM)", min_value=0.0, step=10.0,
                value=float(trip["charge"])
            )
            received = st.number_input(
                "Money Received (RM)", min_value=0.0, step=10.0,
                value=float(trip["received"])
            )
            notes = st.text_input("Notes", value=trip["notes"])

            saved = st.form_submit_button("Save Changes")

            if saved:
                if not company.strip():
                    st.error("Please enter a customer or company name.")
                elif received > trip_count * charge:
                    st.error("Received amount cannot exceed the trip charge.")
                else:
                    st.session_state.trips[selected] = {
                        "date": str(trip_date),
                        "lorry": lorry,
                        "registration": registration,
                        "company": company,
                        "trips": trip_count,
                        "charge": charge,
                        "received": received,
                        "notes": notes
                    }
                    st.success("Trip updated for this demo session.")
