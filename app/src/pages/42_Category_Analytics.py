import streamlit as st
import requests
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from modules.nav import SideBarLinks

st.set_page_config(page_title="Category Analytics", page_icon="📊", layout="wide")
SideBarLinks(show_home=True)

st.title("📊 Category Analytics")
st.write("Analyze category performance and trends")

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


def get_category_from_rec(rec):
	return rec.get('category_name', 'Unknown')


# --- Fetch data (direct try/except) ---
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

# Build listing id -> category map
listing_cat_map = {}
for l in listings:
	if 'listingId' in l and 'category_name' in l:
		listing_cat_map[str(l['listingId'])] = l['category_name']


# Prepare transactions DataFrame with parsed dates, amount, and category
rows = []
for t in transactions:
	if 'bookDate' not in t or not t['bookDate']:
		continue
	
	dt = parse_date(t['bookDate'])
	if not dt:
		continue
	
	amt = t.get('paymentAmt')
	cat = t.get('category_name', 'Unknown')
	
	# Fallback to map if no category in transaction
	if not cat or cat == 'Unknown':
		listing_id = t.get('listingId')
		if listing_id:
			cat = listing_cat_map.get(str(listing_id), 'Unknown')
	
	rows.append({'_parsed_date': dt, '_amt': float(amt) if amt is not None else np.nan, '_cat': cat})

if rows:
	df_txn = pd.DataFrame(rows)
	df_txn['_parsed_date'] = pd.to_datetime(df_txn['_parsed_date'], utc=True)
else:
	df_txn = pd.DataFrame(columns=['_parsed_date', '_amt', '_cat'])

# Prepare listings DataFrame for supply counts
rows_l = []
for l in listings:
	cat = l.get('category_name', 'Unknown')
	is_active = l.get('listingStatus') == 'active'
	rows_l.append({'_cat': cat, 'is_active': is_active})

if rows_l:
	df_listings = pd.DataFrame(rows_l)
else:
	df_listings = pd.DataFrame(columns=['_cat', 'is_active'])


# Time windows
now = datetime.now(timezone.utc)
recent_start = now - timedelta(days=30)
prev_start = now - timedelta(days=60)
prev_end = recent_start

# Aggregate transaction value by category for recent and previous windows
df_txn_recent = df_txn[df_txn['_parsed_date'] >= recent_start]
df_txn_prev = df_txn[(df_txn['_parsed_date'] >= prev_start) & (df_txn['_parsed_date'] < prev_end)]

agg_recent = df_txn_recent.groupby('_cat')['_amt'].sum().reset_index().rename(columns={'_amt': 'recent_value'})
agg_prev = df_txn_prev.groupby('_cat')['_amt'].sum().reset_index().rename(columns={'_amt': 'prev_value'})

agg = pd.merge(agg_recent, agg_prev, on='_cat', how='outer').fillna(0)
agg['pct_change'] = agg.apply(lambda r: (round((r['recent_value'] - r['prev_value']) / r['prev_value'] * 100, 1)
										  if r['prev_value'] > 0 else (100.0 if r['recent_value'] > 0 else 0.0)), axis=1)

# Top categories by recent transaction value
top_cats = agg.sort_values('recent_value', ascending=False)

# Supply (active listings) per category
supply = df_listings[df_listings['is_active']].groupby('_cat').size().reset_index(name='supply')
# Demand (transactions count) per category in recent month
demand = df_txn_recent.groupby('_cat').size().reset_index(name='demand')

supply_demand = pd.merge(supply, demand, on='_cat', how='outer').fillna(0)
if not supply_demand.empty:
	supply_demand['_cat'] = supply_demand['_cat'].astype(str)


left, spacer, right = st.columns([1, 0.2, 2])

with left:
	st.subheader('Top Categories (by $ in last 30d)')
	if top_cats.empty:
		st.write('No category transaction data available')
	else:
		top3 = top_cats.head(3)
		for _, row in top3.iterrows():
			cat = row['_cat']
			val = row['recent_value']
			pct = row['pct_change']
			st.metric(f"{cat}", f"${val:,.2f}", f"{pct}% vs prev 30d")
	st.write('')
	if st.button('See more (All categories)', use_container_width=True):
		st.session_state['authenticated'] = True
		st.session_state['role'] = st.session_state.get('role', '')
		st.switch_page('pages/44_All_Catgories_Stats.py')

with right:
	st.subheader('Supply vs Demand (recent 30d)')
	if supply_demand.empty:
		st.write('No supply/demand data available')
	else:
		# choose top N categories by demand+ supply
		supply_demand['score'] = supply_demand['supply'] + supply_demand['demand']
		viz = supply_demand.sort_values('score', ascending=False).head(12)
		viz_m = viz.melt(id_vars=['_cat'], value_vars=['supply', 'demand'], var_name='type', value_name='count')
		chart = alt.Chart(viz_m).mark_bar().encode(
			x=alt.X('count:Q'),
			y=alt.Y('_cat:N', sort='-x'),
			color='type:N',
			tooltip=['_cat:N', 'type:N', 'count:Q']
		).interactive()
		st.altair_chart(chart, use_container_width=True)




