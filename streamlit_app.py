import streamlit as st  # type: ignore[import]
import requests
import pandas as pd  # type: ignore[import]
import plotly.express as px
import plotly.graph_objects as go  # type: ignore[import]
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
import os

API = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="AI Finance Analyzer",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── HELPERS ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_transactions():
    try:
        r = requests.get(f"{API}/transactions/", timeout=10)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Cannot reach API: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=10)
def fetch_summary():
    try:
        r = requests.get(f"{API}/analytics/summary", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}


@st.cache_data(ttl=10)
def fetch_by_category():
    try:
        r = requests.get(f"{API}/analytics/by-category", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=10)
def fetch_by_month():
    try:
        r = requests.get(f"{API}/analytics/by-month", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


# ─── NEW: BUDGET HELPERS ──────────────────────────────────────────────────────
@st.cache_data(ttl=10)
def fetch_budgets():
    try:
        r = requests.get(f"{API}/budgets/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=10)
def fetch_budget_status():
    try:
        r = requests.get(f"{API}/budgets/status", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=10)
def fetch_income():
    try:
        r = requests.get(f"{API}/income/", timeout=5)
        return r.json() if r.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=10)
def fetch_income_summary():
    try:
        r = requests.get(f"{API}/income/summary", timeout=5)
        return r.json() if r.status_code == 200 else {}
    except:
        return {}

def clear_cache():
    fetch_transactions.clear()
    fetch_summary.clear()
    fetch_by_category.clear()
    fetch_by_month.clear()
    fetch_budgets.clear()           # ← NEW
    fetch_budget_status.clear()     # ← NEW
    fetch_income.clear()           # ← NEW
    fetch_income_summary.clear()   

CATEGORY_COLORS = {
    "food": "#FF6B6B",
    "travel": "#4ECDC4",
    "shopping": "#45B7D1",
    "entertainment": "#96CEB4",
    "health": "#FFEAA7",
    "utilities": "#DDA0DD",
    "education": "#98D8C8",
    "finance": "#F7DC6F",
    "uncategorized": "#BDC3C7",
}

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💰 Finance Analyzer")
    st.caption("AI-powered · ML anomaly detection · RAG chat")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "➕ Add Transaction", "📂 Upload CSV", "🤖 AI Chat", 
         "💰 Budgets","💵 Income", "📱 SMS Import","📄 Reports","⚙️ Manage"],
        label_visibility="collapsed",
    )

    st.divider()

    # Filters (only shown on dashboard)
    if page == "📊 Dashboard":
        st.subheader("Filters")
        df_all = fetch_transactions()
        if not df_all.empty and "category" in df_all.columns:
            cats = sorted(df_all["category"].unique().tolist())
            selected_cats = st.multiselect("Categories", cats, default=cats)
            show_anomalies_only = st.checkbox("Show anomalies only")
        else:
            selected_cats = []
            show_anomalies_only = False

    if st.button("🔄 Refresh Data"):
        clear_cache()
        st.rerun()

# ─── PAGE: DASHBOARD ─────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.title("📊 Dashboard")

    summary = fetch_summary()
    df = fetch_transactions()

    # KPI Row
    if summary:
        income_sum = fetch_income_summary()
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("💰 Total Spent",  f"₹{summary.get('total', 0):,.0f}")
        c2.metric("📋 Transactions", summary.get("count", 0))
        c3.metric("📉 Avg Amount",   f"₹{summary.get('avg', 0):,.0f}")
        c4.metric("🔥 Highest",      f"₹{summary.get('max', 0):,.0f}")
        c5.metric("💵 Monthly Income", f"₹{income_sum.get('monthly_income', 0):,.0f}")
        c6.metric("🏦 Monthly Savings",
                    f"₹{income_sum.get('monthly_savings', 0):,.0f}",
                    delta=f"{income_sum.get('savings_rate', 0)}% savings rate",
                    delta_color="normal")

    if df.empty:
        st.info("No transactions yet. Add some or upload a CSV to get started.")
        st.stop()

    # Apply filters
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if selected_cats:
        df = df[df["category"].isin(selected_cats)]
    if show_anomalies_only:
        df = df[df["is_anomaly"] == True]

    st.divider()

    # Charts row 1
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Spending by Category")
        cat_data = fetch_by_category()
        if cat_data:
            cat_df = pd.DataFrame(cat_data)
            cat_df = cat_df[cat_df["category"].isin(selected_cats)] if selected_cats else cat_df
            fig = px.bar(
                cat_df.sort_values("total", ascending=True),
                x="total", y="category", orientation="h",
                color="category",
                color_discrete_map=CATEGORY_COLORS,
                text="total",
                labels={"total": "Amount (₹)", "category": ""},
            )
            fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
            fig.update_layout(showlegend=False, height=320, margin=dict(l=0, r=20, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.subheader("Spending Distribution")
        if cat_data:
            cat_df = pd.DataFrame(cat_data)
            fig2 = px.pie(
                cat_df, values="total", names="category",
                color="category", color_discrete_map=CATEGORY_COLORS,
                hole=0.4,
            )
            fig2.update_traces(textposition="inside", textinfo="percent+label")
            fig2.update_layout(showlegend=False, height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)

    # Monthly trend
    st.subheader("Monthly Spending Trend")
    month_data = fetch_by_month()
    if month_data:
        month_df = pd.DataFrame(month_data)
        fig3 = px.line(
            month_df, x="month", y="total",
            markers=True, line_shape="spline",
            labels={"month": "Month", "total": "Total Spent (₹)"},
        )
        fig3.update_traces(line_color="#4ECDC4", marker_color="#FF6B6B", marker_size=8)
        fig3.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig3, use_container_width=True)

    # Anomalies section
    anomalies = df[df["is_anomaly"] == True] if "is_anomaly" in df.columns else pd.DataFrame()
    if not anomalies.empty:
        st.subheader("🚨 Anomaly Alerts")
        for _, row in anomalies.iterrows():
            st.warning(
                f"⚠️ **{row['description']}** — ₹{row['amount']:,.2f} "
                f"on {str(row['date'])[:10]} | category: `{row['category']}` "
                f"| anomaly score: `{row['anomaly_score']}`"
            )

    # Transactions table
    st.subheader("Transactions")
    display_cols = ["id", "date", "description", "amount", "category", "confidence", "is_anomaly", "anomaly_score"]
    display_cols = [c for c in display_cols if c in df.columns]
    display_df = df[display_cols].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    display_df["confidence"] = display_df["confidence"].apply(lambda x: f"{x:.1f}%")

    def row_style(row):
        if "is_anomaly" in row and row["is_anomaly"]:
            return ["background-color: #fff0f0"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display_df.style.apply(row_style, axis=1),
        use_container_width=True,
        hide_index=True,
    )

# ─── PAGE: ADD TRANSACTION ────────────────────────────────────────────────────
elif page == "➕ Add Transaction":
    st.title("➕ Add Transaction")

    with st.form("add_form", clear_on_submit=True):
        desc = st.text_input("Description", placeholder="e.g. Swiggy order, Uber ride...")
        amount = st.number_input("Amount (₹)", min_value=0.01, step=10.0, format="%.2f")
        override_cat = st.selectbox(
            "Category (optional — AI will predict if left as Auto)",
            ["Auto (AI predict)", "food", "travel", "shopping", "entertainment",
             "health", "utilities", "education", "finance"],
        )
        submitted = st.form_submit_button("Add Transaction", type="primary")

    if submitted:
        if not desc.strip():
            st.error("Description is required")
        else:
            payload = {"description": desc, "amount": amount}
            if override_cat != "Auto (AI predict)":
                payload["category"] = override_cat

            with st.spinner("Saving..."):
                r = requests.post(f"{API}/transactions/", json=payload)

            if r.status_code == 201:
                result = r.json()
                clear_cache()
                st.success(f"✅ Added! Category: **{result['category']}** ({result['confidence']:.1f}% confident)")
                st.balloons()
            else:
                st.error(f"Failed: {r.text}")

# ─── PAGE: UPLOAD CSV ─────────────────────────────────────────────────────────
elif page == "📂 Upload CSV":
    st.title("📂 Upload Bank Statement CSV")

    st.info("""
    **Supported formats:** Any CSV with columns for description/narration, amount/debit, and date.
    Works with HDFC, ICICI, SBI, Axis, and generic exports.
    """)

    sample_csv = """date,description,amount
2024-03-01,Swiggy Order,320.00
2024-03-02,Uber Ride,180.00
2024-03-03,Amazon Shopping,1250.00
2024-03-04,Netflix Subscription,499.00
2024-03-05,Electricity Bill,1800.00
2024-03-06,Gym Membership,2000.00
2024-03-10,Dominos Pizza,450.00
2024-03-12,Train Ticket IRCTC,850.00
2024-03-15,Doctor Consultation,500.00
2024-03-20,Flipkart Order,3200.00
2024-03-22,Zomato Food,290.00
2024-03-28,Salary Credit,50000.00
"""
    st.download_button(
        "⬇️ Download Sample CSV",
        data=sample_csv,
        file_name="sample_transactions.csv",
        mime="text/csv",
    )

    uploaded = st.file_uploader("Upload your CSV", type=["csv"])

    if uploaded:
        with st.spinner("Parsing and importing..."):
            r = requests.post(
                f"{API}/transactions/upload/csv",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
            )

        if r.status_code == 200:
            result = r.json()
            clear_cache()
            st.success(f"✅ Imported **{result['imported']}** transactions")
            if result["skipped"]:
                st.warning(f"⚠️ Skipped {result['skipped']} rows")
            if result["errors"]:
                with st.expander("Parse errors"):
                    for e in result["errors"]:
                        st.text(e)
        else:
            st.error(f"Upload failed: {r.text}")

# ─── PAGE: AI CHAT ────────────────────────────────────────────────────────────
elif page == "🤖 AI Chat":
    st.title("🤖 Ask AI About Your Finances")
    st.caption("Powered by RAG — answers are based on your actual transaction data")

    st.subheader("Try asking:")
    cols = st.columns(3)
    suggestions = [
        "How much did I spend on food?",
        "What was my highest expense?",
        "Which category do I spend most on?",
        "Show me all travel expenses",
        "Were there any unusual transactions?",
        "How much did I spend this month?",
    ]
    for i, s in enumerate(suggestions):
        if cols[i % 3].button(s, key=f"sug_{i}"):
            st.session_state["chat_input"] = s

    st.divider()

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg.get("sources"):
                st.caption(f"📚 {msg['sources']} transactions referenced")

    user_input = st.chat_input("Ask about your spending...")
    if "chat_input" in st.session_state:
        user_input = st.session_state.pop("chat_input")

    if user_input:
        st.session_state["chat_history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                r = requests.post(f"{API}/chat/", json={"message": user_input})
            if r.status_code == 200:
                data = r.json()
                reply = data["reply"]
                sources = data.get("sources_used", 0)
                st.write(reply)
                st.caption(f"📚 {sources} transactions referenced")
                st.session_state["chat_history"].append(
                    {"role": "assistant", "content": reply, "sources": sources}
                )
            else:
                st.error(f"Chat error: {r.text}")

    if st.session_state.get("chat_history"):
        if st.button("🗑️ Clear Chat"):
            st.session_state["chat_history"] = []
            st.rerun()
            

# ─── PAGE: INCOME ─────────────────────────────────────────────────────────────
elif page == "💵 Income":
    st.title("💵 Income Tracker")

    # ── Summary cards ──────────────────────────────────────
    summary = fetch_income_summary()
    if summary:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("💵 This Month Income",   f"₹{summary['monthly_income']:,.0f}")
        c2.metric("💸 This Month Expenses", f"₹{summary['monthly_expenses']:,.0f}")
        c3.metric("🏦 This Month Savings",  f"₹{summary['monthly_savings']:,.0f}")
        c4.metric("📈 Savings Rate",        f"{summary['savings_rate']}%")

    st.divider()

    # ── Add income form ────────────────────────────────────
    st.subheader("Add Income")
    with st.form("income_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            desc = st.text_input("Description", placeholder="e.g. Monthly Salary")
        with col2:
            amt = st.number_input("Amount (₹)", min_value=1.0, step=1000.0)
        with col3:
            cat = st.selectbox("Type", [
                "salary", "freelance", "business",
                "investment", "rental", "other"
            ])
        submitted = st.form_submit_button("Add Income ➕", type="primary")

    if submitted:
        if not desc.strip():
            st.error("Description is required")
        else:
            r = requests.post(f"{API}/income/", json={
                "description": desc,
                "amount": amt,
                "category": cat,
            })
            if r.status_code == 201:
                clear_cache()
                st.success(f"✅ Income of ₹{amt:,.0f} added!")
                st.balloons()
            else:
                st.error(f"Failed: {r.text}")

    st.divider()

    # ── Income history ─────────────────────────────────────
    st.subheader("Income History")
    incomes = fetch_income()
    if not incomes:
        st.info("No income added yet.")
    else:
        inc_df = pd.DataFrame(incomes)
        inc_df["date"] = pd.to_datetime(inc_df["date"]).dt.strftime("%Y-%m-%d")
        st.dataframe(inc_df, use_container_width=True, hide_index=True)

        # Delete income
        st.subheader("Delete Income Entry")
        del_id = st.selectbox("Select ID to delete",
                              [i["id"] for i in incomes])
        if st.button("🗑️ Delete", type="secondary"):
            r = requests.delete(f"{API}/income/{del_id}")
            if r.status_code == 200:
                clear_cache()
                st.success("Deleted!")
                st.rerun()   
                

# ─── PAGE: REPORTS ────────────────────────────────────────────────────────────
elif page == "📄 Reports":
    st.title("📄 Monthly PDF Reports")
    st.caption("Generate and download beautiful PDF reports for any month")

    # ── Month selector ─────────────────────────────────────
    st.subheader("Select Month")
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Year", list(range(2023, 2027)), index=1)
    with col2:
        month = st.selectbox("Month", list(range(1, 13)),
                             format_func=lambda m: datetime(2024, m, 1).strftime("%B"))

    month_str = f"{year}-{month:02d}"
    st.info(f"📅 Selected: **{datetime(year, month, 1).strftime('%B %Y')}**")

    # ── Generate button ────────────────────────────────────
    if st.button("📄 Generate & Download PDF", type="primary"):
        with st.spinner("Generating your report..."):
            r = requests.get(
                f"{API}/reports/monthly/{month_str}",
                timeout=30,
            )

        if r.status_code == 200:
            st.success("✅ Report generated!")
            st.download_button(
                label="⬇️ Download PDF Report",
                data=r.content,
                file_name=f"finance_report_{month_str}.pdf",
                mime="application/pdf",
            )
        else:
            st.error(f"Failed to generate report: {r.text}")

    st.divider()

    # ── Quick links for recent months ─────────────────────
    st.subheader("⚡ Quick Generate")
    now = datetime.now()
    quick_months = []
    for i in range(4):
        m = now.month - i
        y = now.year
        if m <= 0:
            m += 12
            y -= 1
        quick_months.append((y, m))

    cols = st.columns(4)
    for i, (y, m) in enumerate(quick_months):
        label = datetime(y, m, 1).strftime("%B %Y")
        ms = f"{y}-{m:02d}"
        if cols[i].button(label, key=f"quick_{ms}"):
            with st.spinner(f"Generating {label} report..."):
                r = requests.get(f"{API}/reports/monthly/{ms}", timeout=30)
            if r.status_code == 200:
                st.success(f"✅ {label} report ready!")
                st.download_button(
                    label=f"⬇️ Download {label} PDF",
                    data=r.content,
                    file_name=f"finance_report_{ms}.pdf",
                    mime="application/pdf",
                    key=f"dl_{ms}",
                )
            else:
                st.error("Failed to generate report")                         

# ─── PAGE: BUDGETS ────────────────────────────────────────────────────────────
elif page == "💰 Budgets":
    st.title("💰 Budget Manager")

    # ── Set a budget ──────────────────────────────────────
    st.subheader("Set Monthly Budget")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        cat = st.selectbox("Category", [
            "food", "travel", "shopping", "entertainment",
            "health", "utilities", "education", "finance"
        ])
    with col2:
        amt = st.number_input("Monthly Limit (₹)", min_value=100.0, step=500.0)
    with col3:
        st.write("")
        st.write("")
        if st.button("Save", type="primary"):
            r = requests.post(f"{API}/budgets/", json={"category": cat, "amount": amt})
            if r.status_code == 200:
                clear_cache()
                st.success(f"✅ Budget set for {cat}!")
                st.rerun()

    st.divider()

    # ── Budget status ──────────────────────────────────────
    st.subheader("This Month's Budget Status")
    status = fetch_budget_status()

    if not status:
        st.info("No budgets set yet. Add one above!")
    else:
        for s in status:
            percent = s["percent"]
            color = (
                "🔴" if s["status"] == "exceeded"
                else "🟡" if s["status"] == "warning"
                else "🟢"
            )
            st.write(f"{color} **{s['category'].title()}**")
            st.progress(min(percent / 100, 1.0))
            col1, col2, col3 = st.columns(3)
            col1.metric("Spent", f"₹{s['spent']:,.0f}")
            col2.metric("Budget", f"₹{s['budget']:,.0f}")
            col3.metric("Remaining", f"₹{s['remaining']:,.0f}",
                       delta=f"{percent}% used",
                       delta_color="inverse")

            if s["status"] == "exceeded":
                st.error(f"🚨 Exceeded by ₹{abs(s['remaining']):,.0f}!")
            elif s["status"] == "warning":
                st.warning(f"⚠️ Almost at limit! Only ₹{s['remaining']:,.0f} left.")
            st.divider()

    # ── Delete a budget ────────────────────────────────────
    budgets = fetch_budgets()
    if budgets:
        st.subheader("Remove a Budget")
        del_cat = st.selectbox("Select category to remove",
                               [b["category"] for b in budgets])
        if st.button("🗑️ Remove Budget", type="secondary"):
            r = requests.delete(f"{API}/budgets/{del_cat}")
            if r.status_code == 200:
                clear_cache()
                st.success(f"Removed budget for {del_cat}")
                st.rerun()
                
                
# ─── PAGE: SMS IMPORT ─────────────────────────────────────────────────────────
elif page == "📱 SMS Import":
    st.title("📱 Bank SMS Importer")
    st.caption("Paste your bank SMS messages to auto-extract transactions")

    tab1, tab2 = st.tabs(["📩 Single SMS", "📦 Bulk Import"])

    # ── Single SMS ─────────────────────────────────────────
    with tab1:
        st.subheader("Paste one SMS")
        sms_input = st.text_area(
            "Bank SMS",
            height=120,
            placeholder="""Example:
Dear Customer, INR 320.00 debited from AC XX1234 on 01-03-24 for Swiggy. Available balance: 12,450.00"""
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Preview", use_container_width=True):
                if sms_input.strip():
                    r = requests.post(
                        f"{API}/sms/parse",
                        json={"sms_text": sms_input}
                    )
                    data = r.json()
                    if data["success"]:
                        parsed = data["parsed"]
                        st.success("✅ Successfully parsed!")
                        st.json({
                            "Description": parsed["description"],
                            "Amount": f"₹{parsed['amount']:,.2f}",
                            "Type": parsed["type"],
                            "Date": str(parsed["date"])[:10],
                        })
                        st.session_state["sms_preview"] = sms_input
                    else:
                        st.error(f"❌ {data['error']}")

        with col2:
            if st.button("💾 Import", type="primary", use_container_width=True):
                if sms_input.strip():
                    r = requests.post(
                        f"{API}/sms/import",
                        json={"sms_text": sms_input}
                    )
                    data = r.json()
                    if data["success"]:
                        clear_cache()
                        tx_type = data["type"]
                        saved = data["saved"]
                        if tx_type == "expense":
                            st.success(
                                f"✅ Saved as **expense**: "
                                f"{saved['description']} — ₹{saved['amount']:,.2f} "
                                f"| Category: {saved['category']}"
                            )
                        else:
                            st.success(
                                f"✅ Saved as **income**: "
                                f"{saved['description']} — ₹{saved['amount']:,.2f}"
                            )
                        st.balloons()
                    else:
                        st.error(f"❌ {data['error']}")

        # ── Example SMS templates ──────────────────────────
        st.divider()
        st.subheader("💡 Try these examples:")
        examples = [
            "Dear Customer, INR 320.00 debited from AC XX1234 on 01-03-24 for Swiggy. Avl bal: 12,450.00",
            "Rs.180 debited from your account for Uber on 02/03/2024. Available balance: Rs.12,270",
            "Your a/c XX5678 credited with INR 50,000.00 on 01-03-2024. Salary March 2024.",
            "INR 1,250.00 spent on Amazon.in on 03-03-2024. Available limit: Rs.48,750",
        ]
        for ex in examples:
            if st.button(f"📋 {ex[:60]}...", key=f"ex_{ex[:20]}"):
                st.session_state["sms_example"] = ex
                st.rerun()

        if "sms_example" in st.session_state:
            st.info(f"Copied! Paste this in the SMS box above:\n\n{st.session_state['sms_example']}")

    # ── Bulk SMS ───────────────────────────────────────────
    with tab2:
        st.subheader("Paste multiple SMS messages")
        st.caption("Put each SMS on a new line")

        bulk_input = st.text_area(
            "Multiple SMS (one per line)",
            height=250,
            placeholder="""INR 320.00 debited for Swiggy on 01-03-24
Rs.180 debited for Uber on 02-03-24
INR 499.00 debited for Netflix on 03-03-24
INR 1800.00 debited for Electricity Bill on 05-03-24"""
        )

        if st.button("📦 Import All", type="primary"):
            if bulk_input.strip():
                sms_list = [
                    line.strip()
                    for line in bulk_input.strip().split("\n")
                    if line.strip()
                ]
                with st.spinner(f"Importing {len(sms_list)} SMS messages..."):
                    r = requests.post(
                        f"{API}/sms/bulk-import",
                        json={"sms_list": sms_list}
                    )
                data = r.json()
                clear_cache()
                st.success(f"✅ Imported **{data['imported']}** transactions")
                if data["skipped"]:
                    st.warning(f"⚠️ Skipped {data['skipped']} messages (couldn't parse)")

                if data["results"]:
                    st.subheader("Imported:")
                    for res in data["results"]:
                        saved = res["saved"]
                        icon = "💸" if res["type"] == "expense" else "💵"
                        st.write(
                            f"{icon} **{saved['description']}** "
                            f"— ₹{saved['amount']:,.2f}"
                        )                

# ─── PAGE: MANAGE ─────────────────────────────────────────────────────────────
elif page == "⚙️ Manage":
    st.title("⚙️ Manage Transactions")

    df = fetch_transactions()

    if df.empty:
        st.info("No transactions to manage.")
        st.stop()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    tab1, tab2 = st.tabs(["✏️ Edit / Update", "🗑️ Delete"])

    with tab1:
        st.subheader("Update a Transaction")
        update_id = st.selectbox("Select transaction ID", df["id"].tolist())
        row = df[df["id"] == update_id].iloc[0]

        with st.form("update_form"):
            new_desc = st.text_input("Description", value=row["description"])
            new_amount = st.number_input("Amount (₹)", value=float(row["amount"]), min_value=0.01)
            new_cat = st.selectbox(
                "Category",
                ["food", "travel", "shopping", "entertainment", "health",
                 "utilities", "education", "finance", "uncategorized"],
                index=["food", "travel", "shopping", "entertainment", "health",
                       "utilities", "education", "finance", "uncategorized"].index(
                    row["category"] if row["category"] in
                    ["food","travel","shopping","entertainment","health",
                     "utilities","education","finance","uncategorized"] else "uncategorized"
                ),
            )
            if st.form_submit_button("Update", type="primary"):
                r = requests.put(
                    f"{API}/transactions/{update_id}",
                    json={"description": new_desc, "amount": new_amount, "category": new_cat},
                )
                if r.status_code == 200:
                    clear_cache()
                    st.success("✅ Updated!")
                    st.rerun()
                else:
                    st.error(f"Update failed: {r.text}")

    with tab2:
        st.subheader("Delete a Transaction")
        del_id = st.selectbox("Select transaction ID to delete", df["id"].tolist(), key="del")
        row_del = df[df["id"] == del_id].iloc[0]
        st.info(f"**{row_del['description']}** — ₹{row_del['amount']} on {str(row_del['date'])[:10]}")

        if st.button("🗑️ Delete", type="primary"):
            r = requests.delete(f"{API}/transactions/{del_id}")
            if r.status_code == 200:
                clear_cache()
                st.success("Deleted!")
                st.rerun()
            else:
                st.error(f"Delete failed: {r.text}")