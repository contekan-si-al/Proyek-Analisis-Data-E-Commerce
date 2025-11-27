import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import requests
from io import StringIO

# -----------------------------
# GitHub URLs for all datasets
# -----------------------------
BASE = "https://media.githubusercontent.com/media/contekan-si-al/Proyek-Analisis-Data-E-Commerce/main/data/"

DATASETS = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "product_category_translation": "product_category_name_translation.csv",
}

# -----------------------------
# Function to download CSV
# -----------------------------
@st.cache_data(show_spinner=True)
def load_csv(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return pd.read_csv(StringIO(resp.text), encoding="utf-8-sig")


# -----------------------------
# Load all datasets
# -----------------------------
st.title("📦 Olist E-Commerce Dashboard")

dfs = {}
with st.spinner("Mengunduh seluruh dataset dari GitHub..."):
    for key, filename in DATASETS.items():
        dfs[key] = load_csv(BASE + filename)

st.success("Semua dataset berhasil dimuat!")

# Unpack datasets
df_customers = dfs["customers"]
df_geolocation = dfs["geolocation"]
df_order_items = dfs["order_items"]
df_order_payments = dfs["order_payments"]
df_order_reviews = dfs["order_reviews"]
df_orders = dfs["orders"]
df_products = dfs["products"]
df_sellers = dfs["sellers"]
df_product_category_name_translation = dfs["product_category_translation"]

# -----------------------------
# Data Cleaning (from the script)
# -----------------------------
# Convert columns to datetime
df_order_items['shipping_limit_date'] = pd.to_datetime(df_order_items['shipping_limit_date'])
df_order_reviews['review_creation_date'] = pd.to_datetime(df_order_reviews['review_creation_date'])
df_order_reviews['review_answer_timestamp'] = pd.to_datetime(df_order_reviews['review_answer_timestamp'])
df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'])
df_orders['order_approved_at'] = pd.to_datetime(df_orders['order_approved_at'])
df_orders['order_delivered_carrier_date'] = pd.to_datetime(df_orders['order_delivered_carrier_date'])
df_orders['order_delivered_customer_date'] = pd.to_datetime(df_orders['order_delivered_customer_date'])
df_orders['order_estimated_delivery_date'] = pd.to_datetime(df_orders['order_estimated_delivery_date'])

# Create total_value column
df_order_items["total_value"] = df_order_items["price"] + df_order_items["freight_value"]

df_order_items_ = df_order_items.groupby(by=["order_id", "product_id", "shipping_limit_date"]).agg(
    product_counts = ("product_id", "count"),
    total_price = ("price", "sum"),
    total_value = ("total_value", "sum")
).reset_index()

# Handle missing values in df_order_reviews
df_order_reviews['review_comment_title'].fillna('no comment', inplace=True)
df_order_reviews['review_comment_message'].fillna('no comment', inplace=True)

# Handle missing values in df_products
df_products['product_category_name'].fillna('unknown', inplace=True)
numerical_cols_to_fill_products = [
    'product_name_lenght', 'product_description_lenght', 'product_photos_qty',
    'product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm'
]
for col in numerical_cols_to_fill_products:
    df_products[col].fillna(df_products[col].median(), inplace=True)

# Handle missing values in df_orders
df_orders['order_approved_at'].fillna(df_orders['order_purchase_timestamp'], inplace=True)
df_orders['order_delivered_carrier_date'].fillna(df_orders['order_approved_at'], inplace=True)
df_orders['order_delivered_customer_date'].fillna(df_orders['order_delivered_carrier_date'], inplace=True)

# -----------------------------
# Interactive Filtering
# -----------------------------
st.header("Filter Data")

# Date range filter
min_date = df_orders['order_purchase_timestamp'].min().date()
max_date = df_orders['order_purchase_timestamp'].max().date()
date_range = st.date_input("Pilih Rentang Tanggal Pembelian", [min_date, max_date], min_value=min_date, max_value=max_date)

# State filter (multiselect)
unique_states = sorted(df_customers['customer_state'].unique())
selected_states = st.multiselect("Pilih Negara Bagian (State)", unique_states, default=unique_states)

# City filter (multiselect, based on selected states)
filtered_customers = df_customers[df_customers['customer_state'].isin(selected_states)]
unique_cities = sorted(filtered_customers['customer_city'].unique())
selected_cities = st.multiselect("Pilih Kota (City)", unique_cities, default=unique_cities)

# Apply filters to main datasets
@st.cache_data
def get_filtered_data(date_range, selected_states, selected_cities):
    filtered_orders = df_orders[
        (df_orders['order_purchase_timestamp'].dt.date >= date_range[0]) &
        (df_orders['order_purchase_timestamp'].dt.date <= date_range[1])
    ]

    filtered_customers = df_customers[
        (df_customers['customer_state'].isin(selected_states)) &
        (df_customers['customer_city'].isin(selected_cities))
    ]

    # Merge filtered customers with orders to apply location filters
    filtered_orders = filtered_orders.merge(filtered_customers[['customer_id', 'customer_city', 'customer_state']], on='customer_id', how='inner')

    # Filter other datasets based on filtered_orders
    filtered_order_ids = filtered_orders['order_id'].unique()
    filtered_order_items = df_order_items[df_order_items['order_id'].isin(filtered_order_ids)]
    filtered_order_payments = df_order_payments[df_order_payments['order_id'].isin(filtered_order_ids)]
    filtered_order_reviews = df_order_reviews[df_order_reviews['order_id'].isin(filtered_order_ids)]

    return filtered_orders, filtered_order_items, filtered_order_payments, filtered_order_reviews

filtered_orders, filtered_order_items, filtered_order_payments, filtered_order_reviews = get_filtered_data(date_range, selected_states, selected_cities)

# -----------------------------
# EDA and Visualizations (adapted with filters)
# -----------------------------
st.header("Analisis Pelanggan")

# Geo data preparation (adapted)
data_geo = (
    df_geolocation
        .sort_values(by="geolocation_zip_code_prefix", ascending=True)
        .groupby(by=["geolocation_city", "geolocation_state"])
        .head(1)
)

data_customers_filtered = (
    filtered_orders.merge(filtered_order_items, how="inner", on="order_id")
        .query('order_status == "delivered"')
        .groupby(by=["customer_city", "customer_state"])
        .agg(
            orders_count=("order_id", "nunique"),
            total_value=("total_value", "sum")
        )
        .sort_values(by="orders_count", ascending=False)
        .merge(
            data_geo,
            how="inner",
            left_on=["customer_city", "customer_state"],
            right_on=["geolocation_city", "geolocation_state"]
        )
)

data_customers_filtered["location"] = (
    data_customers_filtered["geolocation_city"].apply(lambda x: str(x).title())
    + ", "
    + data_customers_filtered["geolocation_state"]
)

# Top N Sales by Geoloc with slider
st.subheader("Top N Penjualan Berdasarkan Geolokasi")
top_n_geo = st.slider("Pilih Jumlah Top Lokasi", min_value=5, max_value=50, value=10, step=5)
top_n = data_customers_filtered.head(top_n_geo).copy()
if not top_n.empty:
    max_orders = top_n["orders_count"].max() if not top_n["orders_count"].isna().all() else 0

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=top_n["location"],
            y=top_n["orders_count"],
            name="Jumlah Pesanan",
            marker_color="rgb(64,224,208)",
            hovertemplate="%{x}<br>Jumlah Pesanan: %{y}"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=top_n["location"],
            y=top_n["total_value"],
            name="GMV",
            yaxis="y2",
            marker_color="rgb(255,160,122)",
            mode="lines+markers",
        )
    )

    fig.update_layout(
        title=dict(
            text=f"<b>Top {top_n_geo} Penjualan Berdasarkan Geolokasi<b>",
            font=dict(size=12, family="Arial", color="black")
        ),
        plot_bgcolor="white",
        yaxis=dict(
            side="left",
            range=[0, max_orders + 1000],
            showgrid=False,
            zeroline=True,
            showline=False,
            showticklabels=True
        ),
        yaxis2=dict(
            side="right",
            overlaying="y",
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=True
        ),
        xaxis=dict(showline=True, linecolor="rgb(204, 204, 204)", linewidth=2),
        legend=dict(orientation="h", x=0.8, y=1.1),
        annotations=[
            dict(
                text="Created By AL.",
                xref="paper", yref="paper",
                x=1, y=-.35,
                showarrow=False,
                font=dict(size=10, color="gray", family="Arial")
            )
        ],
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.write("Tidak ada data yang tersedia untuk filter ini.")

# -----------------------------
# RFM Analysis Section
# -----------------------------
st.header("Analisis Lanjutan: Segmentasi Pelanggan Menggunakan Model RFM")

# Prepare data_orders from filtered data
data_orders = (
    filtered_orders.merge(df_order_items_, how="left", on="order_id")
    .query('order_status == "delivered"')
    .groupby("customer_id")
    .agg(
        last_purchase_date=("order_purchase_timestamp", "max"),
        order_count=("order_id", "nunique"),
        total_price=("total_price", "sum")
    )
    .sort_values(by="order_count", ascending=False)
    .reset_index()
)

# RFM Calculation (adapted from script)
df_rfm = data_orders[["customer_id", "last_purchase_date", "order_count", "total_price"]].copy().sort_values(by="last_purchase_date", ascending=True)
df_rfm.columns = ["customer_unique_id", "last_purchase_date", "freq", "monetary"]

recency_date = df_rfm["last_purchase_date"].max() + pd.Timedelta(days=1)
df_rfm["recency"] = df_rfm["last_purchase_date"].apply(lambda x: (recency_date - x).days).fillna(0).astype(int)

# Quartiles
r_quartiles = df_rfm["recency"].quantile([0.2, 0.4, 0.6, 0.8])
f_quartiles = df_rfm["freq"].quantile([0.2, 0.4, 0.6, 0.8])
m_quartiles = df_rfm["monetary"].quantile([0.2, 0.4, 0.6, 0.8])

# Scoring functions (from script)
def r_score(value, r_quartiles):
    if value >= r_quartiles[0.8]:
        return 1
    elif value >= r_quartiles[0.6]:
        return 2
    elif value >= r_quartiles[0.4]:
        return 3
    elif value >= r_quartiles[0.2]:
        return 4
    else:
        return 5

def f_score(value, f_quartiles):
    if value >= f_quartiles[0.8]:
        return 5
    elif value >= f_quartiles[0.6]:
        return 4
    elif value >= f_quartiles[0.4]:
        return 3
    elif value >= f_quartiles[0.2]:
        return 2
    else:
        return 1

def m_score(value, m_quartiles):
    if value >= m_quartiles[0.8]:
        return 5
    elif value >= m_quartiles[0.6]:
        return 4
    elif value >= m_quartiles[0.4]:
        return 3
    elif value >= m_quartiles[0.2]:
        return 2
    else:
        return 1

df_rfm["R_Score"] = df_rfm["recency"].apply(lambda x: r_score(x, r_quartiles))
df_rfm["F_Score"] = df_rfm["freq"].apply(lambda x: f_score(x, f_quartiles))
df_rfm["M_Score"] = df_rfm["monetary"].apply(lambda x: m_score(x, m_quartiles))

df_rfm["RFM_Score"] = (
    df_rfm["R_Score"].astype(str) +
    df_rfm["F_Score"].astype(str) +
    df_rfm["M_Score"].astype(str)
)

# Segment function (from script)
def rfm_segment(score):
    if score in ["555", "554", "545", "544", "545", "455", "445"]:
        return "Champions"
    elif score in ["543", "444", "435", "355", "354", "345", "344", "335"]:
        return "Loyal"
    elif score in ["553", "551", "552", "541", "542", "533", "532", "531", "452", "451", "442", "441",
                   "431", "453", "433", "432", "423", "353", "352", "351", "342", "341", "333", "323"]:
        return "Potential Loyalist"
    elif score in ["525", "524", "523", "522", "521", "515", "514", "513", "425", "424", "413", "414",
                   "415", "315", "314", "313"]:
        return "Promising"
    elif score in ["512", "511", "422", "421", "412", "411", "311"]:
        return "New Customers"
    elif score in ["535", "534", "443", "434", "343", "334", "325", "324"]:
        return "Need Attention"
    elif score in ["331", "321", "312", "221", "213", "231", "241", "251"]:
        return "About To Sleep"
    elif score in ["255", "254", "245", "244", "243", "252", "243", "242", "235", "234", "225", "224",
                   "153", "152", "145", "143", "142", "135", "134", "133", "125", "124"]:
        return "At Risk"
    elif score in ["155", "154", "144", "214", "215", "115", "114", "113"]:
        return "Cannot Lose Them"
    elif score in ["332", "322", "233", "232", "223", "222", "132", "123", "122", "212", "211"]:
        return "Hibernating Customers"
    elif score in ["111", "112", "121", "131", "141", "151"]:
        return "Lost Customers"
    else:
        return "Other"

df_rfm["Segment"] = df_rfm["RFM_Score"].apply(rfm_segment)

# RFM Filter
unique_segments = sorted(df_rfm['Segment'].unique())
selected_segments = st.multiselect("Pilih Segmen RFM", unique_segments, default=unique_segments)

# Apply segment filter
filtered_rfm = df_rfm[df_rfm['Segment'].isin(selected_segments)]

# RFM Summary
data_rfm_summary = (
    filtered_rfm
    .groupby("Segment")
    .agg(
        customer_count=("Segment", "count"),
        total_monetary=("monetary", "sum")
    )
    .reset_index()
)

total_monetary_all = data_rfm_summary["total_monetary"].sum()
data_rfm_summary["total_monetary_percent"] = round(
    (data_rfm_summary["total_monetary"] / total_monetary_all) * 100, 2
)

data_rfm_summary["total_monetary_scaling"] = data_rfm_summary["total_monetary"].apply(
    lambda x: (x - data_rfm_summary["total_monetary"].min()) / (data_rfm_summary["total_monetary"].max() - data_rfm_summary["total_monetary"].min())
    if (data_rfm_summary["total_monetary"].max() - data_rfm_summary["total_monetary"].min()) != 0 else 0
)

# Display RFM Summary Table
st.subheader("Ringkasan Segmen RFM")
st.dataframe(data_rfm_summary)

# Visualization: Pareto Chart (adapted)
data_rfm_summary = data_rfm_summary.sort_values(by="total_monetary", ascending=False).reset_index(drop=True)
data_rfm_summary["Cumulative_%"] = data_rfm_summary["total_monetary"].cumsum() / data_rfm_summary["total_monetary"].sum() * 100

fig_pareto = go.Figure()

fig_pareto.add_trace(
    go.Bar(
        x=data_rfm_summary["Segment"].astype(str),
        y=data_rfm_summary["total_monetary"].round(2),
        name="Total Monetary",
        marker_color=px.colors.sequential.Blues,
        hovertemplate="<b>%{x}</b><br>Total Monetary: $%{y: ,.2f}<extra></extra>"
    )
)

fig_pareto.add_trace(
    go.Scatter(
        x=data_rfm_summary["Segment"].astype(str),
        y=data_rfm_summary["Cumulative_%"],
        name="Cumulative %",
        mode="lines+markers+text",
        yaxis="y2",
        marker_color="rgb(255,160,122)",
        line=dict(color="rgb(192, 57, 43)", width=3),
        hovertemplate="<b>%{x}</b><br>Cumulative: %{y:.1f}%<extra></extra>"
    )
)

fig_pareto.update_layout(
    title=dict(text="<b>Bagan Pareto Segmen Pelanggan Berdasarkan Nilai Moneter</b>", font=dict(size=12, family="Arial", color="black")),
    plot_bgcolor="white",
    yaxis=dict(side="left", showgrid=False, zeroline=True, showline=False, showticklabels=True),
    yaxis2=dict(side="right", overlaying="y", showgrid=False, zeroline=False, showline=False, showticklabels=True, ticksuffix="%", range=[0, 100]),
    xaxis=dict(showline=True, linecolor="rgb(204, 204, 204)", linewidth=2),
    showlegend=False
)

st.plotly_chart(fig_pareto, use_container_width=True)

# =============================
# 📌 2. Explorasi Orders
# =============================
st.header("🛒 Analisis Pemesanan")

# Convert date columns (already done, but ensure for filtered)
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for col in date_cols:
    if col in filtered_orders.columns:
        filtered_orders[col] = pd.to_datetime(filtered_orders[col], errors="coerce")

# Order status distribution
status_counts = filtered_orders["order_status"].value_counts().reset_index()
status_counts.columns = ["status", "total"]
fig_status = px.bar(status_counts, x="status", y="total", title="Distribusi Status Order")
st.plotly_chart(fig_status, use_container_width=True)

# Orders over time with aggregation option
aggregation = st.selectbox("Pilih Agregasi Waktu", ["Harian", "Mingguan", "Bulanan"], index=0)
    
if aggregation == "Harian":
    group_col = filtered_orders["order_purchase_timestamp"].dt.date
elif aggregation == "Mingguan":
    group_col = filtered_orders["order_purchase_timestamp"].dt.to_period("W")
else:  # Bulanan
    group_col = filtered_orders["order_purchase_timestamp"].dt.to_period("M")
    
orders_over_time = filtered_orders.groupby(group_col).size().reset_index(name='count')
orders_over_time.index = orders_over_time.index.astype(str)  # For x-axis
    
fig_time = px.line(
    orders_over_time,
    x=orders_over_time.index,
    y='count',
    title="Jumlah Order dari Waktu ke Waktu",
    labels={"index": "Periode", "count": "Jumlah Order"}
)
st.plotly_chart(fig_time, use_container_width=True)


# =============================
# 📌 3. Payment Analysis
# =============================
st.header("💳 Analisis Pembayaran")

payment_counts = filtered_order_payments["payment_type"].value_counts().reset_index()
payment_counts.columns = ["payment_type", "total"]

fig_pay = px.pie(payment_counts, names="payment_type", values="total", title="Distribusi Metode Pembayaran")
st.plotly_chart(fig_pay, use_container_width=True)


# =============================
# 📌 4. Review Analysis
# =============================
st.header("⭐ Analisis Penilaian Pelanggan")

review_counts = filtered_order_reviews["review_score"].value_counts().sort_index()

fig_review = px.bar(
    review_counts,
    title="Distribusi Rating Review",
    labels={"index": "Rating", "value": "Jumlah Review"}
)
st.plotly_chart(fig_review, use_container_width=True)


# =============================
# 📌 5. Product Analysis (PERBAIKAN DITERAPKAN)
# =============================
st.header("📦 Analisis Produk")

# Filter products based on filtered orders and count by category sales
filtered_product_ids = filtered_order_items['product_id'].unique()
filtered_products = df_products[df_products['product_id'].isin(filtered_product_ids)]

# Merge to get categories for sold items
filtered_order_items_with_cat = filtered_order_items.merge(
    filtered_products[['product_id', 'product_category_name']],
    on='product_id',
    how='left'
)

# Count occurrences (sales) per category
category_sales = filtered_order_items_with_cat["product_category_name"].fillna("Unknown").value_counts()

# Top N with slider
top_n_prod = st.slider("Pilih Jumlah Top Kategori Produk", min_value=5, max_value=50, value=15, step=5)
top_categories = category_sales.head(top_n_prod)

fig_prod = px.bar(
    top_categories,
    title=f"Top {top_n_prod} Kategori Produk Terbanyak (Berdasarkan Penjualan)",
    labels={"index": "Kategori Produk", "value": "Jumlah Penjualan"}
)
st.plotly_chart(fig_prod, use_container_width=True)


# =============================
# 📌 6. Seller Analysis
# =============================
st.header("🏬 Aktivitas Penjual")

# Top N sellers with slider
top_n_seller = st.slider("Pilih Jumlah Top Penjual", min_value=5, max_value=50, value=15, step=5)
seller_order_counts = filtered_order_items["seller_id"].value_counts().head(top_n_seller)

fig_seller = px.bar(
    seller_order_counts,
    title=f"Top {top_n_seller} Seller dengan Pesanan Terbanyak",
    labels={"index": "Seller ID", "value": "Jumlah Items Terjual"}
)
st.plotly_chart(fig_seller, use_container_width=True)