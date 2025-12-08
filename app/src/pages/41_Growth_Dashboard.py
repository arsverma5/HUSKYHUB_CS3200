import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks

st.set_page_config(page_title="Growth Dashboard", page_icon="📈", layout="wide")
SideBarLinks(show_home=True)

st.title("📈 Growth Dashboard")
st.write("Analyze growth metrics and trends")

# API URL
API_URL = "http://web-api:4000"


def parse_date(val):
	if not val:
		return None
	try:
		dt = parsedate_to_datetime(val)
		if dt.tzinfo is None:
			return dt.replace(tzinfo=timezone.utc)
		return dt
	except Exception:
		return None


def get_campus(rec):
	return rec.get('campus', 'Unknown')

# Fetch data from APIs
try:
	response = requests.get(f"{API_URL}/students")
	if response.status_code == 200:
		students = response.json()
	else:
		students = []
except Exception as e:
	students = []
	st.error(f"Error fetching students: {e}")

try:
	response = requests.get(f"{API_URL}/listings")
	if response.status_code == 200:
		listings = response.json()
	else:
		listings = []
except Exception as e:
	listings = []
	st.error(f"Error fetching listings: {e}")

try:
	response = requests.get(f"{API_URL}/transactions")
	if response.status_code == 200:
		transactions = response.json()
	else:
		transactions = []
except Exception as e:
	transactions = []
	st.error(f"Error fetching transactions: {e}")

# Determine campus options
campus_options = set()
for rec in students + listings + transactions:
	c = get_campus(rec)
	if c:
		campus_options.add(c)
campus_options = sorted([c for c in campus_options if c and c != 'Unknown'])
campus_options.insert(0, 'All')

# Campus filter
campus = st.sidebar.selectbox('Filter by campus', campus_options)

# Convert lists to DataFrames with parsed dates and campus
def records_to_df(records, date_field):
	rows = []
	for r in records:
		if date_field not in r or not r[date_field]:
			continue
		dt = parse_date(r[date_field])
		if not dt:
			continue
		campus_val = get_campus(r)
		rows.append({**r, '_parsed_date': dt, '_campus': campus_val})
	
	if not rows:
		return pd.DataFrame()
	
	df = pd.DataFrame(rows)
	df['_parsed_date'] = pd.to_datetime(df['_parsed_date'], utc=True)
	return df

df_users = records_to_df(students, 'joinDate')
df_listings = records_to_df(listings, 'lastUpdate')
df_txn = records_to_df(transactions, 'bookDate')

# Apply campus filter if selected
def apply_campus_filter(df):
	if df.empty:
		return df
	if campus == 'All' or not campus:
		return df
	mask = df['_campus'].astype(str).str.lower() == str(campus).lower()
	return df[mask]

df_users = apply_campus_filter(df_users)
df_listings = apply_campus_filter(df_listings)
df_txn = apply_campus_filter(df_txn)

# Helper to get month windows
now = datetime.now(timezone.utc)
recent_start = now - timedelta(days=30)
prev_start = now - timedelta(days=60)
prev_end = recent_start

# --- Top metrics calculations ---
# Users
if df_users.empty:
	total_users = 0
	new_users_recent = 0
	new_users_prev = 0
	pct_change_users = 0.0
else:
	total_users = len(df_users)
	users_recent = df_users[df_users['_parsed_date'] >= recent_start]
	users_prev = df_users[(df_users['_parsed_date'] >= prev_start) & (df_users['_parsed_date'] < prev_end)]
	new_users_recent = len(users_recent)
	new_users_prev = len(users_prev)
	pct_change_users = (round((new_users_recent - new_users_prev) / new_users_prev * 100, 1)
						if new_users_prev > 0 else (100.0 if new_users_recent > 0 else 0.0))

# Listings (active)
if df_listings.empty:
	df_active = pd.DataFrame()
	total_active_listings = 0
	new_active_recent = 0
	new_active_prev = 0
	pct_change_active = 0.0
else:
	df_active = df_listings[df_listings['listingStatus'] == 'active']
	total_active_listings = len(df_active)
	
	if df_active.empty:
		new_active_recent = 0
		new_active_prev = 0
		pct_change_active = 0.0
	else:
		active_recent = df_active[df_active['_parsed_date'] >= recent_start]
		active_prev = df_active[(df_active['_parsed_date'] >= prev_start) & (df_active['_parsed_date'] < prev_end)]
		new_active_recent = len(active_recent)
		new_active_prev = len(active_prev)
		pct_change_active = (round((new_active_recent - new_active_prev) / new_active_prev * 100, 1)
							 if new_active_prev > 0 else (100.0 if new_active_recent > 0 else 0.0))

# Transactions: average value
avg_tx_all = 'N/A'
pct_change_avg_tx = 'N/A'

if not df_txn.empty:
	df_txn['_amt'] = pd.to_numeric(df_txn['paymentAmt'], errors='coerce')
	avg_recent = df_txn[df_txn['_parsed_date'] >= recent_start]['_amt'].mean()
	avg_prev = df_txn[(df_txn['_parsed_date'] >= prev_start) & (df_txn['_parsed_date'] < prev_end)]['_amt'].mean()
	avg_all = df_txn['_amt'].mean()
	
	if not np.isnan(avg_all):
		avg_tx_all = f"${avg_all:,.2f}"
	
	if not np.isnan(avg_prev):
		pct_change_avg_tx = f"{round((avg_recent - avg_prev) / avg_prev * 100, 1)}%"
	else:
		pct_change_avg_tx = f"{100.0 if not np.isnan(avg_recent) else 0.0}%"

# --- Display top metrics ---
col1, col2, col3 = st.columns(3)
with col1:
	st.metric("Total Users", total_users, f"{pct_change_users}% in last 30d")
with col2:
	st.metric("Active Listings", total_active_listings, f"{pct_change_active}% in last 30d")
with col3:
	st.metric("Avg Transaction Value", avg_tx_all, pct_change_avg_tx)

# --- Time series charts ---
st.divider()
st.subheader("Trends Over Time")

def cumulative_series(df, date_col='_parsed_date', freq='D'):
	if df.empty:
		return pd.DataFrame()
	s = df.copy()
	s['date'] = pd.to_datetime(s[date_col]).dt.date
	counts = s.groupby('date').size().rename('count').reset_index()
	# create full date range
	idx = pd.date_range(start=counts['date'].min(), end=datetime.now(timezone.utc).date(), freq=freq)
	counts['date'] = pd.to_datetime(counts['date'])
	counts = counts.set_index('date').reindex(idx, fill_value=0).rename_axis('date').reset_index()
	counts['cumulative'] = counts['count'].cumsum()
	return counts

users_cum = cumulative_series(df_users)
txns_cum = cumulative_series(df_txn)
listings_counts = cumulative_series(df_listings)

# Plotting helpers
def line_chart(df, y='cumulative', title=''):
	if df.empty:
		st.write(f"No data for {title}")
		return
	chart = alt.Chart(df).mark_line().encode(
		x='date:T',
		y=alt.Y(y+':Q', title=title),
		tooltip=['date:T', alt.Tooltip(y+':Q')]
	).interactive()
	st.altair_chart(chart, use_container_width=True)

st.subheader('Cumulative New Users Over Time')
line_chart(users_cum, 'cumulative', 'Cumulative Users')

st.subheader('Cumulative Transactions Over Time')
line_chart(txns_cum, 'cumulative', 'Cumulative Transactions')

st.subheader('Listings Over Time')
line_chart(listings_counts, 'count', 'Listings per Day')

