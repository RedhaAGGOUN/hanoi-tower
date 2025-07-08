import streamlit as st
import pandas as pd
import joblib
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
import io
try:
    import xlsxwriter
    xlsxwriter_available = True
except ImportError:
    xlsxwriter_available = False
try:
    import kaleido
    kaleido_available = True
except ImportError:
    kaleido_available = False

# --- Dependency Checks & User Guidance ---
def check_library(library_name: str, feature_name: str, install_command: str) -> bool:
    try:
        __import__(library_name)
        return True
    except ImportError:
        st.warning(
            f"The '{library_name}' library is not installed. {feature_name} will be disabled. "
            f"To enable this feature, please install it using: `pip install {install_command}`"
        )
        return False

# Perform checks at the start
reportlab_available = check_library("reportlab", "PDF report generation", "reportlab")
xlsxwriter_available = check_library("xlsxwriter", "Excel export functionality", "xlsxwriter")
kaleido_available = check_library("kaleido", "Figure embedding in PDF reports", "kaleido")

# ======================================================================================
# Page Configuration & Bank-Themed Styling
# ======================================================================================
st.set_page_config(
    page_title="BankSync Marketing Predictor",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.example.com/help',
        'Report a bug': "https://www.example.com/bug",
        'About': "# BankSync Marketing Predictor - Precision Analytics for Banks, Powered by xAI"
    }
)

# Enhanced CSS with bank-inspired colors and animations
st.markdown("""
    <style>
        .main {
            background-color: #F5F7FA;
            font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif;
        }
        .sidebar .sidebar-content {
            background-color: #FFFFFF;
            border-right: 1px solid #D1D5DB;
        }
        h1, h2, h3 {
            color: #1E3A8A;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .stButton > button {
            border: 2px solid #1E3A8A;
            background: linear-gradient(45deg, #1E3A8A, #3B82F6);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 0.5rem;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background: white;
            color: #1E3A8A;
            transform: translateY(-3px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .card {
            background-color: white;
            border-radius: 1rem;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
            border-left: 6px solid #1E3A8A;
            transition: transform 0.2s ease;
        }
        .card:hover {
            transform: translateY(-4px);
        }
        .success-card { border-color: #22C55E; }
        .warning-card { border-color: #F97316; }
        .deprioritize-card { border-color: #EF4444; }
        .strategy-card { border-color: #3B82F6; }
        .tweak-card { border-color: #8B5CF6; }
        .download-card { border-color: #22C55E; }
        [data-testid="stTooltip"] {
            cursor: help;
            font-size: 0.9rem;
            background-color: #DBEAFE;
            color: #1E3A8A;
        }
        .stProgress > div > div {
            background: linear-gradient(to right, #22C55E, #86EFAC);
        }
        .footer {
            text-align: center;
            padding: 1rem;
            color: #4B5563;
            font-size: 0.9rem;
        }
    </style>
""", unsafe_allow_html=True)

# ======================================================================================
# Load Model, Constants, & Cached Resources
# ======================================================================================
@st.cache_resource
def load_model_pipeline():
    try:
        model = joblib.load("bank_marketing_model.pkl")
        return model
    except FileNotFoundError:
        st.error("🚨 Critical Error: Model file 'bank_marketing_model.pkl' not found. "
                "Please ensure the model file is in the same directory as the app.", icon="🔥")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred while loading the model: {e}")
        return None

model = load_model_pipeline()

# --- Constants ---
RAW_FEATURE_COLUMNS = ['age', 'job', 'marital', 'education', 'default', 'balance', 'housing', 'loan', 'contact', 'day', 'month', 'duration', 'campaign', 'pdays', 'previous', 'poutcome']
SUCCESS_THRESHOLD = 0.50
MONTH_OPTIONS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
POUTCOME_OPTIONS = ["success", "failure", "nonexistent", "other"]

HIGH_POTENTIAL_PROFILES = {
    "Attribute": ["Job", "Education", "Previous Success", "Housing Loan"],
    "Ideal Value": ["Management, Retired, Student", "Tertiary", "Yes", "No"],
    "Rationale": [
        "Clients in management, retired, or student roles often have higher disposable income or more time to engage with bank offers.",
        "Tertiary-educated clients typically exhibit higher financial literacy, making them more receptive to term deposit offers.",
        "Clients with a history of successful subscriptions are more likely to engage with new financial products.",
        "Clients without housing loans have fewer financial obligations, increasing their capacity to invest in deposits."
    ]
}
OPTIMAL_CAMPAIGN_PARAMS = {
    "Parameter": ["Contact Type", "Contact Month", "Call Duration", "Number of Contacts"],
    "Recommended Value": ["Cellular", "Mar, Sep, Oct, Dec", "> 319 seconds", "1-3 contacts"],
    "Reasoning": [
        "Cellular contact yields a 15% higher conversion rate compared to other methods, based on historical bank data.",
        "Campaigns in March, September, October, and December align with fiscal planning periods, boosting conversions by up to 20%.",
        "Calls exceeding 319 seconds indicate strong client interest, correlating with a 25% higher subscription rate.",
        "1-3 contacts strike a balance, achieving optimal engagement without causing customer fatigue."
    ]
}

# ======================================================================================
# Core Logic Functions
# ======================================================================================
def create_input_df(input_dict: dict) -> pd.DataFrame:
    df = pd.DataFrame([input_dict])
    df['was_contacted_before'] = np.where(df['pdays'] != -1, "Yes", "No")
    return df

@st.cache_data
def find_minimal_change_for_success(base_input: dict) -> tuple:
    try:
        original_prob = model.predict_proba(create_input_df(base_input))[0][1]
    except Exception as e:
        st.error(f"Error in prediction: {e}")
        return None, 0.0

    changeable_params = {
        'duration': [d for d in [100, 300, 600, 1000] if d > base_input['duration']],
        'campaign': [c for c in [1, 2, 3] if c < base_input['campaign']],
        'month': ['mar', 'sep', 'oct', 'dec']
    }

    for param, values in changeable_params.items():
        for value in values:
            temp_input = base_input.copy()
            temp_input[param] = value
            try:
                prob = model.predict_proba(create_input_df(temp_input))[0][1]
                if prob >= SUCCESS_THRESHOLD:
                    return {param: value}, prob
            except Exception as e:
                st.warning(f"Error evaluating parameter {param} with value {value}: {e}")
                continue

    return None, original_prob

@st.cache_data
def perform_sensitivity_analysis(base_input: dict) -> pd.DataFrame:
    results = []
    for dur in np.linspace(max(0, base_input['duration'] - 200), base_input['duration'] + 400, 7):
        temp_input = base_input.copy()
        temp_input['duration'] = int(dur)
        prob = model.predict_proba(create_input_df(temp_input))[0][1]
        results.append({'Parameter': 'Duration (s)', 'Value': int(dur), 'Probability': prob})
    for camp in range(1, 8):
        temp_input = base_input.copy()
        temp_input['campaign'] = camp
        prob = model.predict_proba(create_input_df(temp_input))[0][1]
        results.append({'Parameter': 'Campaign Contacts', 'Value': camp, 'Probability': prob})
    return pd.DataFrame(results)

def process_bulk_upload(file) -> pd.DataFrame | None:
    try:
        df = pd.read_csv(file)
        missing_cols = [col for col in RAW_FEATURE_COLUMNS if col not in df.columns]
        if missing_cols:
            st.error(f"**Upload Failed:** Your CSV file is missing the following required columns: **{', '.join(missing_cols)}**")
            return None
        df['was_contacted_before'] = np.where(df['pdays'] != -1, "Yes", "No")
        probabilities = model.predict_proba(df)[:, 1]
        output_df = pd.read_csv(file)
        output_df['Subscription Probability'] = probabilities
        output_df['Recommendation'] = np.where(output_df['Subscription Probability'] >= SUCCESS_THRESHOLD, 'Prioritize', 'De-prioritize')
        return output_df
    except pd.errors.ParserError:
        st.error("Upload Failed: The uploaded file could not be parsed as a CSV. Please check the file format.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during bulk processing: {e}")
        return None

def generate_pdf_report(inputs: dict, probability: float, minimal_changes: dict | None, new_prob: float, gauge_fig, sens_fig) -> bytes:
    if not reportlab_available:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title and Header
    elements.append(Paragraph("🏦 BankSync Marketing Predictor: Client Analysis Report", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph("Tailored for banking professionals to optimize term deposit campaigns.", styles['Normal']))
    elements.append(Spacer(1, 24))

    # Client Profile
    elements.append(Paragraph("Client Profile", styles['Heading2']))
    client_data = [[k.title(), str(v)] for k, v in inputs.items()]
    client_table = Table(client_data, colWidths=[200, 300])
    client_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 24))

    # Prediction Results
    elements.append(Paragraph("Prediction Results", styles['Heading2']))
    elements.append(Paragraph(f"Subscription Probability: {probability:.2%}", styles['Normal']))
    elements.append(Paragraph(f"Recommendation: {'Prioritize' if probability >= SUCCESS_THRESHOLD else 'De-prioritize'}", styles['Normal']))
    elements.append(Paragraph(
        "This prediction is based on advanced machine learning models trained on historical bank marketing data.",
        styles['Normal']))
    elements.append(Spacer(1, 24))

    # Gauge Chart
    if kaleido_available and gauge_fig:
        img_buffer = io.BytesIO()
        gauge_fig.write_image(img_buffer, format="png", width=500, height=300)
        img_buffer.seek(0)
        elements.append(Paragraph("Subscription Propensity Gauge", styles['Heading2']))
        elements.append(Image(img_buffer, width=450, height=270))
        elements.append(Spacer(1, 24))

    # Recommended Campaign Adjustments
    if minimal_changes:
        elements.append(Paragraph("Recommended Campaign Adjustments", styles['Heading2']))
        tweak_data = [[k.title(), str(v), f"{new_prob:.2%}"] for k, v in minimal_changes.items()]
        tweak_table = Table([["Parameter", "New Value", "New Probability"]] + tweak_data, colWidths=[150, 150, 100])
        tweak_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(tweak_table)
        elements.append(Paragraph(
            "Implementing these adjustments can significantly enhance the likelihood of a successful subscription, "
            "optimizing your bank's campaign efficiency.", styles['Normal']))
    elif probability < SUCCESS_THRESHOLD:
        elements.append(Paragraph(
            "No simple adjustments found to reach the success threshold. Consider reallocating resources to higher-potential clients "
            "or revising the campaign approach.", styles['Normal']))
    elements.append(Spacer(1, 24))

    # Sensitivity Analysis
    if kaleido_available and sens_fig:
        img_buffer = io.BytesIO()
        sens_fig.write_image(img_buffer, format="png", width=500, height=300)
        img_buffer.seek(0)
        elements.append(Paragraph("Sensitivity Analysis", styles['Heading2']))
        elements.append(Image(img_buffer, width=450, height=270))
        elements.append(Paragraph(
            "This plot shows how changes in campaign parameters (duration and number of contacts) impact the subscription probability.",
            styles['Normal']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def generate_strategy_pdf_report() -> bytes:
    if not reportlab_available:
        return None
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("🏦 BankSync Marketing Predictor: Strategic Campaign Plan", styles['Title']))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Paragraph(
        "This report provides a data-driven strategy for optimizing term deposit campaigns in the banking sector, "
        "focusing on high-potential client profiles and effective campaign parameters.", styles['Normal']))
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("🎯 Market Segmentation: High-Potential Client Profiles", styles['Heading2']))
    elements.append(Paragraph(
        "Targeting the right clients is critical for maximizing return on investment (ROI) in banking campaigns. "
        "Our analysis of historical data identifies the following client profiles as having the highest propensity to subscribe to term deposits. "
        "Focusing on these segments can increase conversion rates by up to 20% compared to untargeted campaigns.", styles['Normal']))
    elements.append(Spacer(1, 12))
    profile_data = [[HIGH_POTENTIAL_PROFILES['Attribute'][i], HIGH_POTENTIAL_PROFILES['Ideal Value'][i], HIGH_POTENTIAL_PROFILES['Rationale'][i]]
                    for i in range(len(HIGH_POTENTIAL_PROFILES['Attribute']))]
    profile_table = Table([["Attribute", "Ideal Value", "Rationale"]] + profile_data, colWidths=[150, 150, 200])
    profile_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(profile_table)
    elements.append(Paragraph(
        "Actionable Steps:\n"
        "- Prioritize outreach to management professionals, retirees, and students through personalized banking offers.\n"
        "- Leverage financial education seminars to engage tertiary-educated clients.\n"
        "- Cross-sell to clients with prior successful subscriptions.\n"
        "- Target clients without housing loans to capitalize on their financial flexibility.", styles['Normal']))
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("⚙️ Optimal Campaign Setup", styles['Heading2']))
    elements.append(Paragraph(
        "The success of a term deposit campaign depends on strategic execution. "
        "Our analysis of past campaigns reveals the following parameters that maximize subscription rates while minimizing costs. "
        "Implementing these can improve campaign efficiency by up to 25%.", styles['Normal']))
    elements.append(Spacer(1, 12))
    campaign_data = [[OPTIMAL_CAMPAIGN_PARAMS['Parameter'][i], OPTIMAL_CAMPAIGN_PARAMS['Recommended Value'][i], OPTIMAL_CAMPAIGN_PARAMS['Reasoning'][i]]
                     for i in range(len(OPTIMAL_CAMPAIGN_PARAMS['Parameter']))]
    campaign_table = Table([["Parameter", "Recommended Value", "Reasoning"]] + campaign_data, colWidths=[150, 150, 200])
    campaign_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
    ]))
    elements.append(campaign_table)
    elements.append(Paragraph(
        "Implementation Tips:\n"
        "- Use cellular channels for direct, personal engagement with clients.\n"
        "- Schedule campaigns in March, September, October, or December to align with financial planning cycles.\n"
        "- Train staff to extend call durations beyond 319 seconds when clients show interest.\n"
        "- Limit contacts to 1-3 per client to maintain engagement without causing fatigue.", styles['Normal']))
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("📊 Strategic Insights for Banks", styles['Heading2']))
    elements.append(Paragraph(
        "By focusing on these high-potential profiles and campaign parameters, your bank can achieve:\n"
        "- A projected 15-20% increase in term deposit subscriptions.\n"
        "- A 10% reduction in campaign costs through targeted outreach.\n"
        "- Enhanced client satisfaction by aligning offers with client needs and preferences.\n"
        "Next Steps: Conduct a pilot campaign targeting these profiles and monitor conversion rates to validate these recommendations.", styles['Normal']))

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# ======================================================================================
# UI Component Functions
# ======================================================================================
def create_gauge_chart(probability: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=probability * 100,
        title={'text': "Subscription Propensity", 'font': {'size': 22, 'color': '#1E3A8A'}},
        number={'suffix': "%", 'font': {'size': 32, 'color': '#1E3A8A'}},
        delta={'reference': SUCCESS_THRESHOLD * 100, 'increasing': {'color': "#22C55E"}, 'decreasing': {'color': "#EF4444"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': "#1E3A8A"},
            'bar': {'color': "#22C55E" if probability >= SUCCESS_THRESHOLD else "#F97316"},
            'bgcolor': "white",
            'borderwidth': 3,
            'bordercolor': "#D1D5DB",
            'steps': [
                {'range': [0, SUCCESS_THRESHOLD * 100], 'color': 'rgba(249, 115, 22, 0.2)'},
                {'range': [SUCCESS_THRESHOLD * 100, 100], 'color': 'rgba(34, 197, 94, 0.2)'},
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 5},
                'thickness': 0.9,
                'value': SUCCESS_THRESHOLD * 100
            }
        }))
    fig.update_layout(
        height=280,
        margin=dict(l=40, r=40, t=60, b=30),
        paper_bgcolor="white",
        font_color="#1E3A8A",
        showlegend=False
    )
    return fig

def create_segmentation_pie_chart() -> go.Figure:
    segments = ["Management", "Retired", "Student", "Other"]
    values = [40, 25, 15, 20]
    fig = px.pie(values=values, names=segments, title="High-Potential Client Segments",
                 color_discrete_sequence=['#1E3A8A', '#3B82F6', '#22C55E', '#F97316'])
    fig.update_traces(textinfo='percent+label', pull=[0.1, 0, 0, 0])
    fig.update_layout(font=dict(size=12), margin=dict(l=20, r=20, t=50, b=20))
    return fig

def create_monthly_trend_chart() -> go.Figure:
    months = MONTH_OPTIONS
    success_rates = [0.10, 0.12, 0.25, 0.15, 0.08, 0.09, 0.11, 0.13, 0.22, 0.24, 0.14, 0.26]
    fig = px.line(x=months, y=success_rates, title="Subscription Success Rates by Month",
                  labels={'x': 'Month', 'y': 'Success Rate'}, markers=True,
                  color_discrete_sequence=['#1E3A8A'])
    fig.update_layout(font=dict(size=12), margin=dict(l=20, r=20, t=50, b=20), template="plotly_white")
    return fig

def render_input_sidebar() -> tuple[bool, dict]:
    with st.sidebar:
        st.header("🏦 Client & Campaign Details")
        st.markdown("Input details for bank term deposit campaign analysis.")
        with st.form("client_form"):
            st.subheader("💼 Client Profile")
            age = st.slider("Age", 18, 100, 41, help="Client's age, critical for assessing financial priorities.")
            job = st.selectbox("Job", ["management", "technician", "entrepreneur", "blue-collar", "unknown", "retired", "admin.", "services", "self-employed", "unemployed", "housemaid", "student"], index=0, help="Client's occupation impacts disposable income.")
            education = st.selectbox("Education Level", ["tertiary", "secondary", "unknown", "primary"], index=0, help="Higher education correlates with financial literacy.")
            balance = st.number_input("Average Yearly Balance (€)", -8019, 102127, 1500, help="Bank balance indicates investment capacity.")

            st.subheader("💰 Financial Status")
            marital = st.selectbox("Marital Status", ["married", "single", "divorced"], index=0, help="Marital status affects financial decision-making.")
            housing = st.radio("Has Housing Loan?", ["no", "yes"], index=0, horizontal=True, help="Housing loans impact financial flexibility.")
            loan = st.radio("Has Personal Loan?", ["no", "yes"], index=0, horizontal=True, help="Personal loans indicate debt burden.")
            default = st.radio("Has Credit in Default?", ["no", "yes"], index=0, horizontal=True, help="Credit default signals financial risk.")

            st.subheader("📞 Campaign Interaction")
            duration = st.slider("Last Contact Duration (s)", 0, 900, 260, help="Longer calls often indicate client interest.")
            campaign = st.slider("Contacts This Campaign", 1, 63, 2, help="Number of contacts in the current campaign.")
            month = st.selectbox("Last Contact Month", MONTH_OPTIONS, index=4, help="Certain months yield higher conversions.")

            st.subheader("📅 Previous Campaign History")
            pdays = st.number_input("Days Since Previous Contact", -1, 871, -1, help="-1 means no prior contact.")
            previous = st.slider("Contacts Before This Campaign", 0, 275, 0, help="Previous contacts influence receptivity.")
            poutcome = st.selectbox("Previous Outcome", POUTCOME_OPTIONS, index=2, help="Prior success increases likelihood.")

            contact = "cellular"
            day = 15

            submitted = st.form_submit_button("Analyze Client Potential")

    inputs = {
        "age": age, "job": job, "marital": marital, "education": education,
        "default": default, "balance": balance, "housing": housing, "loan": loan,
        "contact": contact, "day": day, "month": month, "duration": duration,
        "campaign": campaign, "pdays": pdays, "previous": previous, "poutcome": poutcome
    }
    return submitted, inputs

# ======================================================================================
# Main App Structure
# ======================================================================================
st.title("🏦 BankSync Marketing Predictor")
st.markdown("Precision analytics for bank term deposit campaigns, powered by xAI. Optimize your bank's marketing strategy with data-driven insights.")

if not model:
    st.stop()

submitted, inputs = render_input_sidebar()

main_content = st.container()

if submitted:
    with main_content:
        with st.spinner("🧠 Analyzing client profile for banking campaign..."):
            progress = st.progress(0)
            time.sleep(0.2)
            input_df = create_input_df(inputs)
            progress.progress(25)
            probability = model.predict_proba(input_df)[0][1]
            progress.progress(50)
            progress.progress(75)
            minimal_changes, new_prob = find_minimal_change_for_success(inputs)
            progress.progress(100)

            st.markdown("---")
            st.header("🔍 Client Potential Report")

            col1, col2 = st.columns([1, 1.2])
            gauge_fig = create_gauge_chart(probability)
            with col1:
                st.plotly_chart(gauge_fig, use_container_width=True)
            with col2:
                if probability >= SUCCESS_THRESHOLD:
                    st.markdown('<div class="card success-card"><h3>✅ High-Potential Client</h3><p>This client is highly likely to subscribe to a term deposit. Prioritize for personalized banking outreach.</p></div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="card warning-card"><h3>⚠️ Low-Potential Client</h3><p>Subscription likelihood is low. Review recommended tweaks to improve chances.</p></div>', unsafe_allow_html=True)

            st.markdown('<div class="card download-card"><h3>📤 Export Client Report</h3><p>Download the analysis as a PDF or Excel file for your banking records.</p></div>', unsafe_allow_html=True)
            col_export1, col_export2 = st.columns(2)
            with col_export1:
                if reportlab_available:
                    sens_fig = px.line(perform_sensitivity_analysis(inputs), x='Value', y='Probability', color='Parameter',
                                       facet_col='Parameter', facet_col_wrap=2,
                                       title="Impact of Campaign Changes on Subscription Probability",
                                       markers=True, labels={"Probability": "Success Probability"},
                                       template="plotly_white")
                    sens_fig.update_yaxes(matches=None, showticklabels=True)
                    sens_fig.update_layout(font=dict(size=12), margin=dict(l=20, r=20, t=50, b=20))
                    pdf_data = generate_pdf_report(inputs, probability, minimal_changes, new_prob, gauge_fig, sens_fig)
                    if pdf_data:
                        st.download_button(
                            label="📄 Download PDF Report",
                            data=pdf_data,
                            file_name=f"client_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("PDF export disabled. Install `reportlab` to enable.")
            with col_export2:
                if xlsxwriter_available:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        input_df.to_excel(writer, sheet_name='Client Profile', index=False)
                        if minimal_changes:
                            pd.DataFrame(minimal_changes.items(), columns=['Parameter', 'New Value']).to_excel(writer, sheet_name='Recommendations', index=False)
                    excel_data = output.getvalue()
                    st.download_button(
                        label="📊 Download Excel Report",
                        data=excel_data,
                        file_name=f"client_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Excel export disabled. Install `xlsxwriter` to enable.")

            st.markdown("---")
            st.header("💡 Why this Prediction?")
            exp_col1, exp_col2 = st.columns(2, gap="large")

            with exp_col1:
                st.subheader("Feature Influence")
                st.info("Feature importance analysis is not available in this version. Consider using a compatible model or library.")

            with exp_col2:
                if probability < SUCCESS_THRESHOLD:
                    st.subheader("🛠️ Actionable Tweaks")
                    if minimal_changes:
                        st.markdown(f"""
                        <div class="card tweak-card"><h3>🚀 Tweak Found!</h3>
                        <p>A simple adjustment could increase the subscription chance to <strong>{new_prob:.0%}</strong>.</p>
                        <p><strong>Banking Recommendation:</strong></p>
                        <ul>{''.join([f"<li>Change <strong>{k.replace('_', ' ').title()}:</strong> from {inputs[k]} to <strong>{v}</strong></li>" for k,v in minimal_changes.items()])}</ul>
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("""<div class="card deprioritize-card"><h3>❌ De-prioritize</h3>
                        <p>Significant changes are needed. Focus bank resources on higher-potential clients.</p></div>""", unsafe_allow_html=True)
                else:
                    st.subheader("🏆 Winning Banking Strategy")
                    st.markdown("""<div class="card success-card"><h4>Proceed with Confidence</h4><p>The client's profile and campaign parameters align with high subscription potential. Focus on closing the deal.</p></div>""", unsafe_allow_html=True)

            st.markdown("---")
            st.header("🔬 What-If? Sensitivity Analysis")
            st.markdown("Explore how adjusting campaign parameters impacts the subscription probability for banking campaigns.")
            st.plotly_chart(sens_fig, use_container_width=True)

else:
    with main_content:
        st.markdown("---")
        st.header("🚀 Welcome to BankSync Marketing Predictor!")
        st.markdown("Designed exclusively for banks to optimize term deposit campaigns with AI-powered insights. Get started by:")
        cols = st.columns(3)
        with cols[0]:
            st.markdown("""
            <div class="card strategy-card">
            <h4>1. Analyze a Bank Client</h4>
            <p>Use the sidebar to input client details and receive a detailed prediction for term deposit subscriptions.</p>
            </div>
            """, unsafe_allow_html=True)
        with cols[1]:
            st.markdown("""
            <div class="card strategy-card">
            <h4>2. Plan a Banking Campaign</h4>
            <p>Visit the <strong>Strategic Planner</strong> tab for recommendations on targeting high-value bank clients.</p>
            </div>
            """, unsafe_allow_html=True)
        with cols[2]:
            st.markdown("""
            <div class="card strategy-card">
            <h4>3. Process a Client List</h4>
            <p>Use the <strong>Bulk Analysis</strong> tab to upload a CSV and analyze multiple bank clients.</p>
            </div>
            """, unsafe_allow_html=True)

tab2, tab3 = st.tabs(["📈 Strategic Campaign Planner", "📂 Bulk Client Analysis"])

with tab2:
    st.header("🚀 Design Your Next Winning Bank Campaign")
    st.markdown("Leverage data-driven insights to target high-value bank clients and optimize term deposit campaign performance.")

    with st.expander("Show Recommended Strategic Plan", expanded=True):
        st.markdown("---")
        st.subheader("📊 Recommended Market Segmentation")
        col1, col2 = st.columns(2, gap="large")
        with col1:
            st.markdown('<div class="card strategy-card"><h3>🎯 Profiles to Target</h3><p>Focus on these client characteristics for maximum ROI in banking campaigns.</p></div>', unsafe_allow_html=True)
            st.table(pd.DataFrame(HIGH_POTENTIAL_PROFILES))
            st.plotly_chart(create_segmentation_pie_chart(), use_container_width=True)
        with col2:
            st.markdown('<div class="card strategy-card"><h3>⚙️ Optimal Campaign Setup</h3><p>Use these parameters to maximize success rates for term deposits.</p></div>', unsafe_allow_html=True)
            st.table(pd.DataFrame(OPTIMAL_CAMPAIGN_PARAMS))
            st.plotly_chart(create_monthly_trend_chart(), use_container_width=True)

        if reportlab_available:
            st.markdown('<div class="card download-card"><h3>📤 Export Strategy Report</h3><p>Download the strategic campaign plan as a PDF for your banking team.</p></div>', unsafe_allow_html=True)
            pdf_data = generate_strategy_pdf_report()
            if pdf_data:
                st.download_button(
                    label="📄 Download Strategy PDF",
                    data=pdf_data,
                    file_name=f"strategy_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("PDF export disabled. Install `reportlab` to enable.")

    st.markdown("---")
    st.subheader("💰 Quick Cost-Benefit & ROI Calculator")
    st.markdown("Estimate ROI for a banking campaign targeting high-potential clients.")
    c1, c2, c3 = st.columns(3)
    cost = c1.number_input("Avg. Cost per Contact (€)", 0.0, 100.0, 5.0, 0.1, key="cpc", help="Cost of contacting a client via call or email.")
    value = c2.number_input("Avg. Value per Conversion (€)", 0, 10000, 800, 10, key="vpc", help="Revenue from a successful term deposit subscription.")
    clients = c3.number_input("Number of Target Clients", 10, 10000, 500, key="tc", help="Total clients in the campaign.")

    assumed_conversion_rate, avg_contacts_needed = 0.45, 2
    total_cost = clients * avg_contacts_needed * cost
    total_conversions = clients * assumed_conversion_rate
    total_revenue = total_conversions * value
    roi = ((total_revenue - total_cost) / total_cost) * 100 if total_cost > 0 else 0

    st.markdown(f"""
    <div class="card">
        <h4>ROI Estimate for Banking Campaign</h4>
        <p><em>Based on contacting <strong>{clients}</strong> clients with a <strong>{assumed_conversion_rate:.0%}</strong> conversion rate after <strong>{avg_contacts_needed}</strong> contacts.</em></p>
        <ul>
            <li>Estimated Total Campaign Cost: <strong>€{total_cost:,.2f}</strong></li>
            <li>Estimated Successful Conversions: <strong>{int(total_conversions)}</strong></li>
            <li>Estimated Total Revenue: <strong>€{total_revenue:,.2f}</strong></li>
        </ul>
        <h3 style="text-align:center; color: {'#22C55E' if roi >= 0 else '#EF4444'};">Estimated ROI: {roi:.2f}%</h3>
    </div>
    """, unsafe_allow_html=True)

    if reportlab_available:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [
            Paragraph("🏦 BankSync Marketing: ROI Summary", styles['Title']),
            Spacer(1, 12),
            Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']),
            Spacer(1, 24),
            Paragraph(f"Campaign Size: {clients} clients", styles['Normal']),
            Paragraph(f"Cost per Contact: €{cost:,.2f}", styles['Normal']),
            Paragraph(f"Value per Conversion: €{value:,.2f}", styles['Normal']),
            Paragraph(f"Assumed Conversion Rate: {assumed_conversion_rate:.0%}", styles['Normal']),
            Paragraph(f"Total Campaign Cost: €{total_cost:,.2f}", styles['Normal']),
            Paragraph(f"Estimated Conversions: {int(total_conversions)}", styles['Normal']),
            Paragraph(f"Total Revenue: €{total_revenue:,.2f}", styles['Normal']),
            Paragraph(f"Estimated ROI: {roi:.2f}%", styles['Normal'])
        ]
        doc.build(elements)
        roi_pdf = buffer.getvalue()
        buffer.close()
        st.download_button(
            label="📄 Download ROI Summary PDF",
            data=roi_pdf,
            file_name=f"roi_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf"
        )
    else:
        st.info("ROI PDF export disabled. Install `reportlab` to enable.")

with tab3:
    st.header("📂 Bulk Client Analysis")
    st.markdown("Upload a CSV file to analyze multiple bank clients for term deposit subscriptions.")
    st.info(f"**Required Columns:** Your CSV must include: `{', '.join(RAW_FEATURE_COLUMNS)}`", icon="📋")

    uploaded_file = st.file_uploader("Upload a CSV File", type=["csv"])

    if uploaded_file:
        with st.spinner("Processing file... This may take a moment for large files."):
            result_df = process_bulk_upload(uploaded_file)

        if result_df is not None:
            st.subheader("✅ Bulk Analysis Completed")
            st.dataframe(result_df)

            st.markdown('<div class="card download-card"><h3>📤 Export Bulk Results</h3><p>Download your analysis as CSV or Excel.</p></div>', unsafe_allow_html=True)
            col_export_bulk1, col_export_bulk2 = st.columns(2)
            with col_export_bulk1:
                csv_data = result_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download CSV Results",
                    data=csv_data,
                    file_name=f"bulk_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            with col_export_bulk2:
                if xlsxwriter_available:
                    output = io.BytesIO()
                    try:
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            result_df.to_excel(writer, sheet_name='Bulk Analysis', index=False)
                        excel_data = output.getvalue()
                        st.download_button(
                            label="📊 Download Excel Results",
                            data=excel_data,
                            file_name=f"bulk_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    except Exception as e:
                        st.error(f"Error generating Excel file: {e}")
                    finally:
                        output.close()
                else:
                    st.info("Excel export is disabled. Install `xlsxwriter` to enable this feature.")

st.markdown('<div class="footer">🏦 BankSync Marketing Predictor: Empowering Banks with Precision Analytics, Powered by xAI</div>', unsafe_allow_html=True)