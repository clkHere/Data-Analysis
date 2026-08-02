import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import plotly.express as px

# --- WHERE OUR DATA FILES LIVE ---
PRODUCTS_FILE = "Data/products.csv"
ACCOUNTS_FILE = "Data/accounts.csv"
PIPELINE_FILE = "Data/sales_pipeline.csv"
LOGIT_SCRIPT_FILE = "Logit_Regressor.py"

# --- THE MUST-HAVE INFORMATION FOR EACH QUOTE ITEM ---
REQUIRED_COLUMNS = ["Product", "List Price", "Offer Price", "Quantity"]

# --- SET UP THE BROWSER TAB AND PAGE LAYOUT ---
st.set_page_config(
    page_title="Q-00124 | Maven Quote",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- LOAD DATA SAFELY IN THE BACKGROUND ---
@st.cache_data
def load_data(filepath):
    """Loads CSV files smoothly and lets us know if a file is missing."""
    if os.path.exists(filepath):
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            st.error(f"Error loading {filepath}: {e}")
            return None
    return None

df_products = load_data(PRODUCTS_FILE)
df_accounts = load_data(ACCOUNTS_FILE)
df_pipeline = load_data(PIPELINE_FILE)

# --- MAKE SURE QUOTE ITEMS HAVE ALL NECESSARY DETAILS ---
def ensure_line_items_schema(df):
    """Fills in any missing columns so the quote table never crashes or looks incomplete."""
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(columns=REQUIRED_COLUMNS)
    
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col in ["List Price", "Offer Price"]:
                df[col] = 0.0
            elif col == "Quantity":
                df[col] = 1
            else:
                df[col] = "Custom Product"
                
    df["List Price"] = pd.to_numeric(df["List Price"], errors="coerce").fillna(0.0)
    df["Offer Price"] = pd.to_numeric(df["Offer Price"], errors="coerce").fillna(0.0)
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(1).astype(int)
    df["Product"] = df["Product"].fillna("Custom Product").astype(str)
    
    return df[REQUIRED_COLUMNS]

# --- LIGHTNING CSS OVERRIDES (HIGH-CONTRAST LIGHT THEME) ---
st.markdown("""
<style>
    /* 1. Global App & Text Colors */
    .stApp {
        background-color: #ECEFEF !important;
        color: #2B2827 !important;
    }
    
    /* Force all standard text elements to dark slate for high contrast */
    p, span, label, div, li, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #16325C !important;
    }

    /* Force captions and small text to dark blue-gray */
    .stCaption, small, [data-testid="stCaptionContainer"] p {
        color: #54698D !important;
        font-weight: 600 !important;
    }

    /* 2. Header Card */
    .sf-header-card {
        background-color: #FFFFFF;
        padding: 16px 20px;
        border-radius: 8px;
        border: 1px solid #D8DDE6;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        margin-bottom: 16px;
    }
    .sf-object-label {
        font-size: 11px;
        text-transform: uppercase;
        color: #54698D !important;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .sf-record-name {
        font-size: 22px;
        font-weight: 700;
        color: #16325C !important;
        margin-top: 2px;
    }

    /* 3. Card Headers & Labels */
    .sf-card-header {
        font-size: 15px;
        font-weight: 700;
        color: #16325C !important;
        padding-bottom: 8px;
        border-bottom: 2px solid #0070D2;
        margin-bottom: 12px;
    }

    /* 4. Streamlit Metrics Override */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 14px 18px !important;
        border-radius: 6px !important;
        border: 1px solid #D8DDE6 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stMetricValue"] * {
        color: #16325C !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] * {
        color: #54698D !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        font-size: 12px !important;
    }

    /* 5. Clean Button Styling (Light Theme) */
    div.stButton > button {
        background-color: #FFFFFF !important;
        color: #0070D2 !important;
        border: 1px solid #D8DDE6 !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button:hover {
        background-color: #F4F6F9 !important;
        border-color: #0070D2 !important;
    }
    div.stButton > button[kind="primary"] {
        background-color: #0070D2 !important;
        border-color: #0070D2 !important;
        color: #FFFFFF !important;
    }
    div.stButton > button[kind="primary"] * {
        color: #FFFFFF !important;
    }

    /* 6. Fix Form Inputs & Textboxes */
    input, select, textarea, div[data-baseweb="input"] {
        background-color: #FFFFFF !important;
        color: #16325C !important;
        border-color: #C9C7C5 !important;
    }

    /* 7. Tab Headers Formatting */
    button[data-baseweb="tab"] * {
        color: #54698D !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    button[aria-selected="true"] * {
        color: #0070D2 !important;
    }
    
    /* 8. Container Border Boxes */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #D8DDE6 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- KEEP TRACK OF USER SELECTIONS & DEFAULTS ---
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "Quotes"

if "quote_status" not in st.session_state:
    st.session_state.quote_status = "In Review"

# Pre-populate sample quote items if the user hasn't added any yet
if "line_items" not in st.session_state:
    if df_products is not None and not df_products.empty:
        prod_col = [c for c in df_products.columns if "product" in c.lower()][0] if any("product" in c.lower() for c in df_products.columns) else df_products.columns[0]
        price_col = [c for c in df_products.columns if "price" in c.lower() or "cost" in c.lower()]
        price_col = price_col[0] if price_col else df_products.columns[1]

        p1_name = str(df_products.iloc[0][prod_col])
        p1_price = float(df_products.iloc[0][price_col]) if pd.notnull(df_products.iloc[0][price_col]) else 100.0
        
        p2_name = str(df_products.iloc[1][prod_col]) if len(df_products) > 1 else "Standard Service"
        p2_price = float(df_products.iloc[1][price_col]) if len(df_products) > 1 and pd.notnull(df_products.iloc[1][price_col]) else 50.0

        st.session_state.line_items = pd.DataFrame([
            {"Product": p1_name, "List Price": p1_price, "Offer Price": p1_price * 0.90, "Quantity": 1},
            {"Product": p2_name, "List Price": p2_price, "Offer Price": p2_price * 0.95, "Quantity": 1},
        ])
    else:
        st.session_state.line_items = pd.DataFrame([
            {"Product": "GTX Basic", "List Price": 550.00, "Offer Price": 495.00, "Quantity": 1},
            {"Product": "GTX Pro", "List Price": 4821.00, "Offer Price": 4579.95, "Quantity": 1},
        ])

st.session_state.line_items = ensure_line_items_schema(st.session_state.line_items)

# --- WIN PROBABILITY CALCULATOR ---
def safe_sigmoid(logit_val):
    """Converts price scores into a clean 0-100% win percentage."""
    clipped_val = np.clip(-logit_val, -500.0, 500.0)
    return (1.0 / (1.0 + np.exp(clipped_val))) * 100.0

# --- CHART DESIGN TEMPLATE ---
def apply_salesforce_theme(fig, title=""):
    """Applies clean enterprise colors, fonts, and clean layout to charts."""
    fig.update_layout(
        title={"text": title, "font": {"size": 14, "color": "#16325C", "family": "Arial, sans-serif"}},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#54698D", size=11),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickangle=0,
            tickfont=dict(color="#16325C", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E0E5EE",
            zeroline=False,
            tickfont=dict(color="#16325C", size=11)
        )
    )
    return fig

# --- LEFT-HAND SIDEBAR MENU ---
with st.sidebar:
    st.markdown("### ⚡ **Maven Experience**")
    st.selectbox("App Switcher", ["Sales Console", "Service Cloud", "CPQ Quoting"], index=2)
    st.divider()
    
    st.markdown("**Navigation**")
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.nav_page == "Home" else "secondary"):
        st.session_state.nav_page = "Home"
    if st.button("💼 Accounts", use_container_width=True, type="primary" if st.session_state.nav_page == "Accounts" else "secondary"):
        st.session_state.nav_page = "Accounts"
    if st.button("🎯 Opportunities", use_container_width=True, type="primary" if st.session_state.nav_page == "Opportunities" else "secondary"):
        st.session_state.nav_page = "Opportunities"
    if st.button("📄 Quotes", use_container_width=True, type="primary" if st.session_state.nav_page == "Quotes" else "secondary"):
        st.session_state.nav_page = "Quotes"
    if st.button("📦 Products", use_container_width=True, type="primary" if st.session_state.nav_page == "Products" else "secondary"):
        st.session_state.nav_page = "Products"
    
    st.divider()
    st.caption("Environment: **Maven Production (NA104)**")
    st.caption("Logged in as: **Calvin King (AE)**")

# --- PAGE 1: EXECUTIVE SALES DASHBOARD ---
if st.session_state.nav_page == "Home":
    st.markdown("""
    <div class="sf-header-card">
        <div class="sf-object-label">Executive Sales Console</div>
        <div class="sf-record-name">Calvin King — Sales Rep Performance Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Top summary metrics
    st.markdown("##### **Key Performance Indicators**")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Pipeline Value", "$342,500", delta="+12.4% vs Q1")
    m2.metric("Quota Attainment", "78.5%", delta="+5.2%")
    m3.metric("Avg Win Rate", "64.2%", delta="+3.1%")
    m4.metric("Sales Cycle", "28 Days", delta="-4 Days")
    m5.metric("Open Proposals", "8 Quotes", delta="2 In Review")

    st.divider()

    clean_pipe = df_pipeline.copy() if df_pipeline is not None else pd.DataFrame()
    
    row1_c1, row1_c2 = st.columns(2)

    with row1_c1:
        with st.container(border=True):
            if not clean_pipe.empty and "stage" in [c.lower() for c in clean_pipe.columns]:
                stage_col = [c for c in clean_pipe.columns if "stage" in c.lower()][0]
                val_col = [c for c in clean_pipe.columns if any(x in c.lower() for x in ["close_value", "val", "amount"])][0]
                stage_df = clean_pipe.groupby(stage_col)[val_col].sum().reset_index()
            else:
                stage_df = pd.DataFrame({
                    "Stage": ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won"],
                    "Value": [45000, 78000, 112000, 65000, 142000]
                })
                stage_col, val_col = "Stage", "Value"

            fig1 = px.bar(stage_df, x=stage_col, y=val_col, text_auto="$,.0f", color_discrete_sequence=["#0070D2"])
            fig1.update_traces(textposition="outside")
            apply_salesforce_theme(fig1, "1. Opportunity Stage Distribution ($)")
            st.plotly_chart(fig1, use_container_width=True)

    with row1_c2:
        with st.container(border=True):
            q_df = pd.DataFrame({
                "Category": ["Closed Revenue", "Quota Target"],
                "Amount": [157000, 200000]
            })
            fig2 = px.bar(q_df, x="Category", y="Amount", text_auto="$,.0f", color="Category", color_discrete_map={"Closed Revenue": "#2E8B57", "Quota Target": "#54698D"})
            fig2.update_traces(textposition="outside")
            apply_salesforce_theme(fig2, "2. Revenue Progress vs. Quota Goal ($)")
            st.plotly_chart(fig2, use_container_width=True)

    row2_c1, row2_c2, row2_c3 = st.columns(3)

    with row2_c1:
        with st.container(border=True):
            trend_df = pd.DataFrame({
                "Month": ["Feb", "Mar", "Apr", "May", "Jun", "Jul"],
                "Win Rate (%)": [52, 55, 58, 61, 62, 64]
            })
            fig3 = px.line(trend_df, x="Month", y="Win Rate (%)", markers=True, color_discrete_sequence=["#0070D2"])
            apply_salesforce_theme(fig3, "3. Win Rate Trend (6 Months)")
            st.plotly_chart(fig3, use_container_width=True)

    with row2_c2:
        with st.container(border=True):
            prod_df = pd.DataFrame({
                "Product": ["GTX Basic", "MG Enterprise", "GTX Pro", "Service Package"],
                "Revenue": [85000, 120000, 64000, 32000]
            })
            fig4 = px.bar(prod_df, x="Product", y="Revenue", text_auto="$,.0f", color_discrete_sequence=["#1B96FF"])
            fig4.update_traces(textposition="outside")
            apply_salesforce_theme(fig4, "4. Top Product Revenue Contributions")
            st.plotly_chart(fig4, use_container_width=True)

    with row2_c3:
        with st.container(border=True):
            quote_df = pd.DataFrame({
                "Status": ["Draft", "In Review", "Approved", "Accepted"],
                "Count": [2, 3, 5, 8]
            })
            fig5 = px.bar(quote_df, x="Status", y="Count", text_auto=True, color_discrete_sequence=["#FF9800"])
            fig5.update_traces(textposition="outside")
            apply_salesforce_theme(fig5, "5. Quotes by Approval Status")
            st.plotly_chart(fig5, use_container_width=True)

# --- PAGE 2: ACCOUNTS OVERVIEW ---
elif st.session_state.nav_page == "Accounts":
    st.markdown('<div class="sf-header-card"><div class="sf-object-label">Account Management</div><div class="sf-record-name">Accounts Directory</div></div>', unsafe_allow_html=True)
    if df_accounts is not None:
        st.dataframe(df_accounts, use_container_width=True, hide_index=True)

# --- PAGE 3: OPPORTUNITIES OVERVIEW ---
elif st.session_state.nav_page == "Opportunities":
    st.markdown('<div class="sf-header-card"><div class="sf-object-label">Sales Pipeline</div><div class="sf-record-name">Opportunities Overview</div></div>', unsafe_allow_html=True)
    if df_pipeline is not None:
        st.dataframe(df_pipeline, use_container_width=True, hide_index=True)

# --- PAGE 4: PRODUCTS CATALOG ---
elif st.session_state.nav_page == "Products":
    st.markdown('<div class="sf-header-card"><div class="sf-object-label">Catalog</div><div class="sf-record-name">Products Catalog</div></div>', unsafe_allow_html=True)
    if df_products is not None:
        st.dataframe(df_products, use_container_width=True, hide_index=True)

# --- PAGE 5: QUOTE CREATION & DECISION SUPPORT ---
elif st.session_state.nav_page == "Quotes":

    # Header section with action buttons
    st.markdown("""
    <div class="sf-header-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="sf-object-label">Maven Quote</div>
                <div class="sf-record-name">Q-00124 — Acme Corp Expansion</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1])
    with col_b:
        if st.button("Edit Details", use_container_width=True):
            st.toast("Opening Record Editor...", icon="✏️")
    with col_c:
        if st.button("Sync Quote", use_container_width=True):
            st.toast("Quote synced with Opportunity Opp-49211!", icon="🔄")
    with col_d:
        if st.button("Create PDF", use_container_width=True):
            st.toast("Generating PDF Document...", icon="📄")
    with col_e:
        if st.button("Send Email", use_container_width=True):
            st.toast("Quote PDF emailed to customer!", icon="📧")

    # Interactive progress tracker for quote approval
    stages = ["Draft", "In Review", "Approved", "Presented", "Accepted", "Denied"]
    current_idx = stages.index(st.session_state.quote_status)

    cols = st.columns(len(stages))
    for idx, stage in enumerate(stages):
        with cols[idx]:
            btn_type = "primary" if idx == current_idx else "secondary"
            label = f"✓ {stage}" if idx < current_idx else (f"▶ {stage}" if idx == current_idx else stage)
            if st.button(label, key=f"stage_{stage}", use_container_width=True, type=btn_type):
                st.session_state.quote_status = stage
                st.rerun()

    st.divider()

    left_col, right_col = st.columns([2.3, 1])

    # Calculate pricing, discounts, and totals
    df_items = ensure_line_items_schema(st.session_state.line_items.copy())
    
    if not df_items.empty:
        df_items["Total Price"] = df_items["Offer Price"] * df_items["Quantity"]
        df_items["Discount (%)"] = np.where(
            df_items["List Price"] > 0,
            ((df_items["List Price"] - df_items["Offer Price"]) / df_items["List Price"]) * 100.0,
            0.0
        )
        subtotal = (df_items["List Price"] * df_items["Quantity"]).sum()
        grand_total = df_items["Total Price"].sum()
        total_discount = subtotal - grand_total
    else:
        subtotal, total_discount, grand_total = 0.0, 0.0, 0.0

    # MAIN CONTENT TABS
    with left_col:
        tab_details, tab_lines, tab_decision, tab_pdf = st.tabs([
            "📋 Quote Details", 
            "📦 Line Items (CPQ)", 
            "📊 Decision Support", 
            "📄 Document Preview"
        ])

        # TAB 1: BASIC QUOTE INFORMATION
        with tab_details:
            with st.container(border=True):
                st.markdown('<div class="sf-card-header">Information</div>', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Quote Number</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">Q-00124</div>', unsafe_allow_html=True)
                    st.markdown('<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Opportunity</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">🔗 Acme Corp - Enterprise Expansion</div>', unsafe_allow_html=True)
                    st.markdown('<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Account Name</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">🏢 Acme Corporation</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown('<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Account Executive (AE)</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">👤 Calvin King</div>', unsafe_allow_html=True)
                    st.markdown(f'<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Expiration Date</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">{(datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div><strong style="color:#54698D; font-size:11px; text-transform:uppercase;">Status</strong></div><div style="font-size:15px; font-weight:600; color:#16325C; margin-bottom:12px;">{st.session_state.quote_status}</div>', unsafe_allow_html=True)

        # TAB 2: PRODUCT SELECTION & PRICE ADJUSTMENTS
        with tab_lines:
            with st.container(border=True):
                st.markdown('<div class="sf-card-header">Add Product & Set Offer Price</div>', unsafe_allow_html=True)
                
                if df_products is not None and not df_products.empty:
                    prod_col = [c for c in df_products.columns if "product" in c.lower()][0] if any("product" in c.lower() for c in df_products.columns) else df_products.columns[0]
                    price_col = [c for c in df_products.columns if "price" in c.lower() or "cost" in c.lower()]
                    price_col = price_col[0] if price_col else df_products.columns[1]

                    prod_list = df_products[prod_col].astype(str).tolist()
                    col_p1, col_p2, col_p3, col_p4 = st.columns([3, 1.5, 1, 1])
                    with col_p1:
                        selected_prod = st.selectbox("Select Product", prod_list, key="cat_prod_select")
                    
                    matched_row = df_products[df_products[prod_col].astype(str) == selected_prod]
                    default_list_price = float(matched_row.iloc[0][price_col]) if not matched_row.empty and pd.notnull(matched_row.iloc[0][price_col]) else 100.0

                    with col_p2:
                        custom_offer_price = st.number_input("Set Offer Price ($)", min_value=0.01, value=default_list_price, step=10.0, key="cat_offer_price")
                    with col_p3:
                        add_qty = st.number_input("Quantity", min_value=1, value=1, key="cat_qty")

                    with col_p4:
                        st.write("")
                        st.write("")
                        if st.button("➕ Add", type="primary", use_container_width=True):
                            new_item = {
                                "Product": selected_prod,
                                "List Price": default_list_price,
                                "Offer Price": custom_offer_price,
                                "Quantity": add_qty
                            }
                            updated_df = pd.concat([st.session_state.line_items, pd.DataFrame([new_item])], ignore_index=True)
                            st.session_state.line_items = ensure_line_items_schema(updated_df)
                            st.toast(f"Added {selected_prod} to Quote!", icon="✅")
                            st.rerun()

            with st.container(border=True):
                st.markdown('<div class="sf-card-header">Line Item Editor</div>', unsafe_allow_html=True)
                
                edited_df = st.data_editor(
                    st.session_state.line_items,
                    num_rows="dynamic",
                    use_container_width=True,
                    column_config={
                        "List Price": st.column_config.NumberColumn("List Price ($)", format="$%.2f", disabled=True),
                        "Offer Price": st.column_config.NumberColumn("Offer Price ($)", format="$%.2f", min_value=0.01),
                        "Quantity": st.column_config.NumberColumn("Quantity", min_value=1, step=1),
                    },
                    key="quote_editor"
                )

                st.session_state.line_items = ensure_line_items_schema(edited_df)

                st.divider()
                m1, m2, m3 = st.columns(3)
                m1.metric("Subtotal (List)", f"${subtotal:,.2f}")
                m2.metric("Total Discount/Adder", f"-${total_discount:,.2f}" if total_discount >= 0 else f"+${abs(total_discount):,.2f} (Adder)")
                m3.metric("Grand Total (Offer)", f"${grand_total:,.2f}")

        # TAB 3: DECISION SUPPORT
        with tab_decision:
            with st.container(border=True):
                st.markdown('<div class="sf-card-header">Decision Intelligence & ASP Check-Down Analysis</div>', unsafe_allow_html=True)
                
                st.markdown('<div style="font-size:16px; font-weight:700; color:#16325C; margin-bottom:12px;">Quote Level Summary</div>', unsafe_allow_html=True)
                ds_col1, ds_col2, ds_col3 = st.columns(3)
                total_units = int(df_items["Quantity"].sum()) if not df_items.empty else 0
                avg_discount = float(df_items["Discount (%)"].mean()) if not df_items.empty else 0.0

                ds_col1.metric("Total Quote Value", f"${grand_total:,.2f}")
                ds_col2.metric("Total Units", f"{total_units:,}")
                
                if avg_discount < 0:
                    ds_col3.metric("Average Price Adder", f"+{abs(avg_discount):.1f}%")
                else:
                    ds_col3.metric("Average Discount", f"{avg_discount:.1f}%")

                st.divider()
                st.markdown('<div style="font-size:16px; font-weight:700; color:#16325C; margin-bottom:16px;">Item-Level Predicted Win Rates & Margin Alerts</div>', unsafe_allow_html=True)
                
                # Baseline scoring weights for calculating win probability
                b0 = 0.85
                b1_price = -0.000025
                b2_disc = 0.035

                p_col, v_col, q_col, s_col = None, None, None, None
                clean_pipeline = pd.DataFrame()

                if df_pipeline is not None and not df_pipeline.empty:
                    clean_pipeline = df_pipeline.copy()
                    cols_map = {str(c).lower().strip(): c for c in clean_pipeline.columns}

                    p_col = next((cols_map[k] for k in cols_map if any(x in k for x in ["product", "item", "sku"])), None)
                    v_col = next((cols_map[k] for k in cols_map if any(x in k for x in ["close_value", "close value", "amount", "price", "val"])), None)
                    q_col = next((cols_map[k] for k in cols_map if any(x in k for x in ["qty", "quantity", "unit"])), None)
                    s_col = next((cols_map[k] for k in cols_map if any(x in k for x in ["sector", "industry", "category"])), None)

                    if v_col:
                        clean_pipeline[v_col] = pd.to_numeric(clean_pipeline[v_col], errors='coerce')
                        clean_pipeline = clean_pipeline[clean_pipeline[v_col].notnull() & (clean_pipeline[v_col] > 0)]

                    if q_col:
                        clean_pipeline[q_col] = pd.to_numeric(clean_pipeline[q_col], errors='coerce').fillna(1)
                        clean_pipeline[q_col] = np.where(clean_pipeline[q_col] <= 0, 1, clean_pipeline[q_col])
                    else:
                        clean_pipeline["_units"] = 1
                        q_col = "_units"

                    if v_col and q_col:
                        clean_pipeline["Unit_Price"] = clean_pipeline[v_col] / clean_pipeline[q_col]

                # Render Line Item Analysis with Closed Won Deals in Median Window
                if not df_items.empty:
                    for idx, row in df_items.iterrows():
                        p_name = str(row["Product"])
                        l_price = float(row["List Price"])
                        o_price = float(row["Offer Price"])
                        qty = int(row["Quantity"])
                        disc_pct = float(row["Discount (%)"])

                        cost_basis = l_price * 0.65
                        achieved_margin = ((o_price - cost_basis) / o_price) * 100.0 if o_price > 0 else 0.0

                        # Benchmark & Days-to-Close metrics for each product
                        item_median_price = None
                        won_above_count = 0
                        won_below_count = 0
                        median_days_window = None

                        if not clean_pipeline.empty and p_col:
                            item_deals = clean_pipeline[clean_pipeline[p_col].astype(str) == p_name].copy()
                            
                            if not item_deals.empty and "Unit_Price" in item_deals.columns:
                                item_median_price = item_deals["Unit_Price"].median()

                            # Identify date and stage columns
                            date_cols = {str(c).lower().strip(): c for c in item_deals.columns}
                            engage_k = next((date_cols[k] for k in date_cols if "engage" in k), None)
                            close_k = next((date_cols[k] for k in date_cols if "close_date" in k or "close date" in k), None)
                            stage_k = next((date_cols[k] for k in date_cols if "stage" in k), None)

                            if engage_k and close_k and stage_k:
                                item_deals[engage_k] = pd.to_datetime(item_deals[engage_k], errors='coerce')
                                item_deals[close_k] = pd.to_datetime(item_deals[close_k], errors='coerce')
                                item_deals["days_to_close"] = (item_deals[close_k] - item_deals[engage_k]).dt.days

                                won_deals = item_deals[
                                    (item_deals[stage_k].astype(str).str.lower().str.contains("won")) &
                                    (item_deals["days_to_close"].notnull()) &
                                    (item_deals["days_to_close"] >= 0)
                                ]

                                if not won_deals.empty:
                                    median_days_window = won_deals["days_to_close"].median()
                                    in_window_deals = won_deals[won_deals["days_to_close"] <= median_days_window]
                                    
                                    won_above_count = int((in_window_deals["Unit_Price"] > o_price).sum())
                                    won_below_count = int((in_window_deals["Unit_Price"] <= o_price).sum())

                        logit_val = b0 + (b1_price * (o_price * qty)) + (b2_disc * disc_pct)
                        item_win_prob = safe_sigmoid(logit_val)

                        if o_price <= cost_basis:
                            margin_signal = "🔴 <strong style='color:#C23934;'>RED (DANGER)</strong>"
                            margin_status = "error"
                            msg = f"Offer Price (${o_price:,.2f}) is AT OR BELOW the 35% margin floor (${cost_basis:,.2f})."
                        elif achieved_margin <= 40.0:
                            margin_signal = "🟠 <strong style='color:#DD7A00;'>ORANGE (CAUTION)</strong>"
                            margin_status = "warning"
                            msg = f"Offer Price is within 5 margin percentage points of threshold. Achieved Margin: {achieved_margin:.1f}%."
                        else:
                            margin_signal = "🟢 <strong style='color:#027E46;'>GREEN (HEALTHY)</strong>"
                            margin_status = "success"
                            msg = f"Healthy margin achieved ({achieved_margin:.1f}%)."

                        st.markdown(f"<div style='font-size:15px; font-weight:700; color:#16325C;'>Product: {p_name} — {margin_signal}</div>", unsafe_allow_html=True)
                        ic1, ic2, ic3 = st.columns([1.5, 1.5, 2])

                        with ic1:
                            st.markdown(f"""
                            <div style='background-color:#F3F5F8; padding:10px 14px; border-radius:6px; border:1px solid #D8DDE6; margin-top:4px;'>
                                <div style='font-size:13px; color:#16325C; font-weight:600;'>List Price: <span style='color:#0070D2;'>${l_price:,.2f}</span></div>
                                <div style='font-size:13px; color:#16325C; font-weight:600; margin-top:2px;'>Offer Price: <span style='color:#0070D2;'>${o_price:,.2f}</span></div>
                                <div style='font-size:13px; color:#16325C; font-weight:600; margin-top:2px;'>Discount: <span style='color:#2E8B57;'>{disc_pct:.1f}%</span></div>
                            </div>
                            """, unsafe_allow_html=True)

                        with ic2:
                            st.metric("Predicted Win Rate", f"{item_win_prob:.1f}%")
                            
                            if median_days_window is not None and not np.isnan(median_days_window):
                                st.markdown(f"""
                                <div style='font-size:12px; font-weight:600; color:#54698D; margin-top:6px;'>
                                    <strong>Closed Won Deals (≤ {int(median_days_window)} Days):</strong><br/>
                                    • Above Offer Price (${o_price:,.2f}): <span style='color:#027E46; font-weight:700;'>{won_above_count} deals</span><br/>
                                    • At/Below Offer Price: <span style='color:#C23934; font-weight:700;'>{won_below_count} deals</span>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown("<div style='font-size:12px; font-weight:600; color:#54698D;'>(Insufficient cycle/stage data)</div>", unsafe_allow_html=True)

                        with ic3:
                            if margin_status == "error":
                                st.error(msg)
                            elif margin_status == "warning":
                                st.warning(msg)
                            else:
                                st.success(msg)

                        st.divider()
                else:
                    st.info("No line items currently on quote.")

                # HISTORICAL BENCHMARK & PRICING RECOMMENDATIONS
                st.markdown('<div style="font-size:16px; font-weight:700; color:#16325C; margin-bottom:12px;">Similar Benchmark Opportunities & Price Recommendations</div>', unsafe_allow_html=True)
                
                quote_products = df_items["Product"].astype(str).unique().tolist() if not df_items.empty else []

                if not clean_pipeline.empty and quote_products and p_col:
                    target_median = None
                    methodology_used = ""
                    bench_df = pd.DataFrame()

                    tier1_df = clean_pipeline[clean_pipeline[p_col].astype(str).isin(quote_products)]
                    if not tier1_df.empty and "Unit_Price" in tier1_df.columns and tier1_df["Unit_Price"].notnull().any():
                        target_median = tier1_df["Unit_Price"].median()
                        methodology_used = "Tier 1 — Filtered using exact product matches currently present on this quote."
                        bench_df = tier1_df.copy()

                    if target_median is not None and not np.isnan(target_median):
                        st.info(f"ℹ️ **Methodology:** {methodology_used}")
                        
                        current_avg_unit = grand_total / total_units if total_units > 0 else 0.0
                        var_from_med = current_avg_unit - target_median
                        var_pct_med = (var_from_med / target_median) * 100.0 if target_median > 0 else 0.0

                        mc1, mc2, mc3 = st.columns(3)
                        with mc1:
                            st.metric("Quote Avg Unit Price", f"${current_avg_unit:,.2f}")
                        with mc2:
                            st.metric("Benchmark Median ASP", f"${target_median:,.2f}")
                        with mc3:
                            st.metric("Variance vs Benchmark", f"${var_from_med:,.2f}", delta=f"{var_pct_med:+.1f}%", delta_color="normal")

                        st.markdown('<div style="font-size:14px; font-weight:700; color:#16325C; margin-top:12px; margin-bottom:6px;">Price Recommendation</div>', unsafe_allow_html=True)
                        if abs(var_from_med) <= (0.02 * target_median):
                            st.success("💡 Pricing is aligned with the benchmark median for similar opportunities.")
                        elif var_from_med < 0:
                            rec_total = abs(var_from_med) * total_units
                            st.warning(f"💡 Increase price by **${abs(var_from_med):,.2f}/unit** ({abs(var_pct_med):.1f}%) to match benchmark median. Capture adds **${rec_total:,.2f}** in quote value.")
                        else:
                            st.info(f"💡 Decrease price by **${var_from_med:,.2f}/unit** ({var_pct_med:.1f}%) if buyer price resistance occurs.")

                        st.markdown('<div style="font-size:14px; font-weight:700; color:#16325C; margin-top:12px; margin-bottom:6px;">Historical Benchmark Opportunities</div>', unsafe_allow_html=True)
                        st.dataframe(bench_df.head(10), use_container_width=True, hide_index=True)
                    else:
                        st.warning("⚠️ No comparable benchmark available.")

        # TAB 4: PRINTABLE CLIENT PROPOSAL PREVIEW
        with tab_pdf:
            with st.container(border=True):
                st.markdown('<div class="sf-card-header">Generated Maven Proposal</div>', unsafe_allow_html=True)
                st.markdown(f"""
                ### **MAVEN PROPOSAL / QUOTE**
                **Quote Number:** Q-00124  
                **Account Executive:** Calvin King  
                **Date:** {datetime.date.today().strftime('%B %d, %Y')}  
                **Prepared For:** Acme Corporation  
                """, unsafe_allow_html=True)
                
                if not df_items.empty:
                    proposal_df = df_items[["Product", "Quantity", "Offer Price", "Total Price"]].copy()
                    st.table(proposal_df.style.format({
                        "Offer Price": "${:.2f}",
                        "Total Price": "${:.2f}"
                    }))
                else:
                    st.write("No line items on quote.")
                
                st.markdown(f"**Grand Total:** `${grand_total:,.2f}`")

    # RIGHT-HAND SIDEBAR SUMMARY & LOGS
    with right_col:
        with st.container(border=True):
            st.markdown('<div class="sf-card-header">Totals Summary</div>', unsafe_allow_html=True)
            st.metric("Grand Total", f"${grand_total:,.2f}")
            st.progress(min(1.0, grand_total / 100000.0), text="Quota Target Progress ($100,000)")

        with st.container(border=True):
            st.markdown('<div class="sf-card-header">Activity Feed</div>', unsafe_allow_html=True)
            st.text_input("Log activity...", placeholder="Log call or update notes...", key="act_input")
            if st.button("Log Activity", use_container_width=True):
                st.success("Activity logged!")

            st.divider()
            st.markdown('<div style="font-size:14px; font-weight:700; color:#16325C; margin-bottom:8px;">Recent History</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:12px; font-weight:600; color:#54698D; margin-bottom:6px;">📌 <strong style="color:#16325C;">Stage updated</strong> to <em>In Review</em> — Today</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:12px; font-weight:600; color:#54698D; margin-bottom:6px;">📧 <strong style="color:#16325C;">Email sent:</strong> <em>Quote Q-00124 attached</em> — Yesterday</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:12px; font-weight:600; color:#54698D;">✏️ <strong style="color:#16325C;">Quote Created</strong> by Calvin King — 2 days ago</div>', unsafe_allow_html=True)
