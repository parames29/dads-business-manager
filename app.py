
import streamlit as st
import pandas as pd
from datetime import date
from decimal import Decimal
from supabase import create_client

st.set_page_config(
    page_title="Dad's Business Manager",
    page_icon="🚛",
    layout="centered"
)

# Configure these in Streamlit Cloud -> App settings -> Secrets.
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
db = create_client(url, key)

VEHICLES = [
    "PPF4995",
    "PPD7995",
    "PJX3100",
    "PLT7995",
    "AKU 995",
    "Car - plate to add"
]

CATEGORIES = [
    "Fuel", "Repair", "Tyres", "Servicing", "Toll",
    "Worker Salary", "Bin Cost", "Office Expense", "Other"
]

def money(value):
    return f"RM {float(value or 0):,.2f}"

def load_trips():
    return db.table("trips").select("*").order(
        "trip_date", desc=True
    ).execute().data or []

def load_expenses():
    return db.table("expenses").select("*").order(
        "expense_date", desc=True
    ).execute().data or []

def show_trips(rows):
    if not rows:
        st.info("No trip records yet.")
        return
    data = []
    for t in rows:
        charge = int(t["trip_count"]) * float(t["charge_per_trip"])
        received = float(t["received"])
        data.append({
            "Date": t["trip_date"],
            "Vehicle": t["vehicle"],
            "Company": t["company"],
            "Trips": t["trip_count"],
            "Rate": money(t["charge_per_trip"]),
            "Total charged": money(charge),
            "Received": money(received),
            "Outstanding": money(charge - received)
        })
    st.dataframe(data, use_container_width=True)

def show_expenses(rows):
    if not rows:
        st.info("No expense records yet.")
        return
    data = [{
        "Date": e["expense_date"],
        "Category": e["category"],
        "Vehicle": e["vehicle"],
        "Amount": money(e["amount"]),
        "Description": e["description"],
        "Payment": e["payment_method"]
    } for e in rows]
    st.dataframe(data, use_container_width=True)

st.title("🚛 Dad's Business Manager")

menu = st.sidebar.radio("Menu", [
    "Dashboard",
    "Add Trip",
    "View / Edit / Delete Trips",
    "Add Expense",
    "View / Edit / Delete Expenses",
    "Vehicle Statement"
])

try:
    trips = load_trips()
    expenses = load_expenses()
except Exception as error:
    st.error("Could not connect to the database.")
    st.caption(str(error))
    st.stop()

if menu == "Dashboard":
    charged = sum(
        int(t["trip_count"]) * float(t["charge_per_trip"])
        for t in trips
    )
    received = sum(float(t["received"]) for t in trips)
    outstanding = charged - received
    spent = sum(float(e["amount"]) for e in expenses)
    today_spent = sum(
        float(e["amount"]) for e in expenses
        if str(e["expense_date"]) == str(date.today())
    )

    a, b = st.columns(2)
    a.metric("Income Charged", money(charged))
    b.metric("Money Received", money(received))
    a.metric("Outstanding Bills", money(outstanding))
    b.metric("Total Expenses", money(spent))
    st.metric("Today's Expenses", money(today_spent))
    st.metric("Received minus Expenses", money(received - spent))

    st.subheader("Recent Trips")
    show_trips(trips[:10])

elif menu == "Add Trip":
    st.subheader("Add Trip")
    with st.form("add_trip"):
        trip_date = st.date_input("Trip date", value=date.today())
        vehicle = st.selectbox("Lorry registration", VEHICLES[:3])
        company = st.text_input("Company / Customer")
        count = st.number_input("Number of trips", 1, 100, 1)
        rate = st.number_input("Charge per trip (RM)", 0.0, step=10.0)
        total = count * rate
        st.write("**Total charge:**", money(total))
        received = st.number_input(
            "Money received (RM)", 0.0, value=0.0, step=10.0
        )
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Trip")

    if submitted:
        if not company.strip():
            st.error("Enter the company or customer name.")
        elif received > total:
            st.error("Received amount cannot exceed total charge.")
        else:
            db.table("trips").insert({
                "trip_date": str(trip_date),
                "vehicle": vehicle,
                "company": company.strip(),
                "trip_count": int(count),
                "charge_per_trip": float(rate),
                "received": float(received),
                "notes": notes.strip()
            }).execute()
            st.success("Trip saved to the database.")
            st.rerun()

elif menu == "View / Edit / Delete Trips":
    show_trips(trips)
    if trips:
        options = {
            f'ID {t["id"]} | {t["trip_date"]} | {t["vehicle"]} | {t["company"]}': t
            for t in trips
        }
        selected_label = st.selectbox("Select a trip", list(options))
        t = options[selected_label]

        with st.form("edit_trip"):
            trip_date = st.date_input(
                "Date", value=date.fromisoformat(str(t["trip_date"]))
            )
            vehicle = st.selectbox(
                "Vehicle", VEHICLES,
                index=VEHICLES.index(t["vehicle"])
                if t["vehicle"] in VEHICLES else 0
            )
            company = st.text_input("Company", value=t["company"])
            count = st.number_input(
                "Number of trips", 1, 100, int(t["trip_count"])
            )
            rate = st.number_input(
                "Rate per trip (RM)", min_value=0.0,
                value=float(t["charge_per_trip"]), step=10.0
            )
            received = st.number_input(
                "Received (RM)", min_value=0.0,
                value=float(t["received"]), step=10.0
            )
            notes = st.text_area("Notes", value=t.get("notes") or "")
            save = st.form_submit_button("Save Changes")

        if save:
            if not company.strip():
                st.error("Company name is required.")
            elif received > count * rate:
                st.error("Received amount cannot exceed total charge.")
            else:
                db.table("trips").update({
                    "trip_date": str(trip_date),
                    "vehicle": vehicle,
                    "company": company.strip(),
                    "trip_count": int(count),
                    "charge_per_trip": float(rate),
                    "received": float(received),
                    "notes": notes.strip()
                }).eq("id", t["id"]).execute()
                st.success("Trip updated.")
                st.rerun()

        if st.checkbox("Confirm I want to delete this trip"):
            if st.button("Delete Selected Trip"):
                db.table("trips").delete().eq("id", t["id"]).execute()
                st.success("Trip deleted.")
                st.rerun()

elif menu == "Add Expense":
    st.subheader("Add Daily Expense")
    with st.form("add_expense"):
        expense_date = st.date_input("Expense date", value=date.today())
        category = st.selectbox("Category", CATEGORIES)
        vehicle = st.selectbox("Vehicle", VEHICLES)
        amount = st.number_input("Amount (RM)", min_value=0.01, step=10.0)
        payment = st.selectbox(
            "Payment method", ["Cash", "Bank Transfer", "Card", "Other"]
        )
        description = st.text_input("Description")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Save Expense")

    if submitted:
        if not description.strip():
            st.error("Enter a description.")
        else:
            db.table("expenses").insert({
                "expense_date": str(expense_date),
                "category": category,
                "vehicle": vehicle,
                "amount": float(amount),
                "payment_method": payment,
                "description": description.strip(),
                "notes": notes.strip()
            }).execute()
            st.success("Expense saved to the database.")
            st.rerun()

elif menu == "View / Edit / Delete Expenses":
    show_expenses(expenses)
    if expenses:
        options = {
            f'ID {e["id"]} | {e["expense_date"]} | {e["description"]}': e
            for e in expenses
        }
        label = st.selectbox("Select an expense", list(options))
        e = options[label]

        with st.form("edit_expense"):
            expense_date = st.date_input(
                "Date", value=date.fromisoformat(str(e["expense_date"]))
            )
            category = st.selectbox(
                "Category", CATEGORIES,
                index=CATEGORIES.index(e["category"])
            )
            vehicle = st.selectbox(
                "Vehicle", VEHICLES,
                index=VEHICLES.index(e["vehicle"])
                if e["vehicle"] in VEHICLES else 0
            )
            amount = st.number_input(
                "Amount (RM)", min_value=0.01,
                value=float(e["amount"]), step=10.0
            )
            payment = st.selectbox(
                "Payment method",
                ["Cash", "Bank Transfer", "Card", "Other"],
                index=["Cash", "Bank Transfer", "Card", "Other"].index(
                    e["payment_method"]
                ) if e["payment_method"] in
                ["Cash", "Bank Transfer", "Card", "Other"] else 0
            )
            description = st.text_input(
                "Description", value=e["description"]
            )
            notes = st.text_area("Notes", value=e.get("notes") or "")
            save = st.form_submit_button("Save Changes")

        if save:
            if not description.strip():
                st.error("Description is required.")
            else:
                db.table("expenses").update({
                    "expense_date": str(expense_date),
                    "category": category,
                    "vehicle": vehicle,
                    "amount": float(amount),
                    "payment_method": payment,
                    "description": description.strip(),
                    "notes": notes.strip()
                }).eq("id", e["id"]).execute()
                st.success("Expense updated.")
                st.rerun()

        if st.checkbox("Confirm I want to delete this expense"):
            if st.button("Delete Selected Expense"):
                db.table("expenses").delete().eq("id", e["id"]).execute()
                st.success("Expense deleted.")
                st.rerun()

elif menu == "Vehicle Statement":
    vehicle = st.selectbox("Choose vehicle", VEHICLES)
    st.subheader(f"Statement: {vehicle}")

    vehicle_trips = [t for t in trips if t["vehicle"] == vehicle]
    vehicle_expenses = [e for e in expenses if e["vehicle"] == vehicle]

    total_trips = sum(int(t["trip_count"]) for t in vehicle_trips)
    total_charged = sum(
        int(t["trip_count"]) * float(t["charge_per_trip"])
        for t in vehicle_trips
    )
    total_received = sum(float(t["received"]) for t in vehicle_trips)
    total_vehicle_expenses = sum(
        float(e["amount"]) for e in vehicle_expenses
    )

    st.metric("Total Trips", total_trips)
    st.metric("Income Charged", money(total_charged))
    st.metric("Money Received", money(total_received))
    st.metric("Outstanding", money(total_charged - total_received))
    st.metric("Vehicle Expenses", money(total_vehicle_expenses))

    st.subheader("Trip Details")
    show_trips(vehicle_trips)
    st.subheader("Expense Details")
    show_expenses(vehicle_expenses)

st.caption(
    "Use a secured, authenticated database setup before entering real "
    "business records. Configure backups before relying on this app."
)
