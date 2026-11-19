
import streamlit as st
from datetime import date
from supabase import create_client

# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="THEAVA MAJU",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# 2. PREMIUM NAVY & GOLD DESIGN
# =========================================================

st.markdown("""
<style>
.stApp {
    background: #101923;
    color: #F2F4F7;
}
[data-testid="stSidebar"] {
    background: #172330;
    border-right: 1px solid #344454;
}
h1, h2, h3 {
    color: #F2F4F7;
}
[data-testid="stMetric"] {
    background: #1B2936;
    border: 1px solid #344454;
    padding: 15px;
    border-radius: 13px;
}
[data-testid="stMetricLabel"] {
    color: #AAB8C6;
}
[data-testid="stMetricValue"] {
    color: #E8C982;
}
div.stButton > button,
div.stFormSubmitButton > button {
    background: #C5A66B;
    color: #101923;
    border: none;
    border-radius: 9px;
    font-weight: 700;
    min-height: 40px;
}
div.stButton > button:hover,
div.stFormSubmitButton > button:hover {
    background: #E0C58F;
    color: #101923;
}
[data-testid="stExpander"] {
    background: #1B2936;
    border: 1px solid #344454;
    border-radius: 12px;
}
.brand-subtitle {
    color: #C5A66B;
    letter-spacing: 2px;
    font-size: 11px;
    font-weight: 700;
}
.small-note {
    color: #AAB8C6;
    font-size: 13px;
}
hr {
    border-color: #344454;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 3. LOGIN
# =========================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br><br>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown(
            "<h1 style='text-align:center;'>🚛 THEAVA MAJU</h1>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p class='brand-subtitle' style='text-align:center;'>"
            "BUSINESS MANAGEMENT SYSTEM</p>",
            unsafe_allow_html=True
        )

        with st.form("login_form"):
            password = st.text_input("App Password", type="password")
            submitted = st.form_submit_button(
                "UNLOCK SYSTEM",
                use_container_width=True
            )

        if submitted:
            if password == st.secrets["APP_PASSWORD"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")

    st.stop()

# =========================================================
# 4. DATABASE CONNECTION
# =========================================================

@st.cache_resource
def connect_database():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

try:
    db = connect_database()
except Exception as e:
    st.error(f"Database connection failed: {e}")
    st.stop()

# =========================================================
# 5. CONSTANTS
# =========================================================

GENERAL_BUSINESS = "General Business"

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

VEHICLE_TYPES = ["Lorry", "Hilux", "Car", "Other"]

# =========================================================
# 6. GENERAL FUNCTIONS
# =========================================================

def rm(value):
    try:
        return f"RM {float(value or 0):,.2f}"
    except (ValueError, TypeError):
        return "RM 0.00"


def number(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0


def safe_date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except Exception:
        return date.today()


def refresh():
    st.rerun()


def load_data():
    try:
        vehicles = db.table("vehicles").select("*").execute().data or []
        trips = db.table("trips").select("*").execute().data or []
        expenses = db.table("expenses").select("*").execute().data or []
        return vehicles, trips, expenses
    except Exception as e:
        st.error(f"Could not load business records: {e}")
        st.stop()


def insert_record(table, values):
    try:
        db.table(table).insert(values).execute()
        st.success("Saved successfully.")
        refresh()
    except Exception as e:
        st.error(f"Could not save record: {e}")


def update_record(table, record_id, values):
    try:
        db.table(table).update(values).eq("id", record_id).execute()
        st.success("Updated successfully.")
        refresh()
    except Exception as e:
        st.error(f"Could not update record: {e}")


def delete_record(table, record_id):
    try:
        db.table(table).delete().eq("id", record_id).execute()
        st.success("Record deleted.")
        refresh()
    except Exception as e:
        st.error(f"Could not delete record: {e}")


def trip_income(trip):
    return number(trip.get("trip_count")) * number(
        trip.get("charge_per_trip")
    )


def trip_outstanding(trip):
    return trip_income(trip) - number(trip.get("received"))


def is_business(expense):
    return str(expense.get("vehicle") or "") == GENERAL_BUSINESS


def vehicle_list(vehicles, include_archived=True):
    return sorted([
        v.get("registration", "")
        for v in vehicles
        if v.get("registration")
        and (include_archived or v.get("is_active", True))
    ])


def get_vehicle(vehicles, vehicle_id):
    for vehicle in vehicles:
        if str(vehicle.get("id")) == str(vehicle_id):
            return vehicle
    return None


def get_months(trips, expenses):
    months = {date.today().strftime("%Y-%m")}

    for trip in trips:
        if trip.get("trip_date"):
            months.add(str(trip["trip_date"])[:7])

    for expense in expenses:
        if expense.get("expense_date"):
            months.add(str(expense["expense_date"])[:7])

    return sorted(months, reverse=True)


def month_name(month):
    try:
        return date.fromisoformat(month + "-01").strftime("%B %Y")
    except Exception:
        return month


def money_summary(trips, expenses):
    income = sum(trip_income(t) for t in trips)
    received = sum(number(t.get("received")) for t in trips)
    outstanding = income - received
    total_expenses = sum(number(e.get("amount")) for e in expenses)
    return income, received, outstanding, total_expenses


def expense_categories(existing, standard):
    return list(dict.fromkeys(standard + ([existing] if existing else [])))


def header(title, subtitle=None):
    st.title(title)
    if subtitle:
        st.caption(subtitle)


def show_trip_summary(trip):
    st.write(f"**Date:** {trip.get('trip_date', '-')}")
    st.write(f"**Vehicle:** {trip.get('vehicle', '-')}")
    st.write(f"**Company:** {trip.get('company', '-')}")
    st.write(f"**Trips:** {trip.get('trip_count', 0)}")
    st.write(f"**Charge per trip:** {rm(trip.get('charge_per_trip'))}")
    st.write(f"**Total charged:** {rm(trip_income(trip))}")
    st.write(f"**Received:** {rm(trip.get('received'))}")
    st.write(f"**Outstanding:** {rm(trip_outstanding(trip))}")
    if trip.get("notes"):
        st.write(f"**Notes:** {trip.get('notes')}")


def show_expense_summary(expense):
    st.write(f"**Date:** {expense.get('expense_date', '-')}")
    st.write(f"**Category:** {expense.get('category', '-')}")
    st.write(f"**Type:** {'Business' if is_business(expense) else 'Vehicle'}")
    st.write(f"**Vehicle:** {expense.get('vehicle', '-')}")
    st.write(f"**Amount:** {rm(expense.get('amount'))}")
    st.write(f"**Payment method:** {expense.get('payment_method', '-')}")
    st.write(f"**Description:** {expense.get('description', '-')}")
    if expense.get("notes"):
        st.write(f"**Notes:** {expense.get('notes')}")

# =========================================================
# 7. LOAD CURRENT DATA
# =========================================================

vehicles, trips, expenses = load_data()

active_vehicles = [
    v for v in vehicles if v.get("is_active", True)
]

all_vehicle_names = vehicle_list(vehicles)

lorry_names = [
    v["registration"]
    for v in active_vehicles
    if v.get("vehicle_type") == "Lorry"
]

# =========================================================
# 8. SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:
    st.markdown("## 🚛 THEAVA MAJU")
    st.markdown(
        "<p class='brand-subtitle'>BUSINESS MANAGEMENT</p>",
        unsafe_allow_html=True
    )
    st.divider()

    pages = [
        "Dashboard",
        "Add Trip",
        "Trip History",
        "Add Expense",
        "Expense History",
        "Manage Vehicles",
        "Statements"
    ]

    if "page" not in st.session_state:
        st.session_state.page = "Dashboard"

    if st.session_state.page not in pages:
        st.session_state.page = "Dashboard"

    page = st.radio(
        "MAIN MENU",
        pages,
        index=pages.index(st.session_state.page),
        key="main_navigation"
    )
    st.session_state.page = page

    st.divider()
    st.caption("THEAVA MAJU · FLEET SYSTEM")

    if st.button("Log out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.selected_vehicle_id = None
        st.rerun()

# =========================================================
# 9. VEHICLE DETAIL PAGE
# =========================================================

selected_vehicle_id = st.session_state.get("selected_vehicle_id")

selected_vehicle = (
    get_vehicle(vehicles, selected_vehicle_id)
    if selected_vehicle_id is not None
    else None
)

if page == "Dashboard" and selected_vehicle:

    registration = selected_vehicle["registration"]

    if st.button("← Back to Dashboard"):
        st.session_state.selected_vehicle_id = None
        st.rerun()

    header(registration, selected_vehicle.get("vehicle_type", "Vehicle"))

    vehicle_trips = [
        t for t in trips if t.get("vehicle") == registration
    ]

    vehicle_expenses = [
        e for e in expenses if e.get("vehicle") == registration
    ]

    income, received, outstanding, _ = money_summary(
        vehicle_trips, vehicle_expenses
    )

    total_expense = sum(
        number(e.get("amount")) for e in vehicle_expenses
    )

    c1, c2 = st.columns(2)
    c1.metric("Total Income Charged", rm(income))
    c2.metric("Money Received", rm(received))

    c3, c4 = st.columns(2)
    c3.metric("Outstanding", rm(outstanding))
    c4.metric("Vehicle Expenses", rm(total_expense))

    st.divider()

    a, b = st.columns(2)

    with a:
        if st.button("＋ Add Trip", use_container_width=True):
            st.session_state.trip_vehicle_prefill = registration
            st.session_state.page = "Add Trip"
            st.session_state.selected_vehicle_id = None
            st.rerun()

    with b:
        if st.button("＋ Add Expense", use_container_width=True):
            st.session_state.expense_vehicle_prefill = registration
            st.session_state.page = "Add Expense"
            st.session_state.selected_vehicle_id = None
            st.rerun()

    st.divider()
    st.subheader("Vehicle Trip History")

    if not vehicle_trips:
        st.info("No trips recorded for this vehicle.")
    else:
        for trip in sorted(
            vehicle_trips,
            key=lambda x: str(x.get("trip_date", "")),
            reverse=True
        ):
            with st.expander(
                f"{trip.get('trip_date')} · {trip.get('company', '')} · "
                f"{rm(trip_income(trip))}"
            ):
                show_trip_summary(trip)

    st.subheader("Vehicle Expense History")

    if not vehicle_expenses:
        st.info("No expenses recorded for this vehicle.")
    else:
        for expense in sorted(
            vehicle_expenses,
            key=lambda x: str(x.get("expense_date", "")),
            reverse=True
        ):
            with st.expander(
                f"{expense.get('expense_date')} · "
                f"{expense.get('category')} · {rm(expense.get('amount'))}"
            ):
                show_expense_summary(expense)

# =========================================================
# 10. DASHBOARD
# =========================================================

elif page == "Dashboard":

    header("Business Overview", "Your business at a glance.")

    months = get_months(trips, expenses)
    current_month = date.today().strftime("%Y-%m")

    selected_month = st.selectbox(
        "Select Month",
        months,
        index=months.index(current_month) if current_month in months else 0,
        format_func=month_name,
        key="dashboard_month"
    )

    month_trips = [
        t for t in trips
        if str(t.get("trip_date", ""))[:7] == selected_month
    ]

    month_expenses = [
        e for e in expenses
        if str(e.get("expense_date", ""))[:7] == selected_month
    ]

    income, received, outstanding, total_expenses = money_summary(
        month_trips, month_expenses
    )

    profit = income - total_expenses

    st.markdown(f"### {month_name(selected_month)}")

    c1, c2 = st.columns(2)
    c1.metric("Income Charged", rm(income))
    c2.metric("Total Expenses", rm(total_expenses))

    c3, c4 = st.columns(2)
    c3.metric("Profit / Loss", rm(profit))
    c4.metric("Outstanding", rm(outstanding))

    st.caption(
        "Profit / Loss is based on income charged minus recorded expenses. "
        "Outstanding is charged income not yet received."
    )

    st.divider()
    st.subheader("Your Fleet")

    if not active_vehicles:
        st.info("No active vehicles. Register vehicles under Manage Vehicles.")
    else:
        for start in range(0, len(active_vehicles), 2):
            cols = st.columns(2)

            for col, vehicle in zip(
                cols, active_vehicles[start:start + 2]
            ):
                with col:
                    registration = vehicle["registration"]
                    vtype = vehicle.get("vehicle_type", "Vehicle")

                    with st.container(border=True):
                        st.markdown(f"### 🚛 {registration}")
                        st.caption(vtype)

                        v_trips = [
                            t for t in month_trips
                            if t.get("vehicle") == registration
                        ]

                        v_expenses = [
                            e for e in month_expenses
                            if e.get("vehicle") == registration
                        ]

                        v_income = sum(trip_income(t) for t in v_trips)
                        v_cost = sum(
                            number(e.get("amount")) for e in v_expenses
                        )

                        st.write(f"Income: **{rm(v_income)}**")
                        st.write(f"Expenses: **{rm(v_cost)}**")

                        if st.button(
                            "OPEN VEHICLE →",
                            key=f"open_vehicle_{vehicle['id']}",
                            use_container_width=True
                        ):
                            st.session_state.selected_vehicle_id = vehicle["id"]
                            st.rerun()

# =========================================================
# 11. ADD TRIP
# =========================================================

elif page == "Add Trip":

    header("Add Trip", "Record a new vehicle trip.")

    if not lorry_names:
        st.warning("Register an active lorry under Manage Vehicles first.")
    else:
        prefill = st.session_state.get("trip_vehicle_prefill")
        default_index = (
            lorry_names.index(prefill)
            if prefill in lorry_names else 0
        )

        with st.form("add_trip_form"):

            trip_date = st.date_input("Trip Date", value=date.today())

            vehicle = st.selectbox(
                "Vehicle",
                lorry_names,
                index=default_index
            )

            company = st.text_input("Company / Customer")
            trip_count = st.number_input(
                "Number of Trips",
                min_value=1,
                step=1,
                value=1
            )

            charge = st.number_input(
                "Charge Per Trip (RM)",
                min_value=0.0,
                step=10.0
            )

            received = st.number_input(
                "Amount Received (RM)",
                min_value=0.0,
                step=10.0
            )

            notes = st.text_area("Notes (Optional)")

            submitted = st.form_submit_button(
                "SAVE TRIP",
                use_container_width=True
            )

            if submitted:
                if not company.strip():
                    st.error("Please enter a company or customer.")
                elif received > trip_count * charge:
                    st.error("Received amount cannot exceed total trip charge.")
                else:
                    insert_record("trips", {
                        "trip_date": str(trip_date),
                        "vehicle": vehicle,
                        "company": company.strip(),
                        "trip_count": int(trip_count),
                        "charge_per_trip": charge,
                        "received": received,
                        "notes": notes.strip()
                    })

# =========================================================
# 12. TRIP HISTORY
# =========================================================

elif page == "Trip History":

    header("Trip History", "View, edit and delete recorded trips.")

    if not trips:
        st.info("No trips recorded yet.")
    else:
        sorted_trips = sorted(
            trips,
            key=lambda x: str(x.get("trip_date", "")),
            reverse=True
        )

        st.caption(f"{len(sorted_trips)} trip records")

        for trip in sorted_trips:

            trip_id = trip["id"]

            with st.expander(
                f"{trip.get('trip_date')} · {trip.get('vehicle')} · "
                f"{trip.get('company')} · {rm(trip_income(trip))}"
            ):

                show_trip_summary(trip)

                st.divider()

                with st.form(f"edit_trip_{trip_id}"):

                    edit_date = st.date_input(
                        "Trip Date",
                        value=safe_date(trip.get("trip_date")),
                        key=f"trip_date_{trip_id}"
                    )

                    old_vehicle = trip.get("vehicle", "")
                    trip_vehicles = sorted(set(
                        lorry_names + ([old_vehicle] if old_vehicle else [])
                    ))

                    if not trip_vehicles:
                        trip_vehicles = [old_vehicle or "Unknown"]

                    edit_vehicle = st.selectbox(
                        "Vehicle",
                        trip_vehicles,
                        index=(
                            trip_vehicles.index(old_vehicle)
                            if old_vehicle in trip_vehicles else 0
                        ),
                        key=f"trip_vehicle_{trip_id}"
                    )

                    edit_company = st.text_input(
                        "Company / Customer",
                        value=trip.get("company", ""),
                        key=f"trip_company_{trip_id}"
                    )

                    edit_count = st.number_input(
                        "Number of Trips",
                        min_value=1,
                        step=1,
                        value=max(1, int(number(trip.get("trip_count")))),
                        key=f"trip_count_{trip_id}"
                    )

                    edit_charge = st.number_input(
                        "Charge Per Trip (RM)",
                        min_value=0.0,
                        value=number(trip.get("charge_per_trip")),
                        step=10.0,
                        key=f"trip_charge_{trip_id}"
                    )

                    edit_received = st.number_input(
                        "Amount Received (RM)",
                        min_value=0.0,
                        value=number(trip.get("received")),
                        step=10.0,
                        key=f"trip_received_{trip_id}"
                    )

                    edit_notes = st.text_area(
                        "Notes",
                        value=trip.get("notes") or "",
                        key=f"trip_notes_{trip_id}"
                    )

                    save = st.form_submit_button("SAVE CHANGES")

                    if save:
                        if not edit_company.strip():
                            st.error("Company name is required.")
                        elif edit_received > edit_count * edit_charge:
                            st.error("Received cannot exceed total charge.")
                        else:
                            update_record("trips", trip_id, {
                                "trip_date": str(edit_date),
                                "vehicle": edit_vehicle,
                                "company": edit_company.strip(),
                                "trip_count": int(edit_count),
                                "charge_per_trip": edit_charge,
                                "received": edit_received,
                                "notes": edit_notes.strip()
                            })

                with st.form(f"delete_trip_{trip_id}"):
                    confirm = st.checkbox(
                        "I confirm I want to permanently delete this trip.",
                        key=f"confirm_trip_{trip_id}"
                    )
                    delete = st.form_submit_button("DELETE TRIP")

                    if delete:
                        if confirm:
                            delete_record("trips", trip_id)
                        else:
                            st.warning("Please confirm before deleting.")

# =========================================================
# 13. ADD EXPENSE
# =========================================================

elif page == "Add Expense":

    header("Add Expense", "Record vehicle or general business expenses.")

    expense_type = st.radio(
        "Expense Type",
        ["Vehicle Expense", "Other Business Expense"],
        horizontal=True,
        key="new_expense_type"
    )

    if expense_type == "Vehicle Expense":

        if not active_vehicles:
            st.warning("Register a vehicle under Manage Vehicles first.")
        else:
            prefill = st.session_state.get("expense_vehicle_prefill")
            active_names = vehicle_list(active_vehicles)

            default_index = (
                active_names.index(prefill)
                if prefill in active_names else 0
            )

            with st.form("vehicle_expense_form"):

                expense_date = st.date_input(
                    "Expense Date",
                    value=date.today()
                )

                vehicle = st.selectbox(
                    "Vehicle",
                    active_names,
                    index=default_index
                )

                category = st.selectbox(
                    "Expense Category",
                    VEHICLE_CATEGORIES
                )

                amount = st.number_input(
                    "Amount (RM)",
                    min_value=0.0,
                    step=10.0
                )

                payment_method = st.selectbox(
                    "Payment Method",
                    ["Cash", "Bank Transfer", "Card", "Other"]
                )

                description = st.text_input("Description")
                notes = st.text_area("Notes (Optional)")

                submitted = st.form_submit_button(
                    "SAVE VEHICLE EXPENSE",
                    use_container_width=True
                )

                if submitted:
                    if amount <= 0:
                        st.error("Enter an amount greater than zero.")
                    else:
                        insert_record("expenses", {
                            "expense_date": str(expense_date),
                            "category": category,
                            "vehicle": vehicle,
                            "amount": amount,
                            "payment_method": payment_method,
                            "description": description.strip(),
                            "notes": notes.strip()
                        })

    else:

        st.info(
            "General business expenses do not need a vehicle number. "
            "Examples: electricity, worker salary and office expenses."
        )

        with st.form("business_expense_form"):

            expense_date = st.date_input(
                "Expense Date",
                value=date.today(),
                key="business_expense_date"
            )

            category = st.selectbox(
                "Expense Category",
                BUSINESS_CATEGORIES
            )

            amount = st.number_input(
                "Amount (RM)",
                min_value=0.0,
                step=10.0,
                key="business_expense_amount"
            )

            payment_method = st.selectbox(
                "Payment Method",
                ["Cash", "Bank Transfer", "Card", "Other"],
                key="business_payment_method"
            )

            description = st.text_input("Description")
            notes = st.text_area("Notes (Optional)")

            submitted = st.form_submit_button(
                "SAVE BUSINESS EXPENSE",
                use_container_width=True
            )

            if submitted:
                if amount <= 0:
                    st.error("Enter an amount greater than zero.")
                else:
                    insert_record("expenses", {
                        "expense_date": str(expense_date),
                        "category": category,
                        "vehicle": GENERAL_BUSINESS,
                        "amount": amount,
                        "payment_method": payment_method,
                        "description": description.strip(),
                        "notes": notes.strip()
                    })

# =========================================================
# 14. EXPENSE HISTORY
# =========================================================

elif page == "Expense History":

    header("Expense History", "View, edit and delete all expenses.")

    if not expenses:
        st.info("No expenses recorded yet.")
    else:
        sorted_expenses = sorted(
            expenses,
            key=lambda x: str(x.get("expense_date", "")),
            reverse=True
        )

        st.caption(f"{len(sorted_expenses)} expense records")

        for expense in sorted_expenses:

            expense_id = expense["id"]
            business = is_business(expense)

            with st.expander(
                f"{expense.get('expense_date')} · "
                f"{expense.get('category')} · "
                f"{rm(expense.get('amount'))}"
            ):

                show_expense_summary(expense)

                st.divider()

                with st.form(f"edit_expense_{expense_id}"):

                    edit_date = st.date_input(
                        "Expense Date",
                        value=safe_date(expense.get("expense_date")),
                        key=f"expense_date_{expense_id}"
                    )

                    edit_type = st.selectbox(
                        "Expense Type",
                        ["Vehicle Expense", "Other Business Expense"],
                        index=1 if business else 0,
                        key=f"expense_type_{expense_id}"
                    )

                    if edit_type == "Other Business Expense":
                        edit_vehicle = GENERAL_BUSINESS
                        category_options = expense_categories(
                            expense.get("category"),
                            BUSINESS_CATEGORIES
                        )
                    else:
                        old_vehicle = expense.get("vehicle", "")
                        available = sorted(set(
                            vehicle_list(vehicles) +
                            ([old_vehicle] if old_vehicle and old_vehicle != GENERAL_BUSINESS else [])
                        ))

                        if not available:
                            available = ["Unknown"]

                        edit_vehicle = st.selectbox(
                            "Vehicle",
                            available,
                            index=(
                                available.index(old_vehicle)
                                if old_vehicle in available else 0
                            ),
                            key=f"expense_vehicle_{expense_id}"
                        )

                        category_options = expense_categories(
                            expense.get("category"),
                            VEHICLE_CATEGORIES
                        )

                    edit_category = st.selectbox(
                        "Category",
                        category_options,
                        index=(
                            category_options.index(expense.get("category"))
                            if expense.get("category") in category_options else 0
                        ),
                        key=f"expense_category_{expense_id}"
                    )

                    edit_amount = st.number_input(
                        "Amount (RM)",
                        min_value=0.0,
                        value=number(expense.get("amount")),
                        step=10.0,
                        key=f"expense_amount_{expense_id}"
                    )

                    payment_options = [
                        "Cash", "Bank Transfer", "Card", "Other"
                    ]

                    old_payment = expense.get("payment_method") or "Cash"
                    if old_payment not in payment_options:
                        payment_options.append(old_payment)

                    edit_payment = st.selectbox(
                        "Payment Method",
                        payment_options,
                        index=payment_options.index(old_payment),
                        key=f"expense_payment_{expense_id}"
                    )

                    edit_description = st.text_input(
                        "Description",
                        value=expense.get("description") or "",
                        key=f"expense_description_{expense_id}"
                    )

                    edit_notes = st.text_area(
                        "Notes",
                        value=expense.get("notes") or "",
                        key=f"expense_notes_{expense_id}"
                    )

                    save = st.form_submit_button("SAVE CHANGES")

                    if save:
                        if edit_amount <= 0:
                            st.error("Enter an amount greater than zero.")
                        else:
                            update_record("expenses", expense_id, {
                                "expense_date": str(edit_date),
                                "category": edit_category,
                                "vehicle": edit_vehicle,
                                "amount": edit_amount,
                                "payment_method": edit_payment,
                                "description": edit_description.strip(),
                                "notes": edit_notes.strip()
                            })

                with st.form(f"delete_expense_{expense_id}"):
                    confirm = st.checkbox(
                        "I confirm I want to permanently delete this expense.",
                        key=f"confirm_expense_{expense_id}"
                    )

                    delete = st.form_submit_button("DELETE EXPENSE")

                    if delete:
                        if confirm:
                            delete_record("expenses", expense_id)
                        else:
                            st.warning("Please confirm before deleting.")

# =========================================================
# 15. MANAGE VEHICLES
# =========================================================

elif page == "Manage Vehicles":

    header("Manage Vehicles", "Register, update and archive your fleet.")

    st.subheader("Register New Vehicle")

    with st.form("register_vehicle_form"):

        registration = st.text_input(
            "Vehicle Registration Number"
        ).strip().upper()

        vehicle_type = st.selectbox(
            "Vehicle Type",
            VEHICLE_TYPES
        )

        submitted = st.form_submit_button(
            "REGISTER VEHICLE",
            use_container_width=True
        )

        if submitted:
            if not registration:
                st.error("Enter a registration number.")
            elif any(
                v.get("registration", "").upper() == registration
                for v in vehicles
            ):
                st.error("This registration number already exists.")
            else:
                insert_record("vehicles", {
                    "registration": registration,
                    "vehicle_type": vehicle_type,
                    "is_active": True
                })

    st.divider()
    st.subheader("Active Vehicles")

    if not active_vehicles:
        st.info("No active vehicles.")
    else:
        for vehicle in active_vehicles:

            vehicle_id = vehicle["id"]
            registration = vehicle["registration"]

            with st.expander(
                f"🚛 {registration} · {vehicle.get('vehicle_type', '')}"
            ):

                with st.form(f"edit_vehicle_{vehicle_id}"):

                    new_registration = st.text_input(
                        "Registration Number",
                        value=registration,
                        key=f"registration_{vehicle_id}"
                    ).strip().upper()

                    new_type = st.selectbox(
                        "Vehicle Type",
                        VEHICLE_TYPES,
                        index=(
                            VEHICLE_TYPES.index(vehicle.get("vehicle_type"))
                            if vehicle.get("vehicle_type") in VEHICLE_TYPES
                            else 0
                        ),
                        key=f"type_{vehicle_id}"
                    )

                    save = st.form_submit_button("SAVE VEHICLE")

                    if save:
                        duplicate = any(
                            v.get("registration", "").upper() == new_registration
                            and str(v.get("id")) != str(vehicle_id)
                            for v in vehicles
                        )

                        if not new_registration:
                            st.error("Registration number is required.")
                        elif duplicate:
                            st.error("That registration number is already used.")
                        else:
                            update_record("vehicles", vehicle_id, {
                                "registration": new_registration,
                                "vehicle_type": new_type
                            })

                with st.form(f"archive_vehicle_{vehicle_id}"):
                    confirm = st.checkbox(
                        "I confirm I want to archive this vehicle.",
                        key=f"archive_confirm_{vehicle_id}"
                    )

                    archive = st.form_submit_button("ARCHIVE VEHICLE")

                    if archive:
                        if confirm:
                            update_record("vehicles", vehicle_id, {
                                "is_active": False
                            })
                        else:
                            st.warning("Please confirm before archiving.")

    archived = [
        v for v in vehicles if not v.get("is_active", True)
    ]

    st.divider()
    st.subheader("Archived Vehicles")

    if not archived:
        st.caption("No archived vehicles.")
    else:
        for vehicle in archived:

            vehicle_id = vehicle["id"]

            with st.expander(
                f"Archived · {vehicle.get('registration')}"
            ):
                st.write(
                    f"Type: {vehicle.get('vehicle_type', 'Vehicle')}"
                )

                if st.button(
                    "RESTORE VEHICLE",
                    key=f"restore_{vehicle_id}"
                ):
                    update_record("vehicles", vehicle_id, {
                        "is_active": True
                    })

# =========================================================
# 16. STATEMENTS
# =========================================================

elif page == "Statements":

    header("Statements", "Business financial records.")

    statement_type = st.radio(
        "Choose Statement",
        [
            "Vehicle Statement",
            "Business Expenses Statement"
        ],
        horizontal=True
    )

    st.divider()

    # -----------------------------------------------------
    # VEHICLE STATEMENT
    # -----------------------------------------------------

    if statement_type == "Vehicle Statement":

        st.subheader("Vehicle Statement")

        if not all_vehicle_names:
            st.info("No vehicles registered.")
        else:
            selected_registration = st.selectbox(
                "Select Vehicle",
                all_vehicle_names
            )

            selected_trips = [
                t for t in trips
                if t.get("vehicle") == selected_registration
            ]

            selected_expenses = [
                e for e in expenses
                if e.get("vehicle") == selected_registration
            ]

            income = sum(trip_income(t) for t in selected_trips)
            received = sum(
                number(t.get("received")) for t in selected_trips
            )
            outstanding = income - received
            expense_total = sum(
                number(e.get("amount")) for e in selected_expenses
            )

            c1, c2 = st.columns(2)
            c1.metric("Income Charged", rm(income))
            c2.metric("Money Received", rm(received))

            c3, c4 = st.columns(2)
            c3.metric("Outstanding", rm(outstanding))
            c4.metric("Vehicle Expenses", rm(expense_total))

            st.divider()
            st.subheader("Trip Records")

            if not selected_trips:
                st.info("No trip records.")
            else:
                for trip in sorted(
                    selected_trips,
                    key=lambda x: str(x.get("trip_date", "")),
                    reverse=True
                ):
                    with st.expander(
                        f"{trip.get('trip_date')} · "
                        f"{trip.get('company')} · {rm(trip_income(trip))}"
                    ):
                        show_trip_summary(trip)

            st.subheader("Expense Records")

            if not selected_expenses:
                st.info("No vehicle expenses.")
            else:
                for expense in sorted(
                    selected_expenses,
                    key=lambda x: str(x.get("expense_date", "")),
                    reverse=True
                ):
                    with st.expander(
                        f"{expense.get('expense_date')} · "
                        f"{expense.get('category')} · "
                        f"{rm(expense.get('amount'))}"
                    ):
                        show_expense_summary(expense)

    # -----------------------------------------------------
    # BUSINESS EXPENSE STATEMENT
    # -----------------------------------------------------

    else:

        st.subheader("Business Expenses Statement")

        business_expenses = [
            e for e in expenses if is_business(e)
        ]

        if not business_expenses:
            st.info("No general business expenses recorded.")
        else:
            total = sum(
                number(e.get("amount"))
                for e in business_expenses
            )

            st.metric("Total Business Expenses", rm(total))

            category_totals = {}

            for expense in business_expenses:
                category = expense.get("category") or "Other"
                category_totals[category] = (
                    category_totals.get(category, 0)
                    + number(expense.get("amount"))
                )

            st.divider()
            st.subheader("Expenses by Category")

            for category, amount in sorted(category_totals.items()):
                st.write(f"**{category}**")
                st.write(rm(amount))
                st.divider()

            st.subheader("Business Expense Records")

            for expense in sorted(
                business_expenses,
                key=lambda x: str(x.get("expense_date", "")),
                reverse=True
            ):
                with st.expander(
                    f"{expense.get('expense_date')} · "
                    f"{expense.get('category')} · "
                    f"{rm(expense.get('amount'))}"
                ):
                    show_expense_summary(expense)

# =========================================================
# 17. FOOTER
# =========================================================

st.divider()
st.caption("THEAVA MAJU · BUSINESS MANAGEMENT SYSTEM")
