
import streamlit as st
from datetime import date

st.set_page_config(
    page_title="Dad's Business Manager",
    page_icon="🚛",
    layout="centered"
)

VEHICLES = [
    "Lorry 1", "Lorry 2", "Lorry 3",
    "Hilux 1", "Hilux 2", "Car"
]

CATEGORIES = [
    "Fuel", "Repair", "Tyres", "Servicing",
    "Toll", "Worker Salary", "Bin Cost",
    "Office Expense", "Other"
]

if "trips" not in st.session_state:
    st.session_state.trips = []

if "expenses" not in st.session_state:
    st.session_state.expenses = []

if "notice" not in st.session_state:
    st.session_state.notice = ""

trips = st.session_state.trips
expenses = st.session_state.expenses

st.title("🚛 Dad's Business Manager")
st.caption("Waste Collection Business")

if st.session_state.notice:
    st.success(st.session_state.notice)
    st.session_state.notice = ""

page = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Add Trip",
        "View / Edit / Delete Trips",
        "Add Daily Expense",
        "View / Edit / Delete Expenses"
    ]
)

# DASHBOARD
if page == "Dashboard":
    st.subheader("Business Overview")

    charged = sum(
        t["count"] * t["charge"] for t in trips
    )
    received = sum(t["received"] for t in trips)
    total_expenses = sum(e["amount"] for e in expenses)

    a, b = st.columns(2)
    a.metric("Income Charged", f"RM {charged:.2f}")
    b.metric("Money Received", f"RM {received:.2f}")

    c, d = st.columns(2)
    c.metric("Outstanding Bills", f"RM {charged - received:.2f}")
    d.metric("Total Expenses", f"RM {total_expenses:.2f}")

    today = date.today().isoformat()
    month = date.today().strftime("%Y-%m")

    today_expenses = sum(
        e["amount"] for e in expenses if e["date"] == today
    )
    month_expenses = sum(
        e["amount"] for e in expenses
        if e["date"].startswith(month)
    )

    st.subheader("Expense Summary")
    a, b = st.columns(2)
    a.metric("Today's Expenses", f"RM {today_expenses:.2f}")
    b.metric("This Month", f"RM {month_expenses:.2f}")

    st.metric(
        "Money Received Minus Expenses",
        f"RM {received - total_expenses:.2f}"
    )

    st.caption(
        "This is a simple cash summary, not full accounting profit."
    )

    st.subheader("Business Sections")
    st.write("🚛 Vehicles — 3 lorries, 2 Hilux, 1 car")
    st.write("📋 Customer Collections")
    st.write("🗑️ Bin Management — planned")
    st.write("⛽ Fuel and Repairs")
    st.write("👷 Workers and Drivers — planned")
    st.write("💰 Monthly Salaries — record under expenses")
    st.write("📊 Monthly Expense Summary")

# ADD TRIP
elif page == "Add Trip":
    st.subheader("📋 Add Customer Trip")

    with st.form("add_trip_form"):
        trip_date = st.date_input("Trip Date", value=date.today())
        lorry = st.selectbox("Vehicle", VEHICLES[:3])
        registration = st.text_input("Registration Number")
        company = st.text_input("Customer / Company")
        count = st.number_input(
            "Number of Trips", min_value=1, step=1
        )
        charge = st.number_input(
            "Charge Per Trip (RM)", min_value=0.0, step=10.0
        )
        received = st.number_input(
            "Money Received (RM)", min_value=0.0, step=10.0
        )
        notes = st.text_input("Notes")
        submitted = st.form_submit_button("Save Trip")

    if submitted:
        new_trip = {
            "date": str(trip_date),
            "lorry": lorry,
            "registration": registration.strip(),
            "company": company.strip(),
            "count": int(count),
            "charge": float(charge),
            "received": float(received),
            "notes": notes.strip()
        }

        if not company.strip():
            st.error("Enter a customer or company name.")
        elif received > count * charge:
            st.error("Received cannot exceed the total charge.")
        elif any(old == new_trip for old in trips):
            st.warning(
                "This exact trip already exists. "
                "It was not saved again."
            )
        else:
            trips.append(new_trip)
            st.session_state.notice = "Trip saved successfully."
            st.rerun()

# VIEW, EDIT AND DELETE TRIPS
elif page == "View / Edit / Delete Trips":
    st.subheader("📝 Manage Trips")

    if not trips:
        st.info("No trips recorded yet.")
    else:
        selected = st.selectbox(
            "Choose a trip",
            range(len(trips)),
            format_func=lambda i: (
                f'{trips[i]["date"]} | {trips[i]["company"]} | '
                f'{trips[i]["lorry"]} | '
                f'RM {trips[i]["count"] * trips[i]["charge"]:.2f}'
            )
        )

        trip = trips[selected]

        with st.form("edit_trip_form"):
            trip_date = st.date_input(
                "Trip Date", value=date.fromisoformat(trip["date"])
            )
            lorry = st.selectbox(
                "Vehicle", VEHICLES[:3],
                index=VEHICLES[:3].index(trip["lorry"])
            )
            registration = st.text_input(
                "Registration Number", value=trip["registration"]
            )
            company = st.text_input(
                "Customer / Company", value=trip["company"]
            )
            count = st.number_input(
                "Number of Trips", min_value=1, step=1,
                value=int(trip["count"])
            )
            charge = st.number_input(
                "Charge Per Trip (RM)", min_value=0.0, step=10.0,
                value=float(trip["charge"])
            )
            received = st.number_input(
                "Money Received (RM)", min_value=0.0, step=10.0,
                value=float(trip["received"])
            )
            notes = st.text_input("Notes", value=trip["notes"])
            save_edit = st.form_submit_button("Save Changes")

        if save_edit:
            updated = {
                "date": str(trip_date),
                "lorry": lorry,
                "registration": registration.strip(),
                "company": company.strip(),
                "count": int(count),
                "charge": float(charge),
                "received": float(received),
                "notes": notes.strip()
            }

            if not company.strip():
                st.error("Enter a customer or company name.")
            elif received > count * charge:
                st.error("Received cannot exceed the total charge.")
            elif any(
                i != selected and old == updated
                for i, old in enumerate(trips)
            ):
                st.error("An identical trip already exists.")
            else:
                trips[selected] = updated
                st.session_state.notice = "Trip updated."
                st.rerun()

        st.divider()
        confirm = st.checkbox(
            "I confirm I want to delete this trip",
            key=f"delete_trip_{selected}"
        )
        if st.button("🗑️ Delete Selected Trip", disabled=not confirm):
            del trips[selected]
            st.session_state.notice = "Trip deleted."
            st.rerun()

# ADD DAILY EXPENSE
elif page == "Add Daily Expense":
    st.subheader("⛽ Add Daily Business Expense")

    with st.form("add_expense_form"):
        expense_date = st.date_input(
            "Expense Date", value=date.today()
        )
        category = st.selectbox("Expense Category", CATEGORIES)
        vehicle = st.selectbox("Related Vehicle", ["Not vehicle-related"] + VEHICLES)
        amount = st.number_input(
            "Amount Paid (RM)", min_value=0.01, step=10.0
        )
        payment = st.selectbox(
            "Payment Method",
            ["Cash", "Bank Transfer", "Card", "Other"]
        )
        description = st.text_input(
            "Description / Shop / Receipt Number"
        )
        expense_notes = st.text_input("Notes")
        submitted = st.form_submit_button("Save Expense")

    if submitted:
        new_expense = {
            "date": str(expense_date),
            "category": category,
            "vehicle": vehicle,
            "amount": float(amount),
            "payment": payment,
            "description": description.strip(),
            "notes": expense_notes.strip()
        }

        if any(old == new_expense for old in expenses):
            st.warning("This exact expense already exists.")
        else:
            expenses.append(new_expense)
            st.session_state.notice = "Expense saved successfully."
            st.rerun()

# VIEW, EDIT AND DELETE EXPENSES
elif page == "View / Edit / Delete Expenses":
    st.subheader("🧾 Manage Expenses")

    if not expenses:
        st.info("No expenses recorded yet.")
    else:
        selected = st.selectbox(
            "Choose an expense",
            range(len(expenses)),
            format_func=lambda i: (
                f'{expenses[i]["date"]} | '
                f'{expenses[i]["category"]} | '
                f'RM {expenses[i]["amount"]:.2f}'
            )
        )

        expense = expenses[selected]

        with st.form("edit_expense_form"):
            expense_date = st.date_input(
                "Expense Date",
                value=date.fromisoformat(expense["date"])
            )
            category = st.selectbox(
                "Expense Category", CATEGORIES,
                index=CATEGORIES.index(expense["category"])
            )
            vehicle = st.selectbox(
                "Related Vehicle",
                ["Not vehicle-related"] + VEHICLES,
                index=(["Not vehicle-related"] + VEHICLES).index(
                    expense["vehicle"]
                )
            )
            amount = st.number_input(
                "Amount Paid (RM)", min_value=0.01, step=10.0,
                value=float(expense["amount"])
            )
            payment = st.selectbox(
                "Payment Method",
                ["Cash", "Bank Transfer", "Card", "Other"],
                index=["Cash", "Bank Transfer", "Card", "Other"].index(
                    expense["payment"]
                )
            )
            description = st.text_input(
                "Description / Shop / Receipt Number",
                value=expense["description"]
            )
            expense_notes = st.text_input(
                "Notes", value=expense["notes"]
            )
            save_edit = st.form_submit_button("Save Changes")

        if save_edit:
            updated = {
                "date": str(expense_date),
                "category": category,
                "vehicle": vehicle,
                "amount": float(amount),
                "payment": payment,
                "description": description.strip(),
                "notes": expense_notes.strip()
            }

            if any(
                i != selected and old == updated
                for i, old in enumerate(expenses)
            ):
                st.error("An identical expense already exists.")
            else:
                expenses[selected] = updated
                st.session_state.notice = "Expense updated."
                st.rerun()

        st.divider()
        confirm = st.checkbox(
            "I confirm I want to delete this expense",
            key=f"delete_expense_{selected}"
        )
        if st.button("🗑️ Delete Selected Expense", disabled=not confirm):
            del expenses[selected]
            st.session_state.notice = "Expense deleted."
            st.rerun()

st.divider()
st.caption(
    "TEST VERSION: Records use temporary session memory. "
    "They may disappear when the app restarts and are not shared "
    "permanently between users. Add a secure database before real use."
)
