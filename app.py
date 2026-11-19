
import streamlit as st
from datetime import date
from supabase import create_client

# ==================================================
# PAGE SETTINGS
# ==================================================

st.set_page_config(
    page_title="THEAVA MAJU",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================================================
# LOGIN
# ==================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🚛 THEAVA MAJU")
    st.caption("FLEET MANAGEMENT SYSTEM")

    with st.form("login_form"):
        password = st.text_input("App Password", type="password")
        submitted = st.form_submit_button("Unlock")

    if submitted:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()

# ==================================================
# DATABASE
# ==================================================

db = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)


def load_vehicles():
    return db.table("vehicles").select("*").order("id").execute().data or []


def load_trips():
    return db.table("trips").select("*").order(
        "trip_date", desc=True
    ).execute().data or []


def load_expenses():
    return db.table("expenses").select("*").order(
        "expense_date", desc=True
    ).execute().data or []


def money(value):
    return f"RM {float(value or 0):,.2f}"


# ==================================================
# CATEGORIES
# ==================================================

VEHICLE_CATEGORIES = [
    "Fuel",
    "Repair",
    "Tyres",
    "Servicing",
    "Toll",
    "Road Tax",
    "Insurance",
    "Other Vehicle Expense"
]

BUSINESS_CATEGORIES = [
    "Worker Salary",
    "Bin Cost",
    "Office Expense",
    "Utilities",
    "Other Business Expense"
]

PAYMENT_METHODS = [
    "Cash",
    "Bank Transfer",
    "Card",
    "Other"
]


# ==================================================
# DATE HELPERS
# ==================================================

def month_range(year, month):
    start = date(year, month, 1)

    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    return start, end


def in_month(value, start, end):
    try:
        record_date = date.fromisoformat(str(value)[:10])
        return start <= record_date < end
    except (ValueError, TypeError):
        return False


# ==================================================
# DISPLAY HELPERS
# ==================================================

def show_trips(rows):
    if not rows:
        st.info("No trips recorded.")
        return

    data = []

    for t in rows:
        total = int(t["trip_count"]) * float(t["charge_per_trip"])
        received = float(t["received"])

        data.append({
            "Date": t["trip_date"],
            "Vehicle": t["vehicle"],
            "Company": t["company"],
            "Trips": t["trip_count"],
            "Charged": money(total),
            "Received": money(received),
            "Outstanding": money(total - received)
        })

    st.dataframe(data, use_container_width=True, hide_index=True)


def show_expenses(rows):
    if not rows:
        st.info("No expenses recorded.")
        return

    data = []

    for e in rows:
        data.append({
            "Date": e["expense_date"],
            "Type": (
                "Other Business"
                if e["vehicle"] == "General Business"
                else "Vehicle"
            ),
            "Category": e["category"],
            "Vehicle": e["vehicle"],
            "Description": e["description"],
            "Amount": money(e["amount"])
        })

    st.dataframe(data, use_container_width=True, hide_index=True)


# ==================================================
# ADD TRIP
# ==================================================

def add_trip_form(vehicles, form_key="add_trip"):
    lorries = [
        v["registration"]
        for v in vehicles
        if v["vehicle_type"] == "Lorry" and v["is_active"]
    ]

    if not lorries:
        st.warning("No active lorries. Please add a lorry first.")
        return

    with st.form(form_key):
        trip_date = st.date_input("Trip Date", value=date.today())

        vehicle = st.selectbox("Lorry", lorries)

        company = st.text_input("Company / Customer")

        count = st.number_input(
            "Number of Trips",
            min_value=1,
            max_value=100,
            value=1
        )

        rate = st.number_input(
            "Charge Per Trip (RM)",
            min_value=0.0,
            step=10.0
        )

        total = count * rate
        st.write("**Total Charged:**", money(total))

        received = st.number_input(
            "Money Received (RM)",
            min_value=0.0,
            step=10.0
        )

        notes = st.text_area("Notes")

        submitted = st.form_submit_button(
            "Save Trip",
            use_container_width=True
        )

    if submitted:
        if not company.strip():
            st.error("Please enter a company or customer.")
        elif received > total:
            st.error("Received cannot exceed total charged.")
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

            st.success("Trip saved.")
            st.rerun()


# ==================================================
# SMART TRIP EDIT AND DELETE
# ==================================================

def manage_trips(trips, vehicles, selected_vehicle=None):
    rows = [
        t for t in trips
        if selected_vehicle is None
        or t["vehicle"] == selected_vehicle
    ]

    st.markdown("### Recent Trips")

    if not rows:
        st.info("No trips to manage yet.")
        return

    vehicle_options = [
        v["registration"] for v in vehicles if v["is_active"]
    ]

    for t in rows[:30]:
        total = int(t["trip_count"]) * float(t["charge_per_trip"])

        heading = (
            f'{t["trip_date"]}  |  {t["vehicle"]}  |  '
            f'{t["company"]}  |  {money(total)}'
        )

        with st.expander(heading):
            st.caption(
                f'Received: {money(t["received"])} · '
                f'Outstanding: {money(total - float(t["received"]))}'
            )

            options = list(vehicle_options)

            if t["vehicle"] not in options:
                options.append(t["vehicle"])

            with st.form(f'edit_trip_{t["id"]}'):
                trip_date = st.date_input(
                    "Trip Date",
                    value=date.fromisoformat(str(t["trip_date"])),
                    key=f'trip_date_{t["id"]}'
                )

                vehicle = st.selectbox(
                    "Vehicle",
                    options,
                    index=options.index(t["vehicle"]),
                    key=f'trip_vehicle_{t["id"]}'
                )

                company = st.text_input(
                    "Company / Customer",
                    value=t["company"],
                    key=f'trip_company_{t["id"]}'
                )

                count = st.number_input(
                    "Number of Trips",
                    min_value=1,
                    max_value=100,
                    value=int(t["trip_count"]),
                    key=f'trip_count_{t["id"]}'
                )

                rate = st.number_input(
                    "Charge Per Trip (RM)",
                    min_value=0.0,
                    value=float(t["charge_per_trip"]),
                    key=f'trip_rate_{t["id"]}'
                )

                received = st.number_input(
                    "Money Received (RM)",
                    min_value=0.0,
                    value=float(t["received"]),
                    key=f'trip_received_{t["id"]}'
                )

                notes = st.text_area(
                    "Notes",
                    value=t.get("notes") or "",
                    key=f'trip_notes_{t["id"]}'
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

            if save:
                if not company.strip():
                    st.error("Company name is required.")
                elif received > count * rate:
                    st.error("Received cannot exceed total charged.")
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

            st.divider()

            confirm = st.checkbox(
                "I confirm I want to delete this trip",
                key=f'delete_trip_confirm_{t["id"]}'
            )

            if st.button(
                "Delete Trip",
                key=f'delete_trip_{t["id"]}',
                disabled=not confirm,
                use_container_width=True
            ):
                db.table("trips").delete().eq(
                    "id", t["id"]
                ).execute()

                st.success("Trip deleted.")
                st.rerun()


# ==================================================
# ADD EXPENSE
# ==================================================

def add_expense_form(vehicles, form_key="add_expense"):
    active_vehicles = [
        v["registration"] for v in vehicles if v["is_active"]
    ]

    with st.form(form_key):
        expense_date = st.date_input(
            "Expense Date",
            value=date.today()
        )

        expense_type = st.radio(
            "Expense Type",
            ["Vehicle Expense", "Other Business Expense"]
        )

        if expense_type == "Vehicle Expense":
            if not active_vehicles:
                st.warning("Add a vehicle before recording vehicle expenses.")
                vehicle = "General Business"
            else:
                vehicle = st.selectbox(
                    "Choose Vehicle",
                    active_vehicles
                )

            category = st.selectbox(
                "Expense Category",
                VEHICLE_CATEGORIES
            )

        else:
            vehicle = "General Business"

            category = st.selectbox(
                "Business Expense Category",
                BUSINESS_CATEGORIES
            )

        amount = st.number_input(
            "Amount (RM)",
            min_value=0.01,
            step=10.0
        )

        payment = st.selectbox(
            "Payment Method",
            PAYMENT_METHODS
        )

        description = st.text_input("Description")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button(
            "Save Expense",
            use_container_width=True
        )

    if submitted:
        if expense_type == "Vehicle Expense" and not active_vehicles:
            st.error("Please add a vehicle first.")
        elif not description.strip():
            st.error("Please enter a description.")
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

            st.success("Expense saved.")
            st.rerun()


# ==================================================
# SMART EXPENSE EDIT AND DELETE
# ==================================================

def manage_expenses(expenses, vehicles):
    st.markdown("### Recent Expenses")

    if not expenses:
        st.info("No expenses to manage yet.")
        return

    active_vehicles = [
        v["registration"] for v in vehicles if v["is_active"]
    ]

    for e in expenses[:30]:
        heading = (
            f'{e["expense_date"]}  |  {e["category"]}  |  '
            f'{money(e["amount"])}'
        )

        with st.expander(heading):
            st.caption(
                f'{e["description"]} · {e["vehicle"]}'
            )

            vehicle_options = ["General Business"] + active_vehicles

            if e["vehicle"] not in vehicle_options:
                vehicle_options.append(e["vehicle"])

            old_category = e["category"]

            if e["vehicle"] == "General Business":
                category_options = BUSINESS_CATEGORIES.copy()
            else:
                category_options = VEHICLE_CATEGORIES.copy()

            if old_category not in category_options:
                category_options.append(old_category)

            old_payment = e["payment_method"]

            with st.form(f'edit_expense_{e["id"]}'):
                expense_date = st.date_input(
                    "Expense Date",
                    value=date.fromisoformat(str(e["expense_date"])),
                    key=f'exp_date_{e["id"]}'
                )

                vehicle = st.selectbox(
                    "Expense For",
                    vehicle_options,
                    index=vehicle_options.index(e["vehicle"]),
                    key=f'exp_vehicle_{e["id"]}'
                )

                if vehicle == "General Business":
                    new_categories = BUSINESS_CATEGORIES.copy()
                else:
                    new_categories = VEHICLE_CATEGORIES.copy()

                if old_category not in new_categories:
                    new_categories.append(old_category)

                category = st.selectbox(
                    "Category",
                    new_categories,
                    index=new_categories.index(old_category),
                    key=f'exp_category_{e["id"]}'
                )

                amount = st.number_input(
                    "Amount (RM)",
                    min_value=0.01,
                    value=float(e["amount"]),
                    key=f'exp_amount_{e["id"]}'
                )

                payment = st.selectbox(
                    "Payment Method",
                    PAYMENT_METHODS,
                    index=(
                        PAYMENT_METHODS.index(old_payment)
                        if old_payment in PAYMENT_METHODS else 0
                    ),
                    key=f'exp_payment_{e["id"]}'
                )

                description = st.text_input(
                    "Description",
                    value=e["description"],
                    key=f'exp_description_{e["id"]}'
                )

                notes = st.text_area(
                    "Notes",
                    value=e.get("notes") or "",
                    key=f'exp_notes_{e["id"]}'
                )

                save = st.form_submit_button(
                    "Save Changes",
                    use_container_width=True
                )

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

            st.divider()

            confirm = st.checkbox(
                "I confirm I want to delete this expense",
                key=f'delete_expense_confirm_{e["id"]}'
            )

            if st.button(
                "Delete Expense",
                key=f'delete_expense_{e["id"]}',
                disabled=not confirm,
                use_container_width=True
            ):
                db.table("expenses").delete().eq(
                    "id", e["id"]
                ).execute()

                st.success("Expense deleted.")
                st.rerun()


# ==================================================
# DESIGN
# ==================================================

st.markdown("""
<style>
.stApp {
    background: #0b0b0d;
    color: #f5f5f5;
}
.block-container {
    padding-top: 1.5rem;
    max-width: 1100px;
}
section[data-testid="stSidebar"] {
    background: #151518;
}
div.stButton > button {
    border-radius: 10px;
    min-height: 43px;
    border: 1px solid #33333a;
    background: #19191e;
    color: white;
}
div.stButton > button:hover {
    border-color: #a1a1aa;
    color: white;
}
.vehicle-card {
    background: #17171b;
    border: 1px solid #303036;
    border-radius: 14px;
    padding: 17px;
    margin-bottom: 5px;
}
.vehicle-number {
    font-size: 21px;
    font-weight: 700;
    color: white;
}
.vehicle-type {
    color: #a1a1aa;
    font-size: 13px;
    margin-top: 5px;
}
.active-label {
    color: #4ade80;
    font-size: 12px;
    font-weight: 700;
    margin-top: 12px;
}
div[data-testid="stMetric"] {
    background: #17171b;
    border: 1px solid #303036;
    padding: 13px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# ==================================================
# LOAD DATA
# ==================================================

try:
    vehicles = load_vehicles()
    trips = load_trips()
    expenses = load_expenses()

except Exception as error:
    st.error("Database connection problem.")
    st.caption(str(error))
    st.stop()

active_vehicles = [
    v for v in vehicles if v["is_active"]
]

archived_vehicles = [
    v for v in vehicles if not v["is_active"]
]


# ==================================================
# HEADER
# ==================================================

st.markdown("""
# 🚛 THEAVA MAJU
**FLEET MANAGEMENT SYSTEM**
""")

st.divider()


# ==================================================
# MENU
# ==================================================

menu = st.sidebar.radio(
    "MENU",
    [
        "Dashboard",
        "Add Trip",
        "Add Expense",
        "Manage Vehicles",
        "Vehicle Statement"
    ]
)


# ==================================================
# DASHBOARD — MONTHLY BUSINESS OVERVIEW
# ==================================================

if menu == "Dashboard":

    st.markdown("## Business Overview")

    today = date.today()

    month_options = []

    for i in range(12):
        month_number = today.month - i
        year_number = today.year

        while month_number <= 0:
            month_number += 12
            year_number -= 1

        month_options.append(
            (date(year_number, month_number, 1).strftime("%B %Y"),
             year_number, month_number)
        )

    selected_month = st.selectbox(
        "Select Month",
        month_options,
        format_func=lambda x: x[0]
    )

    start, end = month_range(
        selected_month[1],
        selected_month[2]
    )

    monthly_trips = [
        t for t in trips
        if in_month(t["trip_date"], start, end)
    ]

    monthly_expenses = [
        e for e in expenses
        if in_month(e["expense_date"], start, end)
    ]

    income_charged = sum(
        int(t["trip_count"]) * float(t["charge_per_trip"])
        for t in monthly_trips
    )

    money_received = sum(
        float(t["received"])
        for t in monthly_trips
    )

    outstanding = income_charged - money_received

    vehicle_expenses = [
        e for e in monthly_expenses
        if e["vehicle"] != "General Business"
    ]

    business_expenses = [
        e for e in monthly_expenses
        if e["vehicle"] == "General Business"
    ]

    total_vehicle_expenses = sum(
        float(e["amount"]) for e in vehicle_expenses
    )

    total_business_expenses = sum(
        float(e["amount"]) for e in business_expenses
    )

    total_expenses = (
        total_vehicle_expenses + total_business_expenses
    )

    profit = income_charged - total_expenses

    st.caption("Monthly Profit & Loss")

    a, b = st.columns(2)
    a.metric("Income Charged", money(income_charged))
    b.metric("Total Expenses", money(total_expenses))

    a, b = st.columns(2)
    a.metric(
        "Net Profit / Loss",
        money(profit),
        delta="Profit" if profit >= 0 else "Loss",
        delta_color="normal"
    )
    b.metric("Outstanding Payments", money(outstanding))

    st.divider()

    st.markdown("### Expense Breakdown")

    a, b = st.columns(2)
    a.metric("Vehicle Expenses", money(total_vehicle_expenses))
    b.metric("Other Business Expenses", money(total_business_expenses))

    st.markdown("### Vehicle Expense Details")

    if vehicle_expenses:
        for v in active_vehicles + archived_vehicles:
            total = sum(
                float(e["amount"])
                for e in vehicle_expenses
                if e["vehicle"] == v["registration"]
            )

            if total > 0:
                st.write(
                    f'**{v["registration"]}** — {money(total)}'
                )
    else:
        st.caption("No vehicle expenses for this month.")

    st.markdown("### Other Business Expenses")

    if business_expenses:
        for category in BUSINESS_CATEGORIES:
            total = sum(
                float(e["amount"])
                for e in business_expenses
                if e["category"] == category
            )

            if total > 0:
                st.write(f"**{category}** — {money(total)}")
    else:
        st.caption("No other business expenses for this month.")

    st.divider()

    st.markdown("### Vehicles")
    st.caption("Select a vehicle to open its records.")

    for start_index in range(0, len(active_vehicles), 2):
        cols = st.columns(2)

        for col, v in zip(
            cols,
            active_vehicles[start_index:start_index + 2]
        ):
            with col:
                st.markdown(
                    f"""
                    <div class="vehicle-card">
                        <div class="vehicle-number">
                            {v["registration"]}
                        </div>
                        <div class="vehicle-type">
                            {v["vehicle_type"]}
                        </div>
                        <div class="active-label">
                            ● ACTIVE
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "Open Vehicle →",
                    key=f'open_vehicle_{v["id"]}',
                    use_container_width=True
                ):
                    st.session_state.selected_vehicle_id = v["id"]
                    st.rerun()

    if st.button("＋ Add Vehicle", use_container_width=True):
        st.session_state.show_add_vehicle = not (
            st.session_state.get("show_add_vehicle", False)
        )
        st.rerun()

    if st.session_state.get("show_add_vehicle", False):

        with st.form("add_vehicle_form"):
            st.markdown("### Register Vehicle")

            registration = st.text_input(
                "Registration Number"
            ).strip().upper()

            vehicle_type = st.selectbox(
                "Vehicle Type",
                ["Lorry", "Hilux", "Car", "Other"]
            )

            save_vehicle = st.form_submit_button("Save Vehicle")

        if save_vehicle:
            existing = [
                v["registration"].upper()
                for v in vehicles
            ]

            if not registration:
                st.error("Enter a registration number.")

            elif registration in existing:
                st.error("This registration already exists.")

            else:
                db.table("vehicles").insert({
                    "registration": registration,
                    "vehicle_type": vehicle_type,
                    "is_active": True
                }).execute()

                st.session_state.show_add_vehicle = False
                st.success("Vehicle added.")
                st.rerun()

    # Selected vehicle detail
    selected_id = st.session_state.get("selected_vehicle_id")

    selected_vehicle = next(
        (v for v in active_vehicles if v["id"] == selected_id),
        None
    )

    if selected_vehicle:

        st.divider()

        if st.button("← Back to Dashboard"):
            st.session_state.selected_vehicle_id = None
            st.rerun()

        registration = selected_vehicle["registration"]

        st.markdown(f"## {registration}")
        st.caption(selected_vehicle["vehicle_type"])

        selected_trips = [
            t for t in trips if t["vehicle"] == registration
        ]

        selected_expenses = [
            e for e in expenses if e["vehicle"] == registration
        ]

        charged = sum(
            int(t["trip_count"]) * float(t["charge_per_trip"])
            for t in selected_trips
        )

        received = sum(
            float(t["received"]) for t in selected_trips
        )

        spent = sum(
            float(e["amount"]) for e in selected_expenses
        )

        a, b = st.columns(2)
        a.metric("Total Charged", money(charged))
        b.metric("Received", money(received))

        a, b = st.columns(2)
        a.metric("Outstanding", money(charged - received))
        b.metric("Total Expenses", money(spent))

        st.markdown("### Trip Records")
        show_trips(selected_trips)

        st.markdown("### Expense Records")
        show_expenses(selected_expenses)


# ==================================================
# ADD TRIP + MANAGE TRIPS ON SAME PAGE
# ==================================================

elif menu == "Add Trip":

    st.markdown("## Add Trip")
    add_trip_form(vehicles)

    st.divider()

    manage_trips(trips, vehicles)


# ==================================================
# ADD EXPENSE + MANAGE EXPENSES ON SAME PAGE
# ==================================================

elif menu == "Add Expense":

    st.markdown("## Add Expense")
    add_expense_form(vehicles)

    st.divider()

    manage_expenses(expenses, vehicles)


# ==================================================
# MANAGE VEHICLES
# ==================================================

elif menu == "Manage Vehicles":

    st.markdown("## Manage Vehicles")

    st.caption(
        "Remove a vehicle from the active list without deleting its records."
    )

    if active_vehicles:

        selected = st.selectbox(
            "Choose Active Vehicle",
            active_vehicles,
            format_func=lambda v: (
                f'{v["registration"]} — {v["vehicle_type"]}'
            )
        )

        st.write("Selected:", selected["registration"])

        confirm_remove = st.checkbox(
            "I confirm I want to remove this vehicle from the active list."
        )

        if st.button(
            "Remove Vehicle",
            disabled=not confirm_remove,
            use_container_width=True
        ):
            db.table("vehicles").update({
                "is_active": False
            }).eq("id", selected["id"]).execute()

            st.success("Vehicle removed from active vehicles.")
            st.rerun()

    else:
        st.info("No active vehicles.")

    st.divider()

    st.markdown("### Archived Vehicles")

    if archived_vehicles:

        for v in archived_vehicles:
            with st.expander(
                f'{v["registration"]} — {v["vehicle_type"]}'
            ):
                st.caption("This vehicle is currently inactive.")

                if st.button(
                    "Restore Vehicle",
                    key=f'restore_{v["id"]}'
                ):
                    db.table("vehicles").update({
                        "is_active": True
                    }).eq("id", v["id"]).execute()

                    st.success("Vehicle restored.")
                    st.rerun()

    else:
        st.caption("No archived vehicles.")


# ==================================================
# VEHICLE STATEMENT
# ==================================================

elif menu == "Vehicle Statement":

    all_vehicle_options = active_vehicles + archived_vehicles

    if not all_vehicle_options:
        st.info("No vehicles found.")

    else:
        selected = st.selectbox(
            "Choose Vehicle",
            all_vehicle_options,
            format_func=lambda v: v["registration"]
        )

        registration = selected["registration"]

        st.markdown(f"## {registration}")

        selected_trips = [
            t for t in trips if t["vehicle"] == registration
        ]

        selected_expenses = [
            e for e in expenses if e["vehicle"] == registration
        ]

        total_trips = sum(
            int(t["trip_count"]) for t in selected_trips
        )

        charged = sum(
            int(t["trip_count"]) * float(t["charge_per_trip"])
            for t in selected_trips
        )

        received = sum(
            float(t["received"]) for t in selected_trips
        )

        spent = sum(
            float(e["amount"]) for e in selected_expenses
        )

        a, b = st.columns(2)
        a.metric("Total Trips", total_trips)
        b.metric("Income Charged", money(charged))

        a, b = st.columns(2)
        a.metric("Money Received", money(received))
        b.metric("Outstanding", money(charged - received))

        st.metric("Total Vehicle Expenses", money(spent))

        st.divider()

        st.markdown("### Trip Details")
        show_trips(selected_trips)

        st.markdown("### Expense Details")
        show_expenses(selected_expenses)


# ==================================================
# FOOTER
# ==================================================

st.divider()
st.caption("THEAVA MAJU • BUSINESS MANAGEMENT SYSTEM")
