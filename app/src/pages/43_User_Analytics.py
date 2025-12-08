import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks

st.set_page_config(page_title="User Analytics", page_icon="👥", layout="wide")
SideBarLinks(show_home=True)

st.title("👥 User Analytics")
st.write("Analyze user behavior and trends")

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


# --- Fetch data --- (direct try/except style)
try:
	r = requests.get(f"{API_URL}/students")
	students = r.json() if r.status_code == 200 else []
except Exception as e:
	students = []
	st.error(f"Error fetching students: {e}")

try:
	r = requests.get(f"{API_URL}/transactions")
	transactions = r.json() if r.status_code == 200 else []
except Exception as e:
	transactions = []
	st.error(f"Error fetching transactions: {e}")

try:
	r = requests.get(f"{API_URL}/listings")
	listings = r.json() if r.status_code == 200 else []
except Exception as e:
	listings = []
	st.error(f"Error fetching listings: {e}")


# Convert students to DataFrame with parsed join date and campus
def students_to_df(students):
	rows = []
	for s in students:
		if 'joinDate' not in s or not s['joinDate']:
			continue
		dt = parse_date(s['joinDate'])
		if not dt:
			continue
		campus = get_campus(s)
		rows.append({'user_id': s.get('stuId'), '_parsed_date': dt, '_campus': campus, **s})
	if not rows:
		return pd.DataFrame()
	df = pd.DataFrame(rows)
	df['_parsed_date'] = pd.to_datetime(df['_parsed_date'], utc=True)
	return df


def transactions_to_df(transactions):
	rows = []
	for t in transactions:
		if 'bookDate' not in t or not t['bookDate']:
			continue
		dt = parse_date(t['bookDate'])
		if not dt:
			continue
		user_id = t.get('buyerId')
		rows.append({'user_id': user_id, '_parsed_date': dt, **t})
	if not rows:
		return pd.DataFrame()
	df = pd.DataFrame(rows)
	df['_parsed_date'] = pd.to_datetime(df['_parsed_date'], utc=True)
	return df


df_users = students_to_df(students)
df_txn = transactions_to_df(transactions)

# Campus filter
campus_options = set()
for rec in students + listings + transactions:
	c = get_campus(rec)
	if c:
		campus_options.add(c)
campus_options = sorted([c for c in campus_options if c and c != 'Unknown'])
campus_options.insert(0, 'All')

campus = st.sidebar.selectbox('Filter by campus', campus_options)

def apply_campus_filter(df):
	if df.empty:
		return df
	if campus == 'All' or not campus:
		return df
	if '_campus' in df.columns:
		return df[df['_campus'].astype(str).str.lower() == str(campus).lower()]
	return df

df_users = apply_campus_filter(df_users)
df_txn = apply_campus_filter(df_txn)

# Time windows
now = datetime.now(timezone.utc)
recent_start = now - timedelta(days=30)
prev_start = now - timedelta(days=60)
prev_end = recent_start

# --- Metrics ---
# Total users
total_users = len(df_users) if not df_users.empty else len(students) if students else 0

# New users
if df_users.empty:
	new_users_recent = 0
	new_users_prev = 0
else:
	df_users['_parsed_date'] = pd.to_datetime(df_users['_parsed_date'], utc=True)
	new_users_recent = df_users[df_users['_parsed_date'] >= recent_start].shape[0]
	new_users_prev = df_users[(df_users['_parsed_date'] >= prev_start) & (df_users['_parsed_date'] < prev_end)].shape[0]

pct_change_new_users = (round((new_users_recent - new_users_prev) / new_users_prev * 100, 1)
						if new_users_prev > 0 else (100.0 if new_users_recent > 0 else 0.0))

# Active users = users with a transaction in recent 30d
if df_txn.empty:
	active_recent = 0
	active_prev = 0
else:
	df_txn['_parsed_date'] = pd.to_datetime(df_txn['_parsed_date'], utc=True)
	txn_recent = df_txn[df_txn['_parsed_date'] >= recent_start]
	txn_prev = df_txn[(df_txn['_parsed_date'] >= prev_start) & (df_txn['_parsed_date'] < prev_end)]
	active_recent = txn_recent['user_id'].dropna().nunique() if not txn_recent.empty else 0
	active_prev = txn_prev['user_id'].dropna().nunique() if not txn_prev.empty else 0

pct_change_active = (round((active_recent - active_prev) / active_prev * 100, 1)
					 if active_prev > 0 else (100.0 if active_recent > 0 else 0.0))

# Avg transactions per active user (recent)
if df_txn.empty or active_recent == 0:
	avg_tx_per_user = 0.0
	pct_change_avg_tx_user = 0.0
else:
	txns_recent = df_txn[df_txn['_parsed_date'] >= recent_start]
	txns_prev = df_txn[(df_txn['_parsed_date'] >= prev_start) & (df_txn['_parsed_date'] < prev_end)]
	tx_per_user_recent = txns_recent.groupby('user_id').size().mean() if not txns_recent.empty else 0.0
	tx_per_user_prev = txns_prev.groupby('user_id').size().mean() if not txns_prev.empty else 0.0
	avg_tx_per_user = round(tx_per_user_recent, 2)
	if tx_per_user_prev and tx_per_user_prev > 0:
		pct_change_avg_tx_user = round((tx_per_user_recent - tx_per_user_prev) / tx_per_user_prev * 100, 1)
	else:
		pct_change_avg_tx_user = 100.0 if tx_per_user_recent > 0 else 0.0

# --- Display top metrics ---
col1, col2, col3 = st.columns(3)
with col1:
	st.metric('Total Users', total_users)
	st.caption('Total registered users (filtered)')
with col2:
	st.metric('New Users (30d)', new_users_recent, f"{pct_change_new_users}% vs prev 30d")
	st.caption('Signups in the last 30 days')
with col3:
	st.metric('Active Users (30d)', active_recent, f"{pct_change_active}% vs prev 30d")
	st.caption('Users with >=1 transaction in last 30 days')

st.divider()

# Debug info
with st.expander("Debug Info"):
	st.write(f"Total transactions loaded: {len(df_txn)}")
	st.write(f"Transaction columns: {list(df_txn.columns) if not df_txn.empty else 'N/A'}")
	if not df_txn.empty:
		st.write(f"Sample transaction data:")
		st.dataframe(df_txn[['user_id', '_parsed_date', 'buyerId']].head(3) if 'buyerId' in df_txn.columns else df_txn[['user_id', '_parsed_date']].head(3))
	st.write(f"Users in recent 30d with transactions: {active_recent}")
	st.write(f"Total users loaded: {len(df_users)}")
	if not df_users.empty:
		st.write(f"Sample user data:")
		st.dataframe(df_users[['user_id', 'stuId', '_parsed_date']].head(3))

# --- Charts ---
st.subheader('User Trends')

def cumulative_series(df, date_col='_parsed_date'):
	if df.empty:
		return pd.DataFrame()
	s = df.copy()
	s['date'] = pd.to_datetime(s[date_col]).dt.date
	counts = s.groupby('date').size().rename('count').reset_index()
	# guard: if counts is empty or start date is NaT, try to fall back to df min date
	if counts.empty:
		return pd.DataFrame()
	start_date = counts['date'].min()
	if pd.isna(start_date):
		min_dt = pd.to_datetime(df[date_col]).min()
		if pd.isna(min_dt):
			return pd.DataFrame()
		start_date = min_dt.date()
	end_date = datetime.now(timezone.utc).date()
	if start_date > end_date:
		start_date = end_date
	idx = pd.date_range(start=start_date, end=end_date, freq='D')
	counts['date'] = pd.to_datetime(counts['date'])
	counts = counts.set_index('date').reindex(idx, fill_value=0).rename_axis('date').reset_index()
	counts['cumulative'] = counts['count'].cumsum()
	return counts

users_cum = cumulative_series(df_users) if not df_users.empty else pd.DataFrame()
txns_cum = cumulative_series(df_txn) if not df_txn.empty else pd.DataFrame()

left, right = st.columns(2)
with left:
	st.subheader('Cumulative New Users')
	if users_cum.empty:
		st.write('No user signup data to show')
	else:
		chart = alt.Chart(users_cum).mark_line().encode(
			x='date:T', y='cumulative:Q', tooltip=['date:T', 'cumulative:Q']
		).interactive()
		st.altair_chart(chart, use_container_width=True)

with right:
	st.subheader('Cumulative Transactions')
	if txns_cum.empty:
		st.write('No transaction data to show')
	else:
		chart = alt.Chart(txns_cum).mark_line(color='#2b8cbe').encode(
			x='date:T', y='cumulative:Q', tooltip=['date:T', 'cumulative:Q']
		).interactive()
		st.altair_chart(chart, use_container_width=True)

st.divider()

st.subheader('User Breakdown')
cols = st.columns(2)
with cols[0]:
	# Users by campus
	if df_users.empty:
		st.write('No user data')
	else:
		by_campus = df_users.groupby('_campus').size().reset_index(name='users')
		bar = alt.Chart(by_campus).mark_bar().encode(
			x='users:Q', y=alt.Y('_campus:N', sort='-x'), tooltip=['_campus:N', 'users:Q']
		)
		st.altair_chart(bar, use_container_width=True)

with cols[1]:
	# Transactions per user distribution (recent)
	if df_txn.empty:
		st.write('No transaction data')
	else:
		txns_recent = df_txn[df_txn['_parsed_date'] >= recent_start]
		txs_per_user = txns_recent.groupby('user_id').size().reset_index(name='tx_count')
		if txs_per_user.empty:
			st.write('No recent transactions')
		else:
			hist = alt.Chart(txs_per_user).mark_bar().encode(
				x=alt.X('tx_count:Q', bin=alt.Bin(maxbins=20)),
				y='count()',
				tooltip=[alt.Tooltip('count()', title='users'), 'tx_count']
			)
			st.altair_chart(hist, use_container_width=True)
