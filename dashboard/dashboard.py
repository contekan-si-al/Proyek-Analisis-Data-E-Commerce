import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

st.set_page_config(page_title="Olist E-Commerce Analysis", layout="wide")

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
    # "product_category_translation": "product_category_name_translation.csv",
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
customers = dfs["customers"]
geolocation = dfs["geolocation"]
order_items = dfs["order_items"]
order_payments = dfs["order_payments"]
order_reviews = dfs["order_reviews"]
orders = dfs["orders"]
products = dfs["products"]
sellers = dfs["sellers"]
# translation = dfs["product_category_translation"]


# =============================
# 📌 1. Basic Overview Section (tanpa Dataset Dimensions)
# =============================
st.header("📊 Preview Semua Dataset")

# Hanya preview dataset
# st.subheader("Preview Semua Dataset")
for name, df in dfs.items():
    st.write(f"### {name}")
    st.dataframe(df.head())


# =============================
# 📌 2. Explorasi Orders
# =============================
st.header("🛒 Analisis Pemesanan")

# Convert date columns
date_cols = [
    "order_purchase_timestamp",
    "order_approved_at",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for col in date_cols:
    if col in orders.columns:
        orders[col] = pd.to_datetime(orders[col], errors="coerce")

col1, col2 = st.columns(2)

# Order status distribution
with col1:
    status_counts = orders["order_status"].value_counts().reset_index()
    status_counts.columns = ["status", "total"]
    fig_status = px.bar(status_counts, x="status", y="total", title="Distribusi Status Order")
    st.plotly_chart(fig_status)

# Orders over time
with col2:
    daily_orders = orders.groupby(orders["order_purchase_timestamp"].dt.date).size()
    fig_time = px.line(
        daily_orders,
        title="Jumlah Order dari Waktu ke Waktu",
        labels={"value": "Jumlah Order", "index": "Tanggal"}
    )
    st.plotly_chart(fig_time)


# =============================
# 📌 3. Payment Analysis
# =============================
st.header("💳 Analisis Pembayaran")

payment_counts = order_payments["payment_type"].value_counts().reset_index()
payment_counts.columns = ["payment_type", "total"]

fig_pay = px.pie(payment_counts, names="payment_type", values="total", title="Distribusi Metode Pembayaran")
st.plotly_chart(fig_pay)


# =============================
# 📌 4. Review Analysis
# =============================
st.header("⭐ Analisis Penilaian Pelanggan")

review_counts = order_reviews["review_score"].value_counts().sort_index()

fig_review = px.bar(
    review_counts,
    title="Distribusi Rating Review",
    labels={"index": "Rating", "value": "Jumlah Review"}
)
st.plotly_chart(fig_review)


# =============================
# 📌 5. Product Analysis (PERBAIKAN DITERAPKAN)
# =============================
st.header("📦 Analisis Produk")

# Bar chart
product_counts = products["product_category_name"].fillna("Unknown").value_counts().head(15)

fig_prod = px.bar(
    product_counts,
    title="Top 15 Kategori Produk Terbanyak",
    labels={"index": "Kategori Produk", "value": "Jumlah Produk"}
)
st.plotly_chart(fig_prod)


# =============================
# 📌 6. Seller Analysis
# =============================
st.header("🏬 Aktivitas Penjual")

seller_order_counts = order_items["seller_id"].value_counts().head(15)

fig_seller = px.bar(
    seller_order_counts,
    title="Top 15 Seller dengan Pesanan Terbanyak",
    labels={"index": "Seller ID", "value": "Jumlah Items Terjual"}
)
st.plotly_chart(fig_seller)


# =============================
# 📌 7. Insight Section
# =============================
st.header("🔍 Insight Utama")

st.markdown("""
### 📌 **Ringkasan Insight**
1. **Kategori produk paling populer** didominasi oleh kategori *bed bath table*, *health beauty*, dan *sports leisure*.  
2. **Metode pembayaran paling umum** adalah **credit card**, diikuti oleh **boleto**.  
3. **Mayoritas rating review** adalah 5 (pelanggan puas), namun rating 1 juga cukup tinggi → peluang untuk perbaikan layanan.  
4. **Penjual (seller)** tertentu menguasai pasar dengan jumlah order sangat tinggi → indikasi konsentrasi marketplace.  
5. Aktivitas **order meningkat secara tren** mengikuti pola musiman tertentu.  

### 📌 Insight Lanjutan Bisa Dibuat:
- Analisis shipping performance (waktu kirim vs estimasi)  
- Analisis hubungan harga vs rating  
- Analisis kategori produk yang rawan keterlambatan  
- Cohort analysis untuk pelanggan (retensi)  
- Market basket analysis  
""")




st.caption('Copyright © AL. 2025')