import streamlit as st
import pandas as pd
import joblib
import numpy as np

# Set page config for better appearance
st.set_page_config(page_title="Bank Marketing Predictor", page_icon="📊", layout="wide")

# Custom CSS for styling
st.markdown("""
    <style>
    .main { background-color: #f5f7fa; }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .st-expander { border: 1px solid #e0e0e0; border-radius: 8px; }
    .prediction-box, .recommendation-box, .strategy-box { 
        padding: 20px; 
        border-radius: 10px; 
        text-align: center; 
        font-size: 1.2em; 
    }
    .success-box { background-color: #e6f4ea; border: 2px solid #4CAF50; }
    .warning-box { background-color: #fff3e0; border: 2px solid #ff9800; }
    .recommendation-box { background-color: #e3f2fd; border: 2px solid #2196F3; }
    .strategy-box { background-color: #f3e5f5; border: 2px solid #9c27b0; }
    .stForm { border: 1px solid #e0e0e0; padding: 20px; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# Load the saved PyCaret model
model = joblib.load("bank_marketing_model.pkl")

# Title and description
st.title("📊 Bank Marketing Term Deposit Predictor")
st.markdown("""
    This app helps you **predict** whether a client will subscribe to a term deposit and provides tailored recommendations.  
    - If a client is unlikely to subscribe, get **recommendations** to adjust campaign parameters.  
    - For prioritized clients, get the **optimal marketing strategy** and ideal client profile to target.  
    Enter the client details below and choose an action.
""")

# Input form with organized sections
with st.form("client_form"):
    # Personal Information
    with st.expander("👤 Personal Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            age = st.slider("Age", min_value=18, max_value=100, value=30, help="Client's age (18-100)")
            marital = st.selectbox("Marital Status", ["married", "divorced", "single"], help="Client's marital status")
        with col2:
            job = st.selectbox("Job", [
                "admin.", "unknown", "unemployed", "management", "housemaid", 
                "entrepreneur", "student", "blue-collar", "self-employed", 
                "retired", "technician", "services"
            ], help="Client's occupation")
            education = st.selectbox("Education", ["unknown", "secondary", "primary", "tertiary"], help="Client's education level")

    # Financial Information
    with st.expander("💰 Financial Information"):
        col1, col2 = st.columns(2)
        with col1:
            default = st.selectbox("Credit in Default?", ["no", "yes"], help="Does the client have credit in default?")
            housing = st.selectbox("Has Housing Loan?", ["yes", "no"], help="Does the client have a housing loan?")
        with col2:
            balance = st.number_input("Average Yearly Balance (€)", min_value=-10000, max_value=100000, value=0, step=100, help="Client's average yearly balance in Euros")
            loan = st.selectbox("Has Personal Loan?", ["yes", "no"], help="Does the client have a personal loan?")

    # Campaign Information
    with st.expander("📞 Campaign Details"):
        col1, col2 = st.columns(2)
        with col1:
            contact = st.selectbox("Contact Communication Type", ["unknown", "telephone", "cellular"], help="Type of contact communication")
            day = st.slider("Last Contact Day of Month", min_value=1, max_value=31, value=15, help="Day of the month of last contact")
            month = st.selectbox("Last Contact Month", [
                "jan", "feb", "mar", "apr", "may", "jun", 
                "jul", "aug", "sep", "oct", "nov", "dec"
            ], help="Month of last contact")
        with col2:
            duration = st.slider("Last Contact Duration (seconds)", min_value=0, max_value=5000, value=200, help="Duration of last contact in seconds")
            campaign = st.slider("Number of Contacts during Campaign", min_value=1, max_value=50, value=1, help="Number of contacts in this campaign")
            pdays = st.number_input("Days since Previous Contact", min_value=-1, max_value=999, value=-1, help="Days since last contact (-1 if never contacted)")
            previous = st.slider("Number of Previous Contacts", min_value=0, max_value=50, value=0, help="Number of contacts before this campaign")
            poutcome = st.selectbox("Outcome of Previous Campaign", ["unknown", "other", "failure", "success"], help="Outcome of the previous campaign")

    # Buttons for prediction and optimal strategy
    col1, col2 = st.columns(2)
    with col1:
        predict_submitted = st.form_submit_button("🔍 Predict Subscription")
    with col2:
        strategy_submitted = st.form_submit_button("📋 Optimal Client Strategy")

# Function to create input DataFrame
def create_input_df(input_dict):
    input_df = pd.DataFrame([input_dict])
    input_df['was_contacted_before'] = input_df['pdays'].apply(lambda x: "No" if x == -1 else "Yes")
    return input_df

# Input validation function
def validate_inputs(balance, pdays):
    errors = []
    if not (-10000 <= balance <= 100000):
        errors.append("Balance must be between -10,000 and 100,000.")
    if not (-1 <= pdays <= 999):
        errors.append("Days since previous contact must be between -1 and 999.")
    return errors

# Function to recommend campaign adjustments for non-subscribers
def recommend_for_non_subscriber(base_input):
    contact_options = ["cellular", "telephone", "unknown"]
    month_options = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    duration_options = [100, 300, 500, 1000, 1500]
    campaign_options = [1, 2, 3, 5, 7]
    poutcome_options = ["success", "failure", "other", "unknown"]

    best_confidence = 0
    best_params = {}

    with st.spinner("Analyzing campaign adjustments to encourage subscription..."):
        for contact in contact_options:
            for month in month_options:
                for duration in duration_options:
                    for campaign in campaign_options:
                        for poutcome in poutcome_options:
                            input_dict = base_input.copy()
                            input_dict.update({
                                "contact": contact,
                                "month": month,
                                "duration": duration,
                                "campaign": campaign,
                                "poutcome": poutcome,
                            })
                            input_df = create_input_df(input_dict)
                            try:
                                confidence = model.predict_proba(input_df)[0][1] * 100  # Probability of subscribing
                                if confidence > best_confidence:
                                    best_confidence = confidence
                                    best_params = {
                                        "Contact Type": contact,
                                        "Month": month.capitalize(),
                                        "Call Duration (seconds)": duration,
                                        "Number of Contacts": campaign,
                                        "Previous Campaign Outcome": poutcome,
                                    }
                            except AttributeError:
                                continue

    return best_params, best_confidence

# Handle prediction
if predict_submitted:
    errors = validate_inputs(balance, pdays)
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Create input dictionary
        input_dict = {
            "age": age,
            "job": job,
            "marital": marital,
            "education": education,
            "default": default,
            "balance": balance,
            "housing": housing,
            "loan": loan,
            "contact": contact,
            "day": day,
            "month": month,
            "duration": duration,
            "campaign": campaign,
            "pdays": pdays,
            "previous": previous,
            "poutcome": poutcome,
        }

        # Create DataFrame
        input_df = create_input_df(input_dict)

        # Display loading spinner
        with st.spinner("Predicting..."):
            prediction = model.predict(input_df)[0]
            try:
                confidence = model.predict_proba(input_df)[0][prediction] * 100
            except AttributeError:
                confidence = None

        # Display prediction result
        if prediction == 1:
            st.markdown(f"""
                <div class="prediction-box success-box">
                    <h3>✅ Likely to Subscribe!</h3>
                    <p>This client is likely to subscribe to the term deposit.</p>
                    {"<p>Confidence: {:.2f}%</p>".format(confidence) if confidence else ""}
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="prediction-box warning-box">
                    <h3>⚠️ Unlikely to Subscribe</h3>
                    <p>This client is not likely to subscribe to the term deposit.</p>
                    {"<p>Confidence: {:.2f}%</p>".format(confidence) if confidence else ""}
                </div>
            """, unsafe_allow_html=True)
            
            # Recommend adjustments for non-subscribers
            base_input = {
                "age": age,
                "job": job,
                "marital": marital,
                "education": education,
                "default": default,
                "balance": balance,
                "housing": housing,
                "loan": loan,
                "day": day,
                "pdays": pdays,
                "previous": previous,
            }
            best_params, best_confidence = recommend_for_non_subscriber(base_input)
            if best_params:
                st.markdown(f"""
                    <div class="recommendation-box">
                        <h3>📋 Recommendations to Encourage Subscription</h3>
                        <p>To increase the chance of this client subscribing (confidence: {best_confidence:.2f}%):</p>
                        <ul style="text-align: left; margin: 0 auto; display: inline-block;">
                            <li><b>Contact Type</b>: {best_params['Contact Type'].capitalize()}</li>
                            <li><b>Month</b>: {best_params['Month']}</li>
                            <li><b>Call Duration</b>: {best_params['Call Duration (seconds)']} seconds</li>
                            <li><b>Number of Contacts</b>: {best_params['Number of Contacts']}</li>
                            <li><b>Previous Campaign Outcome</b>: {best_params['Previous Campaign Outcome'].capitalize()}</li>
                        </ul>
                        <p><i>Adjust the campaign strategy as above to improve subscription likelihood for this client.</i></p>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Unable to generate recommendations due to missing probability data.")

# Handle optimal client strategy
if strategy_submitted:
    errors = validate_inputs(balance, pdays)
    if errors:
        for error in errors:
            st.error(error)
    else:
        # Define ideal client profile (based on typical high-probability attributes)
        ideal_profile = {
            "Age": "30-50 (working professionals or retirees)",
            "Job": "management, student, retired, or admin.",
            "Marital Status": "single or married",
            "Education": "tertiary or secondary",
            "Default": "no",
            "Balance": "positive balance (> €1,000)",
            "Housing Loan": "no",
            "Personal Loan": "no",
        }

        # Define campaign strategy for ideal clients
        contact_options = ["cellular", "telephone", "unknown"]
        month_options = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        duration_options = [100, 300, 500, 1000, 1500]
        campaign_options = [1, 2, 3, 5, 7]
        poutcome_options = ["success", "failure", "other", "unknown"]

        best_confidence = 0
        best_params = {}

        # Use a sample input for a high-probability client to optimize campaign
        base_input = {
            "age": 40,
            "job": "management",
            "marital": "single",
            "education": "tertiary",
            "default": "no",
            "balance": 5000,
            "housing": "no",
            "loan": "no",
            "day": 15,
            "pdays": -1,
            "previous": 0,
        }

        with st.spinner("Analyzing optimal marketing strategy for target clients..."):
            for contact in contact_options:
                for month in month_options:
                    for duration in duration_options:
                        for campaign in campaign_options:
                            for poutcome in poutcome_options:
                                input_dict = base_input.copy()
                                input_dict.update({
                                    "contact": contact,
                                    "month": month,
                                    "duration": duration,
                                    "campaign": campaign,
                                    "poutcome": poutcome,
                                })
                                input_df = create_input_df(input_dict)
                                try:
                                    confidence = model.predict_proba(input_df)[0][1] * 100
                                    if confidence > best_confidence:
                                        best_confidence = confidence
                                        best_params = {
                                            "Contact Type": contact,
                                            "Month": month.capitalize(),
                                            "Call Duration (seconds)": duration,
                                            "Number of Contacts": campaign,
                                            "Previous Campaign Outcome": poutcome,
                                        }
                                except AttributeError:
                                    continue

        # Display optimal strategy and ideal client profile
        if best_params:
            st.markdown(f"""
                <div class="strategy-box">
                    <h3>📋 Optimal Marketing Strategy for Target Clients</h3>
                    <p><b>Ideal Client Profile to Prioritize:</b></p>
                    <ul style="text-align: left; margin: 0 auto; display: inline-block;">
                        <li><b>Age</b>: {ideal_profile['Age']}</li>
                        <li><b>Job</b>: {ideal_profile['Job']}</li>
                        <li><b>Marital Status</b>: {ideal_profile['Marital Status']}</li>
                        <li><b>Education</b>: {ideal_profile['Education']}</li>
                        <li><b>Credit in Default</b>: {ideal_profile['Default']}</li>
                        <li><b>Balance</b>: {ideal_profile['Balance']}</li>
                        <li><b>Housing Loan</b>: {ideal_profile['Housing Loan']}</li>
                        <li><b>Personal Loan</b>: {ideal_profile['Personal Loan']}</li>
                    </ul>
                    <p><b>Recommended Campaign Strategy (confidence: {best_confidence:.2f}%):</b></p>
                    <ul style="text-align: left; margin: 0 auto; display: inline-block;">
                        <li><b>Contact Type</b>: {best_params['Contact Type'].capitalize()}</li>
                        <li><b>Month</b>: {best_params['Month']}</li>
                        <li><b>Call Duration</b>: {best_params['Call Duration (seconds)']} seconds</li>
                        <li><b>Number of Contacts</b>: {best_params['Number of Contacts']}</li>
                        <li><b>Previous Campaign Outcome</b>: {best_params['Previous Campaign Outcome'].capitalize()}</li>
                    </ul>
                    <p><i>Target clients with these attributes and use this campaign strategy to maximize subscription rates.</i></p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Unable to generate optimal strategy due to missing probability data.")