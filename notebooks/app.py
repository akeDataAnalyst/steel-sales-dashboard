import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page Configuration

st.set_page_config(
    page_title="Rebar Sales Dashboard • Ethiopia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title & description
st.title("Rebar Sales Performance Dashboard")
st.caption("Reinforcement bar sales analysis — Ethiopian market (2020–2026 + forecast)")

# Load data (cached)

@st.cache_data
def load_data():
    try:
        monthly = pd.read_csv('../data/dashboard_ready/monthly_agg.csv')
        monthly['Order_Date'] = pd.to_datetime(monthly['Order_Date'])

        forecast_rev   = pd.read_csv('../data/dashboard_ready/forecast_revenue.csv')
        forecast_rev['ds'] = pd.to_datetime(forecast_rev['ds'])

        forecast_price = pd.read_csv('../data/dashboard_ready/forecast_price.csv')
        forecast_price['ds'] = pd.to_datetime(forecast_price['ds'])

        top_products = pd.read_csv('../data/dashboard_ready/top_products.csv')
        top_regions  = pd.read_csv('../data/dashboard_ready/top_regions.csv')

        return monthly, forecast_rev, forecast_price, top_products, top_regions
    except FileNotFoundError as e:
        st.error(f"Missing data file: {e}")
        st.stop()

monthly, forecast_rev, forecast_price, top_products, top_regions = load_data()

# Sidebar – Filters
with st.sidebar:
    st.header("Controls")

    # Date range filter
    min_date = monthly['Order_Date'].min().date()
    max_date = monthly['Order_Date'].max().date()

    date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="date_range"
    )

    st.markdown("---")

# Apply date filter
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered = monthly[
        (monthly['Order_Date'].dt.date >= start_date) &
        (monthly['Order_Date'].dt.date <= end_date)
    ]
else:
    filtered = monthly.copy()

# KPI Cards

if filtered.empty:
    st.warning("No data in selected date range.")
else:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_rev = filtered['Revenue_ETB'].sum()
        st.metric("Total Revenue", f"{total_rev:,.0f} ETB", help="Sum in selected period")

    with col2:
        avg_price = filtered['Avg_Price_ETB_kg'].mean()
        st.metric("Avg. Selling Price", f"{avg_price:.2f} ETB/kg")

    with col3:
        total_margin = filtered['Total_Margin_ETB'].sum()
        st.metric("Est. Total Margin", f"{total_margin:,.1f} M ETB")

    with col4:
        if 'Season' in filtered.columns:
            dry_share = filtered[filtered['Season'] == 'Dry']['Revenue_ETB'].sum() / filtered['Revenue_ETB'].sum() * 100
            st.metric("Dry Season Share", f"{dry_share:.1f}%")
        else:
            st.metric("Dry Season Share", "N/A")

# Tabs
tab_trend, tab_categories, tab_forecast, tab_insights = st.tabs([
    "Trends", "Top Categories", "Forecast", "Insights & Recommendations"
])

# Trends (Revenue + Price)
with tab_trend:
    st.subheader("Revenue & Price Trends")

    col_left, col_right = st.columns(2)

    with col_left:
        fig_rev = px.line(
            filtered,
            x='Order_Date',
            y='Revenue_M_ETB',
            title='Monthly Revenue (Million ETB)',
            markers=True,
            labels={'Order_Date': 'Month', 'Revenue_M_ETB': 'Revenue (M ETB)'}
        )
        fig_rev.update_traces(line_color='#1f77b4', line_width=2.5)
        st.plotly_chart(fig_rev, use_container_width=True)

    with col_right:
        fig_price = px.line(
            filtered,
            x='Order_Date',
            y='Avg_Price_ETB_kg',
            title='Average Selling Price (ETB/kg)',
            markers=True,
            labels={'Order_Date': 'Month', 'Avg_Price_ETB_kg': 'Avg Price'}
        )
        fig_price.update_traces(line_color='#ff7f0e', line_width=2.5)
        st.plotly_chart(fig_price, use_container_width=True)

# Tab 2: Top Categories
with tab_categories:
    st.subheader("Top Products & Regions")

    col_p, col_r = st.columns(2)

    with col_p:
        fig_prod = px.bar(
            top_products.head(8),
            x='Revenue_B_ETB',
            y='Category',
            orientation='h',
            title='Top Products by Revenue (Billion ETB)',
            color='Revenue_B_ETB',
            color_continuous_scale='blugrn'
        )
        fig_prod.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_prod, use_container_width=True)

    with col_r:
        fig_reg = px.bar(
            top_regions,
            x='Revenue_B_ETB',
            y='Region',
            orientation='h',
            title='Top Regions by Revenue (Billion ETB)',
            color='Revenue_B_ETB',
            color_continuous_scale='tealgrn'
        )
        fig_reg.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig_reg, use_container_width=True)

# Tab 3: Forecast
with tab_forecast:
    st.subheader("Revenue Forecast – Next 12 Months")

    # Combine historical + forecast
    hist = filtered[['Order_Date', 'Revenue_M_ETB']].rename(
        columns={'Order_Date': 'ds', 'Revenue_M_ETB': 'yhat'}
    )
    hist['type'] = 'Historical'

    fore = forecast_rev[['ds', 'yhat_M']].rename(columns={'yhat_M': 'yhat'})
    fore['type'] = 'Forecast'

    combined = pd.concat([hist, fore])

    fig_fc = px.line(
        combined,
        x='ds',
        y='yhat',
        color='type',
        title='Revenue Historical + Forecast',
        labels={'ds': 'Date', 'yhat': 'Revenue (M ETB)'}
    )

    fig_fc.update_traces(
        line=dict(dash='dash', width=3),
        selector=dict(name='Forecast')
    )

    # confidence band
    fig_fc.add_traces(go.Scatter(
        x=forecast_rev['ds'], y=forecast_rev['yhat_upper']/1e6,
        mode='lines', line=dict(width=0), showlegend=False
    ))
    fig_fc.add_traces(go.Scatter(
        x=forecast_rev['ds'], y=forecast_rev['yhat_lower']/1e6,
        mode='lines', fill='tonexty', fillcolor='rgba(255,0,0,0.1)',
        line=dict(width=0), showlegend=False
    ))

    st.plotly_chart(fig_fc, use_container_width=True)

# Tab 4: Insights
with tab_insights:
    st.subheader("Key Business Insights & Recommendations")

    st.markdown("""
    **Main Observations (based on analysis 2020–2026):**

    - **Total revenue**: ≈ **12.88 billion ETB**
    - **Average selling price**: **247 ETB/kg** (strong upward trend due to inflation & demand)
    - **Average estimated margin**: **25%**
    - **Dominant region**: **Addis Ababa** (41% of revenue)
    - **Most valuable segment**: **Large Contractors** (~22%)
    - **Seasonality**: **Dry season (Nov–May)** generates **67%** of revenue
    - **Top product**: **Rebar 16mm Imported (Turkey)** (16% of revenue)

    **Strategic Recommendations:**

    1. Strengthen presence in **Addis Ababa** and **Oromia** (combined 70%+ share)
    2. Build long-term relationships with **Large Contractors** and **Government Projects**
    3. Prepare inventory & capacity for **dry season peaks** (Nov–May)
    4. Consider local production of **16mm high-grade rebar** to improve margins vs imports
    5. Monitor price elasticity — higher prices reduce order volumes
    6. Forecast indicates continued growth — align expansion with infrastructure boom
    """)

# Footer
st.markdown("---")
st.caption("Developed by **Aklilu Abera** • Data Analyst")

