import streamlit as st
import pandas as pd
from datetime import datetime
import os

from arbitrage_core import find_opportunities, discover_best_seller_categories

st.set_page_config(page_title="Amazon ↔ eBay Comparative Analysis (UK)", page_icon="📊", layout="wide")

st.title("📊 Amazon ↔ eBay Comparative Analysis (UK)")
st.caption("Research-only tool. Always logs in to Amazon (Playwright headless), checks eBay demand/price, estimates profit. No posting, no automation to marketplaces.")

with st.expander("Status & setup"):
    st.markdown("- **Amazon login**: always enabled. Provide `AMAZON_EMAIL`, `AMAZON_PASSWORD`, and optionally `AMAZON_TOTP_SECRET` in environment variables.")
    st.write("Amazon login mode: ✅ always enabled")

with st.expander("⚠️ Terms notice", expanded=False):
    st.markdown("""
- Use this app **only for comparative analysis / research**.
- Respect Amazon & eBay site terms. Avoid heavy load; we include randomized delays and backoff.
- Do **not** use Amazon Prime for shipping to your customers or for resale.
""")

with st.sidebar:
    st.header("Scan settings")
    autod = st.checkbox("Auto-discover Amazon Best Seller categories", value=True)
    max_cats = st.slider("How many categories to scan", 3, 30, 8, 1)
    cats_text = ""
    if not autod:
        cats_text = st.text_area("Amazon Best Sellers URLs (one per line)", height=160, placeholder="https://www.amazon.co.uk/gp/bestsellers/electronics\nhttps://www.amazon.co.uk/gp/bestsellers/kitchen")

    st.subheader("Filters")
    min_profit = st.number_input("Min profit (£)", min_value=0.0, max_value=1000.0, value=0.0, step=0.5)
    min_margin = st.slider("Min margin (%)", min_value=0, max_value=50, value=0, step=1)
    min_sold = st.slider("Min 'sold recently' (eBay)", min_value=0, max_value=200, value=0, step=1)

    st.subheader("Heuristics")
    ebay_fee_rate = st.number_input("eBay fee rate (e.g., 0.13 = 13%)", min_value=0.0, max_value=0.3, value=0.13, step=0.01, format="%.2f")
    ebay_fixed_fee = st.number_input("eBay fixed fee (£)", min_value=0.0, max_value=2.0, value=0.30, step=0.05)
    max_items = st.slider("Max Amazon items per category", min_value=10, max_value=200, value=30, step=10)
    max_ebay_results = st.slider("Max eBay results to scan", min_value=3, max_value=20, value=8, step=1)
    query_words = st.slider("Use first N title words for eBay query", min_value=4, max_value=20, value=8, step=1)
    avoid = st.text_input("Avoid keywords (comma-separated)", value="Apple iPhone,Nike,PlayStation,Xbox,Gift Card")

    run = st.button("Run comparative analysis")

if run:
    if autod:
        with st.spinner("Discovering Amazon Best Seller categories..."):
            categories = discover_best_seller_categories(max_categories=max_cats)
    else:
        categories = [ln.strip() for ln in cats_text.splitlines() if ln.strip()]

    if not categories:
        st.error("No categories to scan. Provide URLs or use auto-discover.")
    else:
        with st.spinner("Scanning categories, checking eBay demand/price, estimating profit..."):
            results = find_opportunities(
                categories=categories,
                min_profit=min_profit,
                min_margin=min_margin/100.0,
                min_sold_recent=min_sold,
                ebay_fee_rate=ebay_fee_rate,
                ebay_fixed_fee=ebay_fixed_fee,
                max_items=max_items,
                max_ebay_results=max_ebay_results,
                avoid_keywords=[s.strip() for s in avoid.split(",") if s.strip()],
                query_words=query_words
            )
        if not results:
            st.info("No items matched your filters. Lower the thresholds or try different categories.")
        else:
            df = pd.DataFrame([r.__dict__ for r in results])
            df["est_margin_pct"] = (df["est_margin"] * 100).round(2)
            cols = ["title","amazon_price","ebay_price","ebay_shipping","ebay_total_price","estimated_ebay_fee",
                    "est_profit_gbp","est_margin_pct","sold_recent","prime","rating","reviews",
                    "amazon_url","ebay_url","asin","category_url","image_url"]
            df = df[cols]
            st.success(f"Found {len(df)} comparative opportunities across {len(categories)} categories")
            st.dataframe(df, use_container_width=True, height=500)

            csv = df.to_csv(index=False)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button("Download CSV report", data=csv, file_name=f"comparative_report_{ts}.csv", mime="text/csv")
else:
    st.info("Choose auto-discover or paste URLs, set filters, then click **Run comparative analysis**.")
