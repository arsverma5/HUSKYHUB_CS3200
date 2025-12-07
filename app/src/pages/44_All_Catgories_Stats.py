import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks

st.set_page_config(page_title="All Categories Stats", page_icon="📋", layout="wide")
SideBarLinks(show_home=True)

st.title("All Categories — Full Stats")
st.write("Comprehensive category-level statistics and export")

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
	try:
		if isinstance(val, str) and val.endswith('Z'):
			val = val.replace('Z', '+00:00')
		return datetime.fromisoformat(val)
	except Exception:
		return None


def get_category_from_rec(rec):
	for k in ('category', 'categoryName', 'category_name', 'category_id', 'cat'):
		if k in rec and rec[k]:
			return rec[k]
	return 'Unknown'


def find_amount(rec):
	for k in ('amount', 'total', 'price', 'value', 'amount_cents'):
		if k in rec and rec[k] is not None:
			return rec[k]
	return None


# Fetch data
try:
	r = requests.get(f"{API_URL}/listings")
	listings = r.json() if r.status_code == 200 else []
except Exception as e:
	listings = []
	st.error(f"Error fetching listings: {e}")

try:
	r = requests.get(f"{API_URL}/transactions")
	transactions = r.json() if r.status_code == 200 else []
except Exception as e:
	transactions = []
	st.error(f"Error fetching transactions: {e}")

# Build listing id -> category map
listing_cat_map = {}
for l in listings:
	lid = None
	for k in ('id', 'listingId', 'listing_id'):
		if k in l and l[k] is not None:
			lid = l[k]
			break
	cat = get_category_from_rec(l) or 'Unknown'
	if lid is not None:
		listing_cat_map[str(lid)] = cat

# Prepare transaction rows
rows = []
for t in transactions:
	dt = None
	for k in ('createdAt', 'created_at', 'timestamp'):
		if k in t and t[k]:
			dt = parse_date(t[k])
			break
	if not dt:
		for v in t.values():
			if isinstance(v, str):
				dt = parse_date(v)
				if dt:
					break
	amt = find_amount(t)
	cat = get_category_from_rec(t) or None
	if not cat:
		for k in ('listingId', 'listing_id', 'listing'):
			if k in t and t[k] is not None:
				cat = listing_cat_map.get(str(t[k]), None)
				if cat:
					break
	rows.append({'date': dt, 'amt': float(amt) if amt is not None else np.nan, 'cat': cat or 'Unknown'})

if rows:
	df_txn = pd.DataFrame(rows)
	df_txn['date'] = pd.to_datetime(df_txn['date'], utc=True)
else:
	df_txn = pd.DataFrame(columns=['date', 'amt', 'cat'])

# Prepare listings stats
rows_l = []
for l in listings:
	cat = get_category_from_rec(l) or 'Unknown'
	is_active = False
	for k in ('active', 'isActive', 'status'):
		if k in l:
			v = l.get(k)
			if isinstance(v, bool):
				is_active = v
			elif isinstance(v, str) and v.lower() in ('active', 'available', 'true', '1'):
				is_active = True
	rows_l.append({'cat': cat, 'is_active': is_active})

if rows_l:
	df_listings = pd.DataFrame(rows_l)
else:
	df_listings = pd.DataFrame(columns=['cat', 'is_active'])


# UI: optional campus filter (if dataset includes campus field)
campus_options = ['All']
# detect campus values
for rec in (listings + transactions):
	for k in ('campus', 'campusName', 'campus_id'):
		if k in rec and rec[k]:
			v = rec[k]
			if v not in campus_options:
				campus_options.append(v)

campus = st.sidebar.selectbox('Filter by campus', campus_options)

if campus != 'All':
	# try to filter by campus fields in transactions/listings
	def has_campus(rec):
		for k in ('campus', 'campusName', 'campus_id', 'campusId'):
			if k in rec and rec[k]:
				return str(rec[k]).lower() == str(campus).lower()
		return False
	transactions = [t for t in transactions if has_campus(t)]
	listings = [l for l in listings if has_campus(l)]
	# rebuild derived frames
	# transactions
	rows = []
	for t in transactions:
		dt = None
		for k in ('createdAt', 'created_at', 'timestamp'):
			if k in t and t[k]:
				dt = parse_date(t[k])
				break
		if not dt:
			for v in t.values():
				if isinstance(v, str):
					dt = parse_date(v)
					if dt:
						break
		amt = find_amount(t)
		cat = get_category_from_rec(t) or None
		if not cat:
			for k in ('listingId', 'listing_id', 'listing'):
				if k in t and t[k] is not None:
					cat = listing_cat_map.get(str(t[k]), None)
					if cat:
						break
		rows.append({'date': dt, 'amt': float(amt) if amt is not None else np.nan, 'cat': cat or 'Unknown'})
	df_txn = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['date','amt','cat'])
	if not df_txn.empty:
		df_txn['date'] = pd.to_datetime(df_txn['date'], utc=True)
	# listings
	rows_l = []
	for l in listings:
		cat = get_category_from_rec(l) or 'Unknown'
		is_active = False
		for k in ('active', 'isActive', 'status'):
			if k in l:
				v = l.get(k)
				if isinstance(v, bool):
					is_active = v
				elif isinstance(v, str) and v.lower() in ('active', 'available', 'true', '1'):
					is_active = True
		rows_l.append({'cat': cat, 'is_active': is_active})
	df_listings = pd.DataFrame(rows_l) if rows_l else pd.DataFrame(columns=['cat','is_active'])

# Time windows
now = datetime.now(timezone.utc)
recent_start = now - timedelta(days=30)
prev_start = now - timedelta(days=60)
prev_end = recent_start

# Aggregations per category
df_txn_recent = pd.DataFrame(columns=['date','amt','cat'])
df_txn_prev = pd.DataFrame(columns=['date','amt','cat'])
if not df_txn.empty:
	df_txn_recent = df_txn[df_txn['date'] >= recent_start]
	df_txn_prev = df_txn[(df_txn['date'] >= prev_start) & (df_txn['date'] < prev_end)]
	agg_recent = df_txn_recent.groupby('cat')['amt'].sum().reset_index().rename(columns={'amt':'recent_value'})
	agg_prev = df_txn_prev.groupby('cat')['amt'].sum().reset_index().rename(columns={'amt':'prev_value'})
else:
	agg_recent = pd.DataFrame(columns=['cat','recent_value'])
	agg_prev = pd.DataFrame(columns=['cat','prev_value'])

agg = pd.merge(agg_recent, agg_prev, on='cat', how='outer').fillna(0)
if not agg.empty:
	agg['pct_change'] = agg.apply(lambda r: (round((r['recent_value'] - r['prev_value']) / r['prev_value'] * 100,1)
											  if r['prev_value'] > 0 else (100.0 if r['recent_value'] > 0 else 0.0)), axis=1)
else:
	agg['pct_change'] = []

supply = df_listings[df_listings['is_active']].groupby('cat').size().reset_index(name='supply') if not df_listings.empty else pd.DataFrame(columns=['cat','supply'])
demand = df_txn_recent.groupby('cat').size().reset_index(name='demand') if not df_txn.empty else pd.DataFrame(columns=['cat','demand'])

all_stats = pd.merge(agg, supply, on='cat', how='outer').merge(demand, on='cat', how='outer').fillna(0)
if not all_stats.empty:
	all_stats['avg_tx'] = all_stats.apply(lambda r: (r['recent_value'] / r['demand']) if r['demand'] > 0 else 0.0, axis=1)

# Display table
st.subheader('All Categories — Metrics')
if all_stats.empty:
	st.write('No category stats available')
else:
	all_stats = all_stats.sort_values('recent_value', ascending=False)
	st.dataframe(all_stats.style.format({
		'recent_value':'${:,.2f}',
		'prev_value':'${:,.2f}',
		'pct_change':'{:.1f}%',
		'avg_tx':'${:,.2f}'
	}))

	csv = all_stats.to_csv(index=False)
	st.download_button('Download CSV', data=csv, file_name='all_categories_stats.csv', mime='text/csv')

st.write('')
st.write('Back to ')
if st.button('Category Analytics Overview'):
	st.session_state['authenticated'] = True
	st.session_state['role'] = st.session_state.get('role','')
	st.switch_page('pages/42_Category_Analytics.py')