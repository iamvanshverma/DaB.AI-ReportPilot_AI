import streamlit as st
import pandas as pd
import re
from datetime import datetime, time, timedelta
import os
import json
import logging
from dotenv import load_dotenv
import sys
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Error handler decorator
def handle_errors(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(traceback.format_exc())
            st.error(f"An error occurred: {str(e)}")
            return None
    return wrapper

# Import custom modules with error handling
try:
    from connectors.google_sheets import GoogleSheetsConnector
    from analysis.analyzer import DataAnalyzer
    from analysis.ai_analyzer import AIAnalyzer
    from visualization.chart_generator import ChartGenerator
    from reporting.report_generator import ReportGenerator
    from scheduler.job_scheduler import JobScheduler
    from utils.email_sender import EmailSender
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"Failed to load modules: {e}")



# Page config
st.set_page_config(
    page_title="Data Analysis & Reporting Hub",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'google_connector' not in st.session_state:
    st.session_state.google_connector = None
if 'scheduler' not in st.session_state:
    try:
        st.session_state.scheduler = JobScheduler()
    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {e}")
        st.session_state.scheduler = None

# Title
st.title("📊 Automated Data Analysis & Reporting Hub")
st.markdown("Connect Google Sheets → Analyze with AI → Send Reports in Multiple Languages")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    
    # API Status checks with error handling
    try:
        if os.getenv('RESEND_API_KEY'):
            st.success("✅ Email API Ready")
        else:
            st.error("❌ Email API Missing")
    except:
        st.warning("⚠️ Cannot verify Email API")
    
    try:
        if os.getenv('GEMINI_API_KEY'):
            st.success("✅ AI API Ready")
        else:
            st.error("❌ AI API Missing")
    except:
        st.warning("⚠️ Cannot verify AI API")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Connect & Analyze", "📧 Send Report", "⏰ Schedule Reports", "📋 Jobs"])

# Tab 1: Connect & Analyze
with tab1:
    st.header("Connect Google Sheets")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 🔐 Step 1: Your Google Spreadsheet URL")
        
    
    with col2:
        st.markdown("### 📄 Step 2: Allow us to fetch data")

    
    # ————— New OAuth flow —————
    with st.expander("🔓 Login with Google (OAuth) to fetch private sheet", expanded=False):
         oauth_url = st.text_input("Google Sheet URL", placeholder="https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit")
# new OAuth connect flow - replace previous block
from google_auth import get_credentials_and_auth_url
from googleapiclient.discovery import build

# read query params (Streamlit will show code when Google redirects back)
qp = st.experimental_get_query_params()
creds, auth_url = get_credentials_and_auth_url(qp)

if auth_url:
    st.info("Click the link below to authorize this app to read your Google Sheet (one-time).")
    st.markdown(f"[Authorize Google Sheets]({auth_url}){{:target='_blank'}}", unsafe_allow_html=True)
    st.caption("After authorizing, Google will redirect you back to this page and the app will automatically pick up the token.")
else:
    # creds available -> build service and fetch sheet
    try:
        service = build('sheets', 'v4', credentials=creds)
        match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", oauth_url)
        if not match:
            st.error("❌ Invalid Google Sheet URL")
        else:
            sheet_id = match.group(1)

            meta = service.spreadsheets().get(
                spreadsheetId=sheet_id,
                fields="sheets(properties(title))"
            ).execute()
            first_sheet = meta["sheets"][0]["properties"]["title"]

            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"'{first_sheet}'"
            ).execute()
            rows = result.get("values", [])

            if not rows:
                st.error("❌ No data found in sheet")
            else:
                df = pd.DataFrame(rows[1:], columns=rows[0])
                st.session_state.data = df
                st.session_state.sheet_url = oauth_url
                st.success(f"✅ OAuth connected! {len(df)} rows loaded.")
    except Exception as e:
        st.error(f"Google Sheets fetch failed: {e}")
        logger.exception("Google Sheets fetch failed")


    # ——————————————————————

    # Data Preview & Analysis
    if st.session_state.data is not None:
        st.markdown("---")
        st.header("📊 Data Analysis")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", f"{len(st.session_state.data):,}")
        with col2:
            st.metric("Total Columns", len(st.session_state.data.columns))
        with col3:
            numeric_cols = st.session_state.data.select_dtypes(include=['number']).columns
            st.metric("Numeric Columns", len(numeric_cols))
        with col4:
            missing = st.session_state.data.isnull().sum().sum()
            st.metric("Missing Values", f"{missing:,}")
        
        # Data preview
        with st.expander("📋 Data Preview", expanded=True):
            st.dataframe(st.session_state.data.head(10))
        
        # Generate analysis
        if st.button("🤖 Generate AI Analysis", type="primary"):
            with st.spinner("Analyzing with AI..."):
                try:
                    analyzer = DataAnalyzer(st.session_state.data)
                    ai_analyzer = AIAnalyzer()
                    
                    # Get AI insights
                    insights = ai_analyzer.analyze_data_comprehensive(st.session_state.data)
                    
                    st.markdown("### 🤖 AI Insights")
                    st.markdown(insights)
                    
                    # Save analysis
                    st.session_state.ai_insights = insights
                except Exception as e:
                    st.error(f"AI Analysis failed: {str(e)}")
                
        # Generate visualizations
        if st.button("📈 Generate Charts"):
            with st.spinner("Creating visualizations..."):
                try:
                    chart_gen = ChartGenerator()
                    charts = chart_gen.generate_all_charts(st.session_state.data)
                    
                    st.session_state.charts = charts
                    
                    for title, fig in charts[:4]:  # Show first 4 charts
                        st.pyplot(fig)
                except Exception as e:
                    st.error(f"Chart generation failed: {str(e)}")

# Tab 2: Send Report
with tab2:
    st.write("🔑 RESEND_API_KEY:", os.getenv("RESEND_API_KEY"))
    st.write("✉️ RESEND_FROM_EMAIL:", os.getenv("RESEND_FROM_EMAIL"))
    st.write("👤 RESEND_FROM_NAME:", os.getenv("RESEND_FROM_NAME"))
    st.header("📧 Send Analysis Report")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please connect to data first")
    else:
        with st.form("send_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                recipient = st.text_input(
                    "Recipient Email",
                    value=os.getenv("DEFAULT_RECIPIENT_EMAIL", "")
                )
                
                language = st.selectbox(
                    "Report Language",
                    options=["en", "es", "fr", "de", "pt", "hi", "zh", "ja"],
                    format_func=lambda x: {
                        "en": "🇬🇧 English",
                        "es": "🇪🇸 Spanish",
                        "fr": "🇫🇷 French", 
                        "de": "🇩🇪 German",
                        "pt": "🇵🇹 Portuguese",
                        "hi": "🇮🇳 Hindi",
                        "zh": "🇨🇳 Chinese",
                        "ja": "🇯🇵 Japanese"
                    }[x]
                )
            
            with col2:
                report_name = st.text_input(
                    "Report Name",
                    value=f"Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
                )
                
                include_charts = st.checkbox("Include Charts", value=True)
                include_raw_data = st.checkbox("Include Data Sample", value=True)
            
            if st.form_submit_button("📧 Send Report Now", type="primary"):
                with st.spinner(f"Generating report in {language.upper()}..."):
                    try:
                        # Generate comprehensive analysis
                        analyzer = DataAnalyzer(st.session_state.data)
                        ai_analyzer = AIAnalyzer()
                        chart_gen = ChartGenerator()
                        
                        # Get AI insights with language support
                        ai_insights = ai_analyzer.analyze_data_comprehensive(
                            st.session_state.data, 
                            language
                        )
                        
                        # Generate charts
                        charts = []
                        if include_charts:
                            charts = chart_gen.generate_all_charts(st.session_state.data)
                        
                        # Generate report
                        report_gen = ReportGenerator()
                        report_content = report_gen.generate_multilingual_report(
                            data=st.session_state.data,
                            language=language,
                            report_name=report_name,
                            include_charts=include_charts,
                            include_raw_data=include_raw_data,
                            ai_insights=ai_insights,
                            charts=charts
                        )


                        # Send email
                        email_sender = EmailSender()
                        success = email_sender.send_report(
                            recipient_email=recipient,
                            report_content=report_content,
                            report_name=report_name,
                            language=language
                        )
                        if success:
                            st.success(f"✅ Report sent to {recipient}!")
                            st.balloons()
                        else:
                            st.error("❌ Failed to send report via SMTP")

                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                        logger.error(f"Report error: {str(e)}", exc_info=True)

# Tab 3: Schedule Reports with MINUTE option
with tab3:
    st.header("⏰ Schedule Automated Reports")
    
    if st.session_state.data is None:
        st.warning("⚠️ Please connect to data first")
    elif st.session_state.scheduler is None:
        st.error("❌ Scheduler not available")
    else:
        with st.form("schedule_report"):
            col1, col2 = st.columns(2)
            
            with col1:
                job_name = st.text_input("Job Name", value="Analysis Report Job")
                recipient = st.text_input("Recipient Email", value=os.getenv("DEFAULT_RECIPIENT_EMAIL", ""))
                
                # Updated frequency options including minutes
                frequency = st.selectbox(
                    "Frequency", 
                    ["Every Minute", "Every 5 Minutes", "Every 15 Minutes", "Every 30 Minutes", 
                     "Hourly", "Daily", "Weekly"],
                    help="Choose how often to send reports"
                )
                
                language = st.selectbox(
                    "Report Language",
                    options=["en", "es", "fr", "de", "pt", "hi", "zh", "ja"],
                    format_func=lambda x: {
                        "en": "🇬🇧 English", "es": "🇪🇸 Spanish", "fr": "🇫🇷 French",
                        "de": "🇩🇪 German", "pt": "🇵🇹 Portuguese", "hi": "🇮🇳 Hindi",
                        "zh": "🇨🇳 Chinese", "ja": "🇯🇵 Japanese"
                    }[x]
                )
            
            with col2:
                # Show time inputs only for daily/weekly
                if frequency == "Daily":
                    run_time = st.time_input("Run Time", value=time(9, 0))
                elif frequency == "Weekly":
                    day = st.selectbox("Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
                    run_time = st.time_input("Run Time", value=time(9, 0))
                elif frequency in ["Every Minute", "Every 5 Minutes", "Every 15 Minutes", "Every 30 Minutes", "Hourly"]:
                    st.info(f"📍 Will run {frequency.lower()} starting immediately")
                
                include_charts = st.checkbox("Include Charts", value=True)
                auto_refresh = st.checkbox("Auto-refresh data", value=True, 
                                         help="Fetch latest data from Google Sheets before each report")
            
            if st.form_submit_button("📅 Schedule Report", type="primary"):
                try:
                    # Prepare job config
                    job_config = {
                        "job_name": job_name,
                        "recipient": recipient,
                        "language": language,
                        "include_charts": include_charts,
                        "auto_refresh": auto_refresh,
                        "sheet_url": st.session_state.get('sheet_url', ''),
                        "creds": st.session_state.get('creds', {})
                    }
                    
                    # Map frequency to scheduler parameters
                    schedule_params = {"frequency": frequency}
                    
                    if frequency == "Daily":
                        schedule_params["type"] = "daily"
                        schedule_params["hour"] = run_time.hour
                        schedule_params["minute"] = run_time.minute
                    elif frequency == "Weekly":
                        schedule_params["type"] = "weekly"
                        schedule_params["day"] = day.lower()[:3]
                        schedule_params["hour"] = run_time.hour
                        schedule_params["minute"] = run_time.minute
                    elif frequency == "Every Minute":
                        schedule_params["type"] = "interval"
                        schedule_params["minutes"] = 1
                    elif frequency == "Every 5 Minutes":
                        schedule_params["type"] = "interval"
                        schedule_params["minutes"] = 5
                    elif frequency == "Every 15 Minutes":
                        schedule_params["type"] = "interval"
                        schedule_params["minutes"] = 15
                    elif frequency == "Every 30 Minutes":
                        schedule_params["type"] = "interval"
                        schedule_params["minutes"] = 30
                    elif frequency == "Hourly":
                        schedule_params["type"] = "interval"
                        schedule_params["hours"] = 1
                    
                    # Schedule job
                    job_id = st.session_state.scheduler.schedule_job(
                        job_config=job_config,
                        schedule_params=schedule_params,
                        initial_data=st.session_state.data
                    )
                    
                    if job_id:
                        st.success(f"✅ Report scheduled! Job ID: {job_id}")
                        
                        # Show next run info
                        if frequency.startswith("Every"):
                            st.info(f"⏱️ First report will be sent in {frequency.replace('Every ', '')}")
                    else:
                        st.error("Failed to schedule report")
                        
                except Exception as e:
                    st.error(f"Scheduling error: {str(e)}")
                    logger.error(f"Scheduling error: {str(e)}", exc_info=True)

# Tab 4: Job Management
with tab4:
    st.header("📋 Scheduled Jobs")
    
    if st.session_state.scheduler is None:
        st.error("❌ Scheduler not available")
    else:
        try:
            jobs = st.session_state.scheduler.get_all_jobs()
            
            if not jobs:
                st.info("No scheduled jobs yet")
            else:
                for job in jobs:
                    with st.expander(f"📋 {job['config'].get('job_name', 'Unnamed Job')}", expanded=True):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.write(f"**Job ID:** `{job['id']}`")
                            st.write(f"**Recipient:** {job['config'].get('recipient')}")
                            st.write(f"**Language:** {job['config'].get('language', 'en').upper()}")
                        
                        with col2:
                            st.write(f"**Frequency:** {job['schedule'].get('frequency', 'Unknown')}")
                            st.write(f"**Next Run:** {job.get('next_run', 'N/A')}")
                            st.write(f"**Status:** {'🟢 Active' if job.get('active', True) else '🔴 Paused'}")
                        
                        with col3:
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                if st.button(f"▶️ Run Now", key=f"run_{job['id']}", use_container_width=True):
                                    try:
                                        st.session_state.scheduler.run_job_now(job['id'])
                                        st.success("Job triggered!")
                                    except Exception as e:
                                        st.error(f"Failed: {str(e)}")
                            
                            with col_b:
                                if st.button(f"🗑️ Delete", key=f"del_{job['id']}", use_container_width=True):
                                    try:
                                        st.session_state.scheduler.delete_job(job['id'])
                                        st.success("Job deleted!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed: {str(e)}")
                                        
        except Exception as e:
            st.error(f"Error loading jobs: {str(e)}")
            logger.error(f"Job loading error: {str(e)}", exc_info=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        Built with Hustle and ❤️ by Vansh Verma | Powered by Gemini AI
    </div>
    """,
    unsafe_allow_html=True
)