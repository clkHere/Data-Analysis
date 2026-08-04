from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import datetime
import os
import plotly.express as px

# Automatically find the directory where app.py is located
BASE_DIR = Path(__file__).resolve().parent

# --- WHERE OUR DATA FILES LIVE ---
PRODUCTS_FILE = BASE_DIR / "Data" / "products.csv"
ACCOUNTS_FILE = BASE_DIR / "Data" / "accounts.csv"
PIPELINE_FILE = BASE_DIR / "Data" / "sales_pipeline.csv"
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

# --- EXECUTIVE DESIGN SYSTEM & CUSTOM CSS OVERRIDES ---
st.markdown("""
<style>
    /* 1. Global App & Background */
    .stApp {
        background-color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        color: #0F172A !important;
    }
    
    /* Clean Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0 !important;
    }

    /* Force all standard text elements to crisp typography */
    p, span, label, div, li, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #0F172A !important;
    }

    /* Force captions and small text to muted gray */
    .stCaption, small, [data-testid="stCaptionContainer"] p {
        color: #64748B !important;
        font-weight: 500 !important;
    }

    /* 2. Glass Cards */
    .glass-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 20px 24px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 16px !important;
    }

    /* 3. Typography Helpers */
    .metric-value {
        font-size: 2.25rem !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        line-height: 1.1 !important;
    }
    
    .metric-label {
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        color: #64748B !important;
        letter-spacing: 0.05em !important;
    }
    
    .field-value {
        color: #0F172A !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        margin-top: 2px !important;
    }

    /* 4. Streamlit Native Metrics Override */
    div[data-testid="stMetric"] {
        background-color: #FFFFFF !important;
        padding: 16px 20px !important;
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stMetricValue"] * {
        color: #0F172A !important;
        font-weight: 700 !important;
    }
    div[data-testid="stMetricLabel"] * {
        color: #64748B !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        font-size: 0.75rem !important;
        letter-spacing: 0.05em !important;
    }

    /* 5. Integrated Process Stepper Bar */
    .stepper-wrapper {
        display: flex;
        align-items: center;
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 4px;
        margin: 16px 0 24px 0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.02);
    }
    
    .step-item {
        flex: 1;
        text-align: center;
        padding: 8px 12px;
        font-size: 0.825rem;
        font-weight: 500;
        color: #64748B;
        border-radius: 6px;
        transition: all 0.2s ease;
    }
    
    .step-item.active {
        background-color: #2563EB;
        color: #FFFFFF !important;
        font-weight: 600;
        box-shadow: 0 2px 4px rgba(37, 99, 235, 0.18);
    }
    
    .step-item.completed {
        color: #0F172A;
        font-weight: 500;
    }

    /* 6. Form Inputs, Selectboxes & Textboxes */
    input, select, textarea, div[data-baseweb="input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
        border-radius: 6px !important;
    }

    /* 7. Modern Flat Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 28px !important;
        border-bottom: 1px solid #E2E8F0 !important;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 40px !important;
        white-space: pre-wrap !important;
        border-radius: 0px !important;
        color: #64748B !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        border-bottom: 2px solid transparent !important;
        padding: 0px 4px !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #2563EB !important;
        border-bottom: 2px solid #2563EB !important;
        background-color: transparent !important;
        font-weight: 600 !important;
    }

    /* 8. Modern Buttons */
    div.stButton > button {
        border-radius: 6px !important;
        border: 1px solid #CBD5E1 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        color: #334155 !important;
        background-color: #FFFFFF !important;
        transition: all 0.15s ease !important;
    }
    
    div.stButton > button:hover {
        border-color: #94A3B8 !important;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }

    div.stButton > button[kind="primary"] {
        background-color: #2563EB !important;
        border-color: #2563EB !important;
        color: #FFFFFF !important;
    }

    div.stButton > button[kind="primary"] * {
        color: #FFFFFF !important;
    }

    /* 9. Container Borders & Dividers */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04) !important;
    }

    hr {
        margin: 1.5rem 0 !important;
        border-color: #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

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
        title={"text": title, "font": {"size": 14, "color": "#0F172A", "family": "Arial, sans-serif"}},
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        margin=dict(l=20, r=20, t=40, b=20),
        font=dict(color="#64748B", size=11),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickangle=0,
            tickfont=dict(color="#0F172A", size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            zeroline=False,
            tickfont=dict(color="#0F172A", size=11)
        )
    )
    return fig

# --- LEFT-HAND SIDEBAR MENU ---
with st.sidebar:
    st.markdown("<h3 style='color: #0F172A; font-size: 1.1rem; font-weight: 700; margin-bottom: 0;'>⚡ Maven Experience</h3>", unsafe_allow_html=True)
    st.caption("CPQ Quoting Workspace")
    st.selectbox("App Switcher", ["Sales Console", "Service Cloud", "CPQ Quoting"], index=2, label_visibility="collapsed")
    
    st.markdown("---")
    
    st.caption("NAVIGATION")
    if st.button("🏠 Home", use_container_width=True, type="primary" if st.session_state.nav_page == "Home" else "secondary"):
        st.session_state.nav_page = "Home"
        st.rerun()
    if st.button("💼 Accounts", use_container_width=True, type="primary" if st.session_state.nav_page == "Accounts" else "secondary"):
        st.session_state.nav_page = "Accounts"
        st.rerun()
    if st.button("🎯 Opportunities", use_container_width=True, type="primary" if st.session_state.nav_page == "Opportunities" else "secondary"):
        st.session_state.nav_page = "Opportunities"
        st.rerun()
    if st.button("📄 Quotes", use_container_width=True, type="primary" if st.session_state.nav_page == "Quotes" else "secondary"):
        st.session_state.nav_page = "Quotes"
        st.rerun()
    if st.button("📦 Products", use_container_width=True, type="primary" if st.session_state.nav_page == "Products" else "secondary"):
        st.session_state.nav_page = "Products"
        st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("ENVIRONMENT")
    st.markdown("<p style='font-size: 0.8rem; color: #64748B; margin: 0;'>Maven Production (NA104)</p>", unsafe_allow_html=True)
    
    st.caption("USER")
    st.markdown("<p style='font-size: 0.8rem; color: #64748B; margin: 0;'>Calvin King (AE)</p>", unsafe_allow_html=True)

# --- PAGE 1: EXECUTIVE SALES DASHBOARD ---
if st.session_state.nav_page == "Home":
    st.markdown("""
    <div class="glass-card">
        <div class="metric-label">Executive Sales Console</div>
        <div style="font-size: 1.5rem; font-weight: 700; color: #0F172A; margin-top: 2px;">Calvin King — Sales Rep Performance Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # Top summary metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Pipeline Value", "$342,500", delta="+12.4% vs Q1")
    m2.metric("Quota Attainment", "78.5%", delta="+5.2%")
    m3.metric("Avg Win Rate", "64.2%", delta="+3.1%")
    m4.metric("Sales Cycle", "28 Days", delta="-4 Days")
    m5.metric("Open Proposals", "8 Quotes", delta="2 In Review")

    st.markdown("---")

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

            fig1 = px.bar(stage_df, x=stage_col, y=val_col, text_auto="$,.0f", color_discrete_sequence=["#2563EB"])
            fig1.update_traces(textposition="outside")
            apply_salesforce_theme(fig1, "1. Opportunity Stage Distribution ($)")
            st.plotly_chart(fig1, use_container_width=True)

    with row1_c2:
        with st.container(border=True):
            q_df = pd.DataFrame({
                "Category": ["Closed Revenue", "Quota Target"],
                "Amount": [157000, 200000]
            })
            fig2 = px.bar(q_df, x="Category", y="Amount", text_auto="$,.0f", color="Category", color_discrete_map={"Closed Revenue": "#059669", "Quota Target": "#64748B"})
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
            fig3 = px.line(trend_df, x="Month", y="Win Rate (%)", markers=True, color_discrete_sequence=["#2563EB"])
            apply_salesforce_theme(fig3, "3. Win Rate Trend (6 Months)")
            st.plotly_chart(fig3, use_container_width=True)

    with row2_c2:
        with st.container(border=True):
            prod_df = pd.DataFrame({
                "Product": ["GTX Basic", "MG Enterprise", "GTX Pro", "Service Package"],
                "Revenue": [85000, 120000, 64000, 32000]
            })
            fig4 = px.bar(prod_df, x="Product", y="Revenue", text_auto="$,.0f", color_discrete_sequence=["#3B82F6"])
            fig4.update_traces(textposition="outside")
            apply_salesforce_theme(fig4, "4. Top Product Revenue Contributions")
            st.plotly_chart(fig4, use_container_width=True)

    with row2_c3:
        with st.container(border=True):
            quote_df = pd.DataFrame({
                "Status": ["Draft", "In Review", "Approved", "Accepted"],
                "Count": [2, 3, 5, 8]
            })
            fig5 = px.bar(quote_df, x="Status", y="Count", text_auto=True, color_discrete_sequence=["#F59E0B"])
            fig5.update_traces(textposition="outside")
            apply_salesforce_theme(fig5, "5. Quotes by Approval Status")
            st.plotly_chart(fig5, use_container_width=True)

# --- PAGE 2: ACCOUNTS OVERVIEW ---
elif st.session_state.nav_page == "Accounts":
    st.markdown('<div class="glass-card"><div class="metric-label">Account Management</div><div style="font-size: 1.5rem; font-weight: 700; color: #0F172A;">Accounts Directory</div></div>', unsafe_allow_html=True)
    if df_accounts is not None:
        st.dataframe(df_accounts, use_container_width=True, hide_index=True)

# --- PAGE 3: OPPORTUNITIES OVERVIEW ---
elif st.session_state.nav_page == "Opportunities":
    st.markdown('<div class="glass-card"><div class="metric-label">Sales Pipeline</div><div style="font-size: 1.5rem; font-weight: 700; color: #0F172A;">Opportunities Overview</div></div>', unsafe_allow_html=True)
    if df_pipeline is not None:
        st.dataframe(df_pipeline, use_container_width=True, hide_index=True)

# --- PAGE 4: PRODUCTS CATALOG ---
elif st.session_state.nav_page == "Products":
    st.markdown('<div class="glass-card"><div class="metric-label">Catalog</div><div style="font-size: 1.5rem; font-weight: 700; color: #0F172A;">Products Catalog</div></div>', unsafe_allow_html=True)
    if df_products is not None:
        st.dataframe(df_products, use_container_width=True, hide_index=True)

# --- PAGE 5: QUOTE CREATION & DECISION SUPPORT ---
elif st.session_state.nav_page == "Quotes":

    # Header section with title and quick actions
    col_title, col_actions = st.columns([2.5, 2], gap="large")

    with col_title:
        st.caption("MAVEN QUOTE / Q-00124")
        st.markdown("<h1 style='margin-top: -8px; color: #0F172A; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em;'>Acme Corp Expansion</h1>", unsafe_allow_html=True)

    with col_actions:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        col_b, col_c, col_d, col_e = st.columns(4)
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
            if st.button("Send Email", type="primary", use_container_width=True):
                st.toast("Quote PDF emailed to customer!", icon="📧")

    # Interactive progress tracker for quote approval
    stages = ["Draft", "In Review", "Approved", "Presented", "Accepted", "Denied"]
    
    cols = st.columns(len(stages))
    for idx, stage in enumerate(stages):
        with cols[idx]:
            is_active = (stage == st.session_state.quote_status)
            btn_type = "primary" if is_active else "secondary"
            current_idx = stages.index(st.session_state.quote_status)
            stage_idx = stages.index(stage)
            
            label = f"✓ {stage}" if stage_idx < current_idx else (f"▶ {stage}" if is_active else stage)
            if st.button(label, key=f"stage_{stage}", use_container_width=True, type=btn_type):
                st.session_state.quote_status = stage
                st.rerun()

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

    left_col, right_col = st.columns([2.5, 1], gap="large")

    # MAIN CONTENT TABS
    with left_col:
        tab_details, tab_lines, tab_decision, tab_pdf = st.tabs([
            "Quote Details", 
            "Line Items (CPQ)", 
            "Decision Support", 
            "Document Preview"
        ])

        # TAB 1: BASIC QUOTE INFORMATION
        with tab_details:
            exp_date_str = (datetime.date.today() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
            st.markdown(f"""
            <div class="glass-card">
                <h4 style="color: #0F172A; font-size: 0.95rem; margin-bottom: 20px; font-weight: 600;">Information</h4>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px 16px;">
                    <div>
                        <div class="metric-label">Quote Number</div>
                        <div class="field-value">Q-00124</div>
                    </div>
                    <div>
                        <div class="metric-label">Account Executive</div>
                        <div class="field-value">Calvin King</div>
                    </div>
                    <div>
                        <div class="metric-label">Opportunity</div>
                        <div class="field-value" style="color: #2563EB;">Acme Corp - Enterprise Expansion</div>
                    </div>
                    <div>
                        <div class="metric-label">Expiration Date</div>
                        <div class="field-value">{exp_date_str}</div>
                    </div>
                    <div>
                        <div class="metric-label">Account Name</div>
                        <div class="field-value">Acme Corporation</div>
                    </div>
                    <div>
                        <div class="metric-label">Status</div>
                        <div class="field-value" style="color: #2563EB;">{st.session_state.quote_status}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # TAB 2: PRODUCT SELECTION & PRICE ADJUSTMENTS
        with tab_lines:
            with st.container(border=True):
                st.markdown('<div class="metric-label" style="margin-bottom: 12px;">Add Product & Set Offer Price</div>', unsafe_allow_html=True)
                
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
                st.markdown('<div class="metric-label" style="margin-bottom: 12px;">Line Item Editor</div>', unsafe_allow_html=True)
                
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

                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Subtotal (List)", f"${subtotal:,.2f}")
                m2.metric("Total Discount/Adder", f"-${total_discount:,.2f}" if total_discount >= 0 else f"+${abs(total_discount):,.2f} (Adder)")
                m3.metric("Grand Total (Offer)", f"${grand_total:,.2f}")

        # TAB 3: DECISION SUPPORT
        with tab_decision:
            with st.container(border=True):
                st.markdown('<div class="metric-label" style="margin-bottom: 12px;">Decision Intelligence & ASP Check-Down Analysis</div>', unsafe_allow_html=True)
                
                st.markdown('<div style="font-size:15px; font-weight:700; color:#0F172A; margin-bottom:12px;">Quote Level Summary</div>', unsafe_allow_html=True)
                ds_col1, ds_col2, ds_col3 = st.columns(3)
                total_units = int(df_items["Quantity"].sum()) if not df_items.empty else 0
                avg_discount = float(df_items["Discount (%)"].mean()) if not df_items.empty else 0.0

                ds_col1.metric("Total Quote Value", f"${grand_total:,.2f}")
                ds_col2.metric("Total Units", f"{total_units:,}")
                
                if avg_discount < 0:
                    ds_col3.metric("Average Price Adder", f"+{abs(avg_discount):.1f}%")
                else:
                    ds_col3.metric("Average Discount", f"{avg_discount:.1f}%")

                st.markdown("---")
                st.markdown('<div style="font-size:15px; font-weight:700; color:#0F172A; margin-bottom:16px;">Item-Level Predicted Win Rates & Margin Alerts</div>', unsafe_allow_html=True)
                
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

                # Render Line Item Analysis
                if not df_items.empty:
                    for idx, row in df_items.iterrows():
                        p_name = str(row["Product"])
                        l_price = float(row["List Price"])
                        o_price = float(row["Offer Price"])
                        qty = int(row["Quantity"])
                        disc_pct = float(row["Discount (%)"])

                        cost_basis = l_price * 0.65
                        achieved_margin = ((o_price - cost_basis) / o_price) * 100.0 if o_price > 0 else 0.0

                        logit_val = b0 + (b1_price * (o_price * qty)) + (b2_disc * disc_pct)
                        item_win_prob = safe_sigmoid(logit_val)

                        if o_price <= cost_basis:
                            margin_signal = "🔴 <strong style='color:#DC2626;'>RED (DANGER)</strong>"
                            msg = f"Offer Price (${o_price:,.2f}) is AT OR BELOW the 35% margin floor (${cost_basis:,.2f})."
                        elif achieved_margin <= 40.0:
                            margin_signal = "🟠 <strong style='color:#D97706;'>ORANGE (CAUTION)</strong>"
                            msg = f"Offer Price is within 5 margin percentage points of threshold. Achieved Margin: {achieved_margin:.1f}%."
                        else:
                            margin_signal = "🟢 <strong style='color:#059669;'>GREEN (HEALTHY)</strong>"
                            msg = f"Healthy margin achieved ({achieved_margin:.1f}%)."

                        st.markdown(f"<div style='font-size:14px; font-weight:700; color:#0F172A; margin-top:12px;'>Product: {p_name} — {margin_signal}</div>", unsafe_allow_html=True)
                        ic1, ic2 = st.columns([2, 3])

                        with ic1:
                            st.markdown(f"""
                            <div style='background-color:#F8FAFC; padding:12px 16px; border-radius:8px; border:1px solid #E2E8F0;'>
                                <div style='font-size:13px; color:#0F172A; font-weight:600;'>List Price: <span style='color:#2563EB;'>${l_price:,.2f}</span></div>
                                <div style='font-size:13px; color:#0F172A; font-weight:600; margin-top:4px;'>Offer Price: <span style='color:#2563EB;'>${o_price:,.2f}</span></div>
                                <div style='font-size:13px; color:#0F172A; font-weight:600; margin-top:4px;'>Discount: <span style='color:#059669;'>{disc_pct:.1f}%</span></div>
                            </div>
                            """, unsafe_allow_html=True)

                        with ic2:
                            st.markdown(f"""
                            <div style='background-color:#F8FAFC; padding:12px 16px; border-radius:8px; border:1px solid #E2E8F0;'>
                                <div style='font-size:13px; color:#0F172A; font-weight:600;'>Win Probability: <span style='color:#2563EB;'>{item_win_prob:.1f}%</span></div>
                                <div style='font-size:12px; color:#64748B; margin-top:4px;'>{msg}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)

        # TAB 4: DOCUMENT PREVIEW
        with tab_pdf:
            st.info("Generated PDF preview section goes here.")

    # --- RIGHT PANEL: SUMMARY & ACTIVITY FEED ---
    with right_col:
        st.markdown(f"""
        <div class="glass-card">
            <div class="metric-label">Grand Total</div>
            <div class="metric-value" style="margin-top: 4px;">${grand_total:,.2f}</div>
            <div style="margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: #64748B; margin-bottom: 6px; font-weight: 500;">
                    <span>Quota Target Progress ($100,000)</span>
                    <span>{(grand_total / 100000.0) * 100:.1f}%</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.progress(min(grand_total / 100000.0, 1.0))
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 12px;">
            <h4 style="color: #0F172A; font-size: 0.95rem; font-weight: 600; margin-bottom: 4px;">Activity Feed</h4>
            <p style="font-size: 0.8rem; color: #64748B; margin: 0;">Log calls, notes, or deal updates below.</p>
        </div>
        """, unsafe_allow_html=True)
        
        note_input = st.text_input(
            "Log Activity", 
            placeholder="Log call or update notes...", 
            label_visibility="collapsed"
        )
        if st.button("Log Activity", use_container_width=True):
            if note_input:
                st.toast(f"Activity logged: {note_input}", icon="📝")
            else:
                st.toast("Please enter a note before logging.", icon="⚠️")
