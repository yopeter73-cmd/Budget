import streamlit as st
import pandas as pd
from pathlib import Path

budget_file = Path('budget_template.csv')
months = ['Jan', 'Feb', 'March', 'April', 'May', 'June', 'July', 'August', 'Sept', 'Oct', 'Nov', 'Dec']

def check_budget_status(row):
    if row['Expense'] > row['Deposit']:
        return '⚠️ Over Budget'
    elif row['Deposit'] == 0 and row['Expense'] == 0:
        return 'No Data'
    else:
        return '✅ Within Budget'


def compute_budget_metrics(df):
    budget_df = df.copy()
    budget_df['Monthly_Savings'] = budget_df['Deposit'] - budget_df['Expense']
    budget_df['Running_Balance'] = budget_df['Monthly_Savings'].cumsum()
    budget_df['Status'] = budget_df.apply(check_budget_status, axis=1)
    return budget_df[['Month', 'Deposit', 'Expense', 'Monthly_Savings', 'Running_Balance', 'Status', 'Notes']]


def load_budget(path=budget_file):
    if path.exists():
        df = pd.read_csv(path)
        df['Notes'] = df['Notes'].fillna('')
        df['Deposit'] = df['Deposit'].fillna(0.0)
        df['Expense'] = df['Expense'].fillna(0.0)
    else:
        df = pd.DataFrame({
            'Month': months,
            'Deposit': [0.0] * len(months),
            'Expense': [0.0] * len(months),
            'Notes': [''] * len(months)
        })
    return df


def save_budget(df, path=budget_file):
    df.to_csv(path, index=False)


# Load data
df = load_budget()
budget_df = compute_budget_metrics(df)

# Sidebar for quick stats
st.sidebar.title('📊 Quick Stats')
total_deposits = budget_df['Deposit'].sum()
total_expenses = budget_df['Expense'].sum()
total_savings = budget_df['Monthly_Savings'].sum()
final_balance = budget_df['Running_Balance'].iloc[-1] if not budget_df.empty else 0.0

st.sidebar.metric('Total Deposits', f'${total_deposits:.2f}')
st.sidebar.metric('Total Expenses', f'${total_expenses:.2f}')
st.sidebar.metric('Net Savings', f'${total_savings:.2f}')
st.sidebar.metric('Final Balance', f'${final_balance:.2f}')

# Reset button in sidebar
if st.sidebar.button('🔄 Reset Budget'):
    df = pd.DataFrame({
        'Month': months,
        'Deposit': [0.0] * len(months),
        'Expense': [0.0] * len(months),
        'Notes': [''] * len(months)
    })
    save_budget(df)
    st.sidebar.success('Budget reset!')
    st.rerun()

# Main content
st.title('🚗 Car Maintenance Budget Tracker')

# Form in columns for better layout
col1, col2 = st.columns(2)

with col1:
    st.subheader('Add / Update Entry')
    with st.form('budget_form'):
        month = st.selectbox('Select Month', months)
        deposit = st.number_input('Deposit Amount ($)', min_value=0.0, format='%.2f')
        expense = st.number_input('Expense Amount ($)', min_value=0.0, format='%.2f')
        notes = st.text_input('Notes')
        submit = st.form_submit_button('Submit Entry')

with col2:
    st.subheader('Running Balance Chart')
    if not budget_df.empty:
        st.line_chart(budget_df.set_index('Month')['Running_Balance'])
    else:
        st.write('No data to display.')

if submit:
    if month in df['Month'].values:
        df.loc[df['Month'] == month, ['Deposit', 'Expense', 'Notes']] = [deposit, expense, notes]
        st.success(f'Updated entry for {month}!')
    else:
        new_entry = pd.DataFrame([{'Month': month, 'Deposit': deposit, 'Expense': expense, 'Notes': notes}])
        df = pd.concat([df, new_entry], ignore_index=True)
        st.success(f'Added entry for {month}!')

    budget_df = compute_budget_metrics(df)
    save_budget(budget_df)
    st.rerun()

st.header('📋 Monthly Budget Overview')
st.dataframe(budget_df, use_container_width=True)

# Summary section
st.header('💡 Summary')
over_budget_months = budget_df[budget_df['Status'] == '⚠️ Over Budget']['Month'].tolist()
if over_budget_months:
    st.warning(f'Months over budget: {", ".join(over_budget_months)}')
else:
    st.success('All months are within budget or have no data!')

st.info('💡 Tip: Track your deposits and expenses monthly to maintain a positive running balance.')

