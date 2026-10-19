import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Sales & Revenue Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Sales & Revenue Analysis Dashboard")
st.caption("Explore sales performance, revenue trends, and top-performing products.")

REQUIRED_COLUMNS = ["Order Date", "Product", "Category", "Quantity", "Unit Price"]


def prepare_data(df):
    df.columns = [str(c).strip() for c in df.columns]

    aliases = {
        "order_date": "Order Date",
        "date": "Order Date",
        "product_name": "Product",
        "product": "Product",
        "category": "Category",
        "quantity": "Quantity",
        "qty": "Quantity",
        "unit_price": "Unit Price",
        "price": "Unit Price",
        "sales": "Revenue",
        "revenue": "Revenue",
        "region": "Region",
        "customer": "Customer"
    }

    rename_columns = {}
    for column in df.columns:
        key = column.strip().lower().replace(" ", "_")
        if key in aliases:
            rename_columns[column] = aliases[key]

    df = df.rename(columns=rename_columns)

    if "Revenue" not in df.columns:
        if "Quantity" in df.columns and "Unit Price" in df.columns:
            df["Revenue"] = (
                pd.to_numeric(df["Quantity"], errors="coerce")
                * pd.to_numeric(df["Unit Price"], errors="coerce")
            )
        else:
            raise ValueError(
                "Dataset must contain Revenue or Quantity and Unit Price."
            )

    if "Order Date" not in df.columns:
        raise ValueError("Dataset must contain an Order Date or Date column.")

    df["Order Date"] = pd.to_datetime(
        df["Order Date"], errors="coerce"
    )
    df["Revenue"] = pd.to_numeric(
        df["Revenue"], errors="coerce"
    )

    df = df.dropna(subset=["Order Date", "Revenue"]).copy()
    df = df[df["Revenue"] >= 0].copy()

    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(
            df["Quantity"], errors="coerce"
        ).fillna(0)
    else:
        df["Quantity"] = 0

    df["Month"] = df["Order Date"].dt.to_period("M").astype(str)

    return df

    # If a dataset already contains revenue/sales, keep it.
    if "Revenue" not in df.columns:
        if "Quantity" not in df.columns or "Unit Price" not in df.columns:
            raise ValueError(
                "Dataset must include Quantity and Unit Price, or a Revenue/Sales column."
            )
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["Unit Price"] = pd.to_numeric(df["Unit Price"], errors="coerce")
        df["Revenue"] = df["Quantity"] * df["Unit Price"]
    else:
        df["Revenue"] = pd.to_numeric(df["Revenue"], errors="coerce")

    if "Order Date" not in df.columns:
        raise ValueError("Dataset must include an Order Date or Date column.")
    if "Product" not in df.columns:
        df["Product"] = "Unknown Product"
    if "Category" not in df.columns:
        df["Category"] = "Uncategorized"

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Quantity" in df.columns:
        df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
    else:
        df["Quantity"] = 0

    st.sidebar.header("📂 Upload Sales Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload an Excel or CSV file",
    type=["csv", "xlsx"]
)
st.sidebar.header("📂 Upload Sales Data")

st.sidebar.caption(
    "Expected fields: Order Date, Product, Category, Quantity, Unit Price."
)

try:
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".xlsx"):
            raw_df = pd.read_excel(uploaded_file)
        else:
            raw_df = pd.read_csv(uploaded_file)

        df = prepare_data(raw_df)

    else:
        raw_df = pd.read_csv("sales_data.csv")
        df = prepare_data(raw_df)
        st.info(
            "Showing sample data. Upload your own CSV or Excel file using the sidebar."
        )

except Exception as e:
    st.error(f"Could not load the dataset: {e}")
    st.stop()

    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith(".xlsx"):
            raw_df = pd.read_excel(uploaded_file)
        else:
            raw_df = pd.read_csv(uploaded_file)
        df = prepare_data(raw_df)
    else:
        df = prepare_data(pd.read_csv("sales_data.csv"))
        st.info("Showing sample data. Upload your own CSV or Excel file using the sidebar.")
except Exception as e:
    st.error(f"Could not load the dataset: {e}")
    st.stop()

if df.empty:
    st.warning("No valid sales rows were found. Check your dates and numeric values.")
    st.stop()

# Sidebar filters
st.sidebar.header("🔎 Filters")
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered = df.copy()
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
    filtered = filtered[
        (filtered["Order Date"].dt.date >= start_date) &
        (filtered["Order Date"].dt.date <= end_date)
    ]

categories = sorted(filtered["Category"].dropna().astype(str).unique().tolist())
selected_categories = st.sidebar.multiselect(
    "Category", categories, default=categories
)
filtered = filtered[filtered["Category"].astype(str).isin(selected_categories)]

products = sorted(filtered["Product"].dropna().astype(str).unique().tolist())
selected_products = st.sidebar.multiselect(
    "Product", products, default=products
)
filtered = filtered[filtered["Product"].astype(str).isin(selected_products)]

if "Region" in filtered.columns:
    regions = sorted(filtered["Region"].dropna().astype(str).unique().tolist())
    selected_regions = st.sidebar.multiselect("Region", regions, default=regions)
    filtered = filtered[filtered["Region"].astype(str).isin(selected_regions)]

if filtered.empty:
    st.warning("No data matches these filters. Please change your selections.")
    st.stop()

# KPIs
total_revenue = filtered["Revenue"].sum()
total_orders = (
    filtered["Order ID"].nunique()
    if "Order ID" in filtered.columns
    else len(filtered)
)
total_units = filtered["Quantity"].sum()
avg_revenue = total_revenue / total_orders if total_orders else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Revenue", f"₹{total_revenue:,.2f}")
k2.metric("Orders / Records", f"{total_orders:,.0f}")
k3.metric("Units Sold", f"{total_units:,.0f}")
k4.metric("Revenue per Order / Record", f"₹{avg_revenue:,.2f}")

st.divider()

# Monthly revenue trend
monthly = (
    filtered.groupby("Month", as_index=False)
    .agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"))
    .sort_values("Month")
)
left, right = st.columns(2)

with left:
    st.subheader("📈 Monthly Revenue Trend")
    fig = px.line(
        monthly, x="Month", y="Revenue", markers=True,
        title="Revenue by Month",
        labels={"Month": "Month", "Revenue": "Revenue (₹)"}
    )
    fig.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("🏆 Top 10 Products")
    top_products = (
        filtered.groupby("Product", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
        .head(10)
        .sort_values("Revenue", ascending=True)
    )
    fig = px.bar(
        top_products, x="Revenue", y="Product", orientation="h",
        title="Top Products by Revenue",
        labels={"Revenue": "Revenue (₹)", "Product": "Product"}
    )
    st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("🧩 Revenue by Category")
    category_sales = (
        filtered.groupby("Category", as_index=False)["Revenue"]
        .sum()
        .sort_values("Revenue", ascending=False)
    )
    fig = px.pie(
        category_sales, names="Category", values="Revenue",
        title="Revenue Share by Category", hole=0.35
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📦 Units Sold by Category")
    category_units = (
        filtered.groupby("Category", as_index=False)["Quantity"]
        .sum()
        .sort_values("Quantity", ascending=False)
    )
    fig = px.bar(
        category_units, x="Category", y="Quantity",
        title="Units Sold by Category",
        labels={"Quantity": "Units Sold"}
    )
    st.plotly_chart(fig, use_container_width=True)


st.subheader("📋 Sales Data")

display_df = filtered.sort_values(
    "Order Date", ascending=False
).copy()

display_df["Order Date"] = display_df["Order Date"].dt.strftime("%Y-%m-%d")

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Order Date": st.column_config.TextColumn("Order Date"),
        "Product": st.column_config.TextColumn("Product"),
        "Category": st.column_config.TextColumn("Category"),
        "Quantity": st.column_config.NumberColumn("Quantity"),
        "Unit Price": st.column_config.NumberColumn(
            "Unit Price", format="₹%.2f"
        ),
        "Region": st.column_config.TextColumn("Region"),
        "Revenue": st.column_config.NumberColumn(
            "Revenue", format="₹%.2f"
        ),
        "Month": st.column_config.TextColumn("Month")
    }
)

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download filtered data as CSV",
    data=csv_bytes,
    file_name="filtered_sales_data.csv",
    mime="text/csv"
)

st.caption("Note: The sample data is fictional. Revenue is calculated as Quantity × Unit Price "
           "when a Revenue column is not supplied.")
