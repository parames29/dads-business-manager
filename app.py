
import streamlit as st
from datetime import date
from supabase import create_client

# --------------------------------------------------
# PAGE SETTINGS
# --------------------------------------------------

st.set_page_config(
    page_title="THEAVA MAJU",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# LOGIN
# --------------------------------------------------

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🚛 THEAVA MAJU")
    st.caption("FLEET MANAGEMENT SYSTEM")

    with st.form("login_form"):
        password = st.text_input(
            "Enter your app password",
            type="password"
        )
        submitted = st.form_submit_button("Unlock")

    if submitted:
        if password == st.secrets["APP_PASSWORD"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password.")

    st.stop()

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
db = create_client(url, key)

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

CATEGORIES = [
    "Fuel",
    "Repair",
    "Tyres",
    "Servicing",
    "Toll",
    "Worker Salary",
    "Bin Cost",
    "Office Expense",
    "Other"
]

PAYMENT_METHODS = [
    "Cash",
    "Bank Transfer",
    "Card",
    "Other"
]


def money(value):
    return f"RM {float(value or 0):,.2f}"


# --------------------------------------------------
# DATABASE FUNCTIONS
# --------------------------------------------------

def load_vehicles():
    return (
        db.table("vehicles")
        .select("*")
        .order("id")
        .execute()
        .data or []
    )


def load_trips():
    return (
        db.table("trips")
        .select("*")
        .order("trip_date", desc=True)
        .execute()
        .data or []
    )


def load_expenses():
    return (
        db.table("expenses")
        .select("*")
        .order("expense_date", desc=True)
        .execute()
        .data or []
    )


# --------------------------------------------------
# DISPLAY FUNCTIONS
# --------------------------------------------------

def show_trips(rows):
    if not rows:
        st.info("No trip records yet.")
        return

    data = []

    for t in rows:
        total = (
            int(t["trip_count"])
            * float(t["charge_per_trip"])
        )

        received = float(t["received"])

        data.append({
            "Date": t["trip_date"],
            "Vehicle": t["vehicle"],
            "Company": t["company"],
            "Trips": t["trip_count"],
            "Rate": money(t["charge_per_trip"]),
            "Total Charged": money(total),
            "Received": money(received),
            "Outstanding": money(total - received)
        })

    st.dataframe(data, use_container_width=True)


def show_expenses(rows):
    if not rows:
        st.info("No expense records yet.")
        return

    data = []

    for e in rows:
        data.append({
            "Date": e["expense_date"],
            "Category": e["category"],
            "Vehicle": e["vehicle"],
            "Amount": money(e["amount"]),
            "Description": e["description"],
            "Payment": e["payment_method"]
        })

    st.dataframe(data, use_container_width=True)


# --------------------------------------------------
# ADD TRIP FORM
# --------------------------------------------------

def add_trip_form(vehicle_list, default_vehicle=None, form_key="add_trip"):
    if not vehicle_list:
        st.warning("Please add a vehicle first.")
        return

    st.subheader("Add Trip")

    default_index = 0

    if default_vehicle in vehicle_list:
        default_index = vehicle_list.index(default_vehicle)

    with st.form(form_key):
        trip_date = st.date_input(
            "Trip date",
            value=date.today()
        )

        vehicle = st.selectbox(
            "Vehicle",
            vehicle_list,
            index=default_index
        )

        company = st.text_input("Company / Customer")

        count = st.number_input(
            "Number of trips",
            min_value=1,
            max_value=100,
            value=1
        )

        rate = st.number_input(
            "Charge per trip (RM)",
            min_value=0.0,
            step=10.0
        )

        total = count * rate

        st.write("**Total charge:**", money(total))

        received = st.number_input(
            "Money received (RM)",
            min_value=0.0,
            value=0.0,
            step=10.0
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

            st.success("Trip saved successfully.")
            st.rerun()


# --------------------------------------------------
# ADD EXPENSE FORM
# --------------------------------------------------

def add_expense_form(vehicle_list, default_vehicle=None, form_key="add_expense"):
    if not vehicle_list:
        st.warning("Please add a vehicle first.")
        return

    default_index = 0

    if default_vehicle in vehicle_list:
        default_index = vehicle_list.index(default_vehicle)

    st.subheader("Add Expense")

    with st.form(form_key):
        expense_date = st.date_input(
            "Expense date",
            value=date.today()
        )

        category = st.selectbox(
            "Category",
            CATEGORIES
        )

        vehicle = st.selectbox(
            "Vehicle",
            ["General Business"] + vehicle_list,
            index=(
                default_index + 1
                if default_vehicle in vehicle_list
                else 0
            )
        )

        amount = st.number_input(
            "Amount (RM)",
            min_value=0.01,
            step=10.0
        )

        payment = st.selectbox(
            "Payment method",
            PAYMENT_METHODS
        )

        description = st.text_input("Description")
        notes = st.text_area("Notes")

        submitted = st.form_submit_button("Save Expense")

    if submitted:
        if not description.strip():
            st.error("Enter an expense description.")

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

            st.success("Expense saved successfully.")
            st.rerun()


# --------------------------------------------------
# DESIGN
# --------------------------------------------------

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
    min-height: 45px;
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
    color: #ffffff;
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
    padding: 14px;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD DATABASE RECORDS
# --------------------------------------------------

try:
    vehicles = load_vehicles()
    trips = load_trips()
    expenses = load_expenses()

except Exception as error:
    st.error("Could not connect to the database.")
    st.caption(str(error))
    st.stop()


active_vehicles = [
    v for v in vehicles
    if v.get("is_active", True)
]

VEHICLES = [
    v["registration"]
    for v in active_vehicles
]

LORRIES = [
    v["registration"]
    for v in active_vehicles
    if v["vehicle_type"] == "Lorry"
]


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown("""
# 🚛 THEAVA MAJU
**FLEET MANAGEMENT SYSTEM**
""")

st.divider()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

menu = st.sidebar.radio(
    "MENU",
    [
        "Dashboard",
        "Add Trip",
        "Trip History",
        "Add Expense",
        "Expense History",
        "Vehicle Statement"
    ]
)


# --------------------------------------------------
# VEHICLE DETAIL PAGE
# --------------------------------------------------

selected_vehicle_id = st.session_state.get(
    "selected_vehicle_id"
)

selected_vehicle = next(
    (
        v for v in active_vehicles
        if v["id"] == selected_vehicle_id
    ),
    None
)


if menu == "Dashboard" and selected_vehicle:

    vehicle = selected_vehicle["registration"]

    if st.button("← Back to Vehicles"):
        st.session_state.selected_vehicle_id = None
        st.session_state.vehicle_action = None
        st.rerun()

    st.markdown(f"## {vehicle}")
    st.caption(selected_vehicle["vehicle_type"] + " • ACTIVE")

    vehicle_trips = [
        t for t in trips
        if t["vehicle"] == vehicle
    ]

    vehicle_expenses = [
        e for e in expenses
        if e["vehicle"] == vehicle
    ]

    charged = sum(
        int(t["trip_count"]) * float(t["charge_per_trip"])
        for t in vehicle_trips
    )

    received = sum(
        float(t["received"])
        for t in vehicle_trips
    )

    outstanding = charged - received

    spent = sum(
        float(e["amount"])
        for e in vehicle_expenses
    )

    trip_count = sum(
        int(t["trip_count"])
        for t in vehicle_trips
    )

    st.divider()

    st.markdown("### Vehicle Overview")

    a, b = st.columns(2)
    a.metric("Total Trips", trip_count)
    b.metric("Money Received", money(received))

    a, b = st.columns(2)
    a.metric("Outstanding", money(outstanding))
    b.metric("Vehicle Expenses", money(spent))

    st.divider()

    st.markdown("### Manage Vehicle")

    a, b = st.columns(2)

    with a:
        if st.button("＋ Add Trip", use_container_width=True):
            st.session_state.vehicle_action = "trip"
            st.rerun()

    with b:
        if st.button("＋ Add Expense", use_container_width=True):
            st.session_state.vehicle_action = "expense"
            st.rerun()

    action = st.session_state.get("vehicle_action")

    if action == "trip":
        st.divider()
        if st.button("Close Trip Form"):
            st.session_state.vehicle_action = None
            st.rerun()

        add_trip_form(
            LORRIES if selected_vehicle["vehicle_type"] == "Lorry"
            else VEHICLES,
            default_vehicle=vehicle,
            form_key="vehicle_add_trip"
        )

    elif action == "expense":
        st.divider()
        if st.button("Close Expense Form"):
            st.session_state.vehicle_action = None
            st.rerun()

        add_expense_form(
            VEHICLES,
            default_vehicle=vehicle,
            form_key="vehicle_add_expense"
        )

    st.divider()

    st.markdown("### Trip History")
    show_trips(vehicle_trips)

    st.markdown("### Expense History")
    show_expenses(vehicle_expenses)

    st.markdown("### Vehicle Statement")
    st.write("Income Charged:", money(charged))
    st.write("Money Received:", money(received))
    st.write("Outstanding:", money(outstanding))
    st.write("Vehicle Expenses:", money(spent))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------



elif menu == "Dashboard":

    st.markdown("## Vehicles")
    st.caption("Select a vehicle to manage its trips and expenses.")

    # Show vehicles FIRST
    if not active_vehicles:
        st.info("No active vehicles. Add your first vehicle.")

    for start in range(0, len(active_vehicles), 2):
        cols = st.columns(2)

        for col, v in zip(
            cols,
            active_vehicles[start:start + 2]
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
                    st.session_state.vehicle_action = None
                    st.rerun()

    # ADD VEHICLE BUTTON BELOW THE VEHICLE LIST
    st.divider()

    if st.button("＋ Add Vehicle", use_container_width=True):
        st.session_state.show_add_vehicle = not (
            st.session_state.get("show_add_vehicle", False)
        )
        st.rerun()

    if st.session_state.get("show_add_vehicle", False):

        st.markdown("### Register New Vehicle")

        with st.form("new_vehicle_form"):
            registration = st.text_input(
                "Vehicle Registration"
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
                st.error("Enter a vehicle registration.")

            elif registration in existing:
                st.error("This vehicle already exists.")

            else:
                db.table("vehicles").insert({
                    "registration": registration,
                    "vehicle_type": vehicle_type,
                    "is_active": True
                }).execute()

                st.session_state.show_add_vehicle = False
                st.success("Vehicle added.")
                st.rerun()


# --------------------------------------------------
# GLOBAL ADD TRIP
# --------------------------------------------------

elif menu == "Add Trip":

    add_trip_form(
        LORRIES,
        form_key="global_add_trip"
    )


# --------------------------------------------------
# TRIP HISTORY / EDIT / DELETE
# --------------------------------------------------

elif menu == "Trip History":

    st.markdown("## Trip History")
    show_trips(trips)

    if trips:

        options = {
            f'ID {t["id"]} | {t["trip_date"]} | {t["vehicle"]} | {t["company"]}': t
            for t in trips
        }

        selected_label = st.selectbox(
            "Select a trip to edit",
            list(options)
        )

        t = options[selected_label]

        with st.form("edit_trip"):

            trip_date = st.date_input(
                "Date",
                value=date.fromisoformat(str(t["trip_date"]))
            )

            vehicle = st.selectbox(
                "Vehicle",
                VEHICLES or [t["vehicle"]],
                index=(
                    VEHICLES.index(t["vehicle"])
                    if t["vehicle"] in VEHICLES else 0
                )
            )

            company = st.text_input(
                "Company",
                value=t["company"]
            )

            count = st.number_input(
                "Number of trips",
                min_value=1,
                max_value=100,
                value=int(t["trip_count"])
            )

            rate = st.number_input(
                "Rate per trip (RM)",
                min_value=0.0,
                value=float(t["charge_per_trip"]),
                step=10.0
            )

            received = st.number_input(
                "Received (RM)",
                min_value=0.0,
                value=float(t["received"]),
                step=10.0
            )

            notes = st.text_area(
                "Notes",
                value=t.get("notes") or ""
            )

            save = st.form_submit_button("Save Changes")

        if save:

            if not company.strip():
                st.error("Company name is required.")

            elif received > count * rate:
                st.error("Received cannot exceed total charge.")

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
                db.table("trips").delete().eq(
                    "id", t["id"]
                ).execute()

                st.success("Trip deleted.")
                st.rerun()


# --------------------------------------------------
# GLOBAL ADD EXPENSE
# --------------------------------------------------

elif menu == "Add Expense":

    add_expense_form(
        VEHICLES,
        form_key="global_add_expense"
    )


# --------------------------------------------------
# EXPENSE HISTORY / EDIT / DELETE
# --------------------------------------------------

elif menu == "Expense History":

    st.markdown("## Expense History")
    show_expenses(expenses)

    if expenses:

        options = {
            f'ID {e["id"]} | {e["expense_date"]} | {e["description"]}': e
            for e in expenses
        }

        label = st.selectbox(
            "Select an expense to edit",
            list(options)
        )

        e = options[label]

        with st.form("edit_expense"):

            expense_date = st.date_input(
                "Date",
                value=date.fromisoformat(str(e["expense_date"]))
            )

            category = st.selectbox(
                "Category",
                CATEGORIES,
                index=(
                    CATEGORIES.index(e["category"])
                    if e["category"] in CATEGORIES else 0
                )
            )

            vehicle_options = ["General Business"] + VEHICLES

            if e["vehicle"] not in vehicle_options:
                vehicle_options.append(e["vehicle"])

            vehicle = st.selectbox(
                "Vehicle",
                vehicle_options,
                index=vehicle_options.index(e["vehicle"])
            )

            amount = st.number_input(
                "Amount (RM)",
                min_value=0.01,
                value=float(e["amount"]),
                step=10.0
            )

            payment = st.selectbox(
                "Payment method",
                PAYMENT_METHODS,
                index=(
                    PAYMENT_METHODS.index(e["payment_method"])
                    if e["payment_method"] in PAYMENT_METHODS else 0
                )
            )

            description = st.text_input(
                "Description",
                value=e["description"]
            )

            notes = st.text_area(
                "Notes",
                value=e.get("notes") or ""
            )

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
                db.table("expenses").delete().eq(
                    "id", e["id"]
                ).execute()

                st.success("Expense deleted.")
                st.rerun()


# --------------------------------------------------
# VEHICLE STATEMENT
# --------------------------------------------------

elif menu == "Vehicle Statement":

    if not VEHICLES:
        st.info("No active vehicles available.")

    else:

        vehicle = st.selectbox(
            "Choose vehicle",
            VEHICLES
        )

        st.markdown(f"## Statement: {vehicle}")

        vehicle_trips = [
            t for t in trips
            if t["vehicle"] == vehicle
        ]

        vehicle_expenses = [
            e for e in expenses
            if e["vehicle"] == vehicle
        ]

        total_trips = sum(
            int(t["trip_count"])
            for t in vehicle_trips
        )

        total_charged = sum(
            int(t["trip_count"]) * float(t["charge_per_trip"])
            for t in vehicle_trips
        )

        total_received = sum(
            float(t["received"])
            for t in vehicle_trips
        )

        total_expenses = sum(
            float(e["amount"])
            for e in vehicle_expenses
        )

        a, b = st.columns(2)
        a.metric("Total Trips", total_trips)
        b.metric("Income Charged", money(total_charged))

        a, b = st.columns(2)
        a.metric("Money Received", money(total_received))
        b.metric("Outstanding", money(total_charged - total_received))

        st.metric("Vehicle Expenses", money(total_expenses))

        st.divider()

        st.markdown("### Trip Details")
        show_trips(vehicle_trips)

        st.markdown("### Expense Details")
        show_expenses(vehicle_expenses)


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption("THEAVA MAJU • FLEET MANAGEMENT SYSTEM")
