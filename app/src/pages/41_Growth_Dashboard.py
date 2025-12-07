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
		pass
	# Try ISO format
	try:
		if isinstance(val, str) and val.endswith('Z'):
			val = val.replace('Z', '+00:00')
		return datetime.fromisoformat(val)
	except Exception:
		return None


def find_date_in_record(rec, candidates=('createdAt', 'created_at', 'joinedAt', 'lastUpdate', 'last_update')):
	for k in candidates:
		if k in rec and rec[k]:
			return parse_date(rec[k])
	return None


def get_campus(rec):
	for k in ('campus', 'campusName', 'campus_id', 'campusId', 'campus_name'):
		if k in rec and rec[k]:
			return rec[k]
	return 'Unknown'

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
def records_to_df(records, date_field_candidates=('createdAt', 'created_at', 'joinedAt', 'lastUpdate')):
	rows = []
	for r in records:
		dt = find_date_in_record(r, date_field_candidates)
		if not dt:
			continue
		campus_val = get_campus(r)
		rows.append({**r, '_parsed_date': dt, '_campus': campus_val})
	if not rows:
		return pd.DataFrame()
	df = pd.DataFrame(rows)
	# normalize tz-awareness
	if pd.api.types.is_datetime64_any_dtype(df['_parsed_date']):
		df['_parsed_date'] = pd.to_datetime(df['_parsed_date'])
	else:
		df['_parsed_date'] = df['_parsed_date'].apply(lambda x: x if isinstance(x, datetime) else parse_date(x))
	return df

df_users = records_to_df(students, ('createdAt', 'created_at', 'joinedAt'))
df_listings = records_to_df(listings, ('lastUpdate', 'last_update', 'createdAt'))
df_txn = records_to_df(transactions, ('createdAt', 'created_at'))

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
def scan_for_any_date(rec):
	# try known date fields first
	dt = find_date_in_record(rec, ('createdAt', 'created_at', 'joinedAt', 'signup_date', 'registeredAt', 'date_joined', 'created'))
	if dt:
		return dt
	# otherwise scan all string values and try parsing
	for v in rec.values():
		if isinstance(v, str):
			try:
				d = parse_date(v)
				if d:
					return d
			except Exception:
				continue
	return None

if df_users.empty or '_parsed_date' not in df_users.columns:
	# Fallback: count directly from raw JSON, respecting campus filter
	if not students:
		total_users = 0
		new_users_recent = 0
		new_users_prev = 0
		pct_change_users = 0.0
	else:
		# apply campus filter manually
		if campus == 'All' or not campus:
			students_filtered = students
		else:
			students_filtered = [s for s in students if str(get_campus(s)).lower() == str(campus).lower()]
		total_users = len(students_filtered)
		new_users_recent = 0
		new_users_prev = 0
		for s in students_filtered:
			dt = scan_for_any_date(s)
			if not dt:
				continue
			# ensure tz-aware
			if dt.tzinfo is None:
				dt = dt.replace(tzinfo=timezone.utc)
			if dt >= recent_start:
				new_users_recent += 1
			elif prev_start <= dt < prev_end:
				new_users_prev += 1
		pct_change_users = (round((new_users_recent - new_users_prev) / new_users_prev * 100, 1)
							if new_users_prev > 0 else (100.0 if new_users_recent > 0 and new_users_prev == 0 else 0.0))
else:
	total_users = len(df_users)
	df_users['_parsed_date'] = pd.to_datetime(df_users['_parsed_date'], utc=True)
	users_recent = df_users[df_users['_parsed_date'] >= recent_start]
	users_prev = df_users[(df_users['_parsed_date'] >= prev_start) & (df_users['_parsed_date'] < prev_end)]
	new_users_recent = len(users_recent)
	new_users_prev = len(users_prev)
	pct_change_users = (round((new_users_recent - new_users_prev) / new_users_prev * 100, 1)
						if new_users_prev > 0 else (100.0 if new_users_recent > 0 and new_users_prev == 0 else 0.0))

# Listings (active)
def listing_is_active(r):
	for k in ('active', 'isActive', 'status'):
		if k in r:
			val = r.get(k)
			if isinstance(val, bool):
				return val
			if isinstance(val, str) and val.lower() in ('active', 'available', 'true', '1'):
				return True
	# fallback: treat listing as active
	return True

if df_listings.empty or '_parsed_date' not in df_listings.columns:
	df_active = pd.DataFrame()
else:
	df_listings['_parsed_date'] = pd.to_datetime(df_listings['_parsed_date'], utc=True)
	df_listings['is_active'] = df_listings.apply(lambda row: listing_is_active(row.to_dict()), axis=1)
	df_active = df_listings[df_listings['is_active']]

total_active_listings = len(df_active)
if df_active.empty or '_parsed_date' not in df_active.columns:
	new_active_recent = 0
	new_active_prev = 0
	pct_change_active = 0.0
else:
	active_recent = df_active[df_active['_parsed_date'] >= recent_start]
	active_prev = df_active[(df_active['_parsed_date'] >= prev_start) & (df_active['_parsed_date'] < prev_end)]
	new_active_recent = len(active_recent)
	new_active_prev = len(active_prev)
	pct_change_active = (round((new_active_recent - new_active_prev) / new_active_prev * 100, 1)
						 if new_active_prev > 0 else (100.0 if new_active_recent > 0 and new_active_prev == 0 else 0.0))

# Transactions: average value
def find_amount_field_in_df(df):
	# scan columns first
	for candidate in ('amount', 'total', 'price', 'value', 'amount_cents'):
		if candidate in df.columns:
			return candidate
	# scan rows for any key
	for _, row in df.iterrows():
		for candidate in ('amount', 'total', 'price', 'value', 'amount_cents'):
			if candidate in row and pd.notna(row[candidate]):
				return candidate
	return None

avg_tx_all = 'N/A'
pct_change_avg_tx = 'N/A'
if not df_txn.empty and '_parsed_date' in df_txn.columns:
	df_txn['_parsed_date'] = pd.to_datetime(df_txn['_parsed_date'], utc=True)
	amt_field = find_amount_field_in_df(df_txn)
	if amt_field:
		# ensure numeric
		df_txn['_amt'] = pd.to_numeric(df_txn[amt_field], errors='coerce')
		avg_recent = df_txn[df_txn['_parsed_date'] >= recent_start]['_amt'].mean()
		avg_prev = df_txn[(df_txn['_parsed_date'] >= prev_start) & (df_txn['_parsed_date'] < prev_end)]['_amt'].mean()
		avg_all = df_txn['_amt'].mean()
		if np.isnan(avg_all):
			avg_tx_all = 'N/A'
		else:
			avg_tx_all = f"${avg_all:,.2f}"
		if avg_prev and not np.isnan(avg_prev):
			pct_change_avg_tx = f"{round((avg_recent - avg_prev) / avg_prev * 100,1)}%"
		else:
			pct_change_avg_tx = f"{100.0 if avg_recent and not np.isnan(avg_recent) else 0.0}%"

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

