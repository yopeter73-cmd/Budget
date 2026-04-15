import streamlit as st
import pandas as pd
from pathlib import Path
import os

# --- CONFIGURATION & PATHS ---
USER_FILE = Path("users.csv")
months = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'August', 'Sept', 'Oct', 'Nov', 'Dec']

# --- USER MANAGEMENT FUNCTIONS ---
def load_users():
    if USER_FILE.exists():
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

# --- SESSION STATE INIT ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
if 'viewing_user' not in st.session_state:
    st.session_state.viewing_user = ""

# --- AUTHENTICATION UI ---
if not st.session_state.logged_in:
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.title("🔐 Login")
        with st.form("login_form"):
            user = st.text_input("Username").lower()
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                users = load_users()
                if user == "admin" and pw == "1234": # Master Admin
                    st.session_state.logged_in = True
                    st.session_state.username = "admin"
                    st.session_state.viewing_user = "admin"
                    st.rerun()
                elif not users[(users['username'] == user) & (users['password'] == pw)].empty:
                    st.session_state.logged_in = True
                    st.session_state.username = user
                    st.session_state.viewing_user = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        st.title("📝 Create Account")
        with st.form("signup_form"):
            new_user = st.text_input("New Username").lower()
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Sign Up"):
                if new_pw != confirm_pw:
                    st.error("Passwords do not match")
                elif len(new_user) < 3:
                    st.error("Username too short")
                else:
                    if save_user(new_user, new_pw):
                        st.success("Account created! Go to Login tab.")
                    else:
                        st.error("Username already exists")
    st.stop()

# --- ADMIN SWITCH LOGIC (FIXED) ---
# We use st.session_state.viewing_user to decide WHICH file to load
if st.session_state.username == "admin":
    st.sidebar.subheader("👑 Admin Control")
    all_user_files = [f.stem.replace('_budget', '') for f in Path('.').glob('*_budget.csv')]
    if st.session_state.username not in all_user_files: all_user_files.append(st.session_state.username)
    
    selected = st.sidebar.selectbox("Switch to User View:", all_user_files, index=all_user_files.index(st.session_state.viewing_user))
    if st.sidebar.button("Update View"):
        st.session_state.viewing_user = selected
        st.rerun()

# --- DATA LOAD ---
current_view = st.session_state.viewing_user
budget_file = Path(f'{current_view}_budget.csv')

def load_budget():
    if budget_file.exists():
        return pd.read_csv(budget_file)
    return pd.DataFrame({'Month': months, 'Deposit': [0.0]*12, 'Expense': [0.0]*12, 'Notes': ['']*12})

def save_budget(df):
    df.to_csv(budget_file, index=False)

df = load_budget()

# --- MAIN APP ---
st.title(f"Budget Tracker: {current_view.capitalize()}")
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- EDIT/UPDATE SECTION ---
st.subheader("📝 Edit or Add Data")
with st.form("edit_form"):
    month = st.selectbox("Month to Edit", months)
    # Automatically fill existing data if it exists
    existing_row = df[df['Month'] == month]
    def_dep = float(existing_row['Deposit'].iloc[0]) if not existing_row.empty else 0.0
    def_exp = float(existing_row['Expense'].iloc[0]) if not existing_row.empty else 0.0
    def_note = str(existing_row['Notes'].iloc[0]) if not existing_row.empty else ""

    col1, col2 = st.columns(2)
    dep = col1.number_input("Deposit ($)", value=def_dep)
    exp = col2.number_input("Expense ($)", value=def_exp)
    note = st.text_input("Notes", value=def_note)
    
    if st.form_submit_button("Update Month"):
        df.loc[df['Month'] == month, ['Deposit', 'Expense', 'Notes']] = [dep, exp, note]
        save_budget(df)
        st.success(f"Updated {month}")
        st.rerun()

# --- VISUALS ---
st.divider()
budget_df = df.copy()
budget_df['Monthly_Savings'] = budget_df['Deposit'] - budget_df['Expense']
budget_df['Running_Balance'] = budget_df['Monthly_Savings'].cumsum()

st.subheader("📋 Monthly Overview")
st.dataframe(budget_df, use_container_width=True)

st.subheader("📈 Balance Trend")
st.line_chart(budget_df.set_index('Month')['Running_Balance'])


