import streamlit as st
import datetime
import json
import pandas as pd
import hashlib
import platform
import uuid
import base64
import io
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart

# Set page configuration
st.set_page_config(
    page_title="Year 11 Committee Financial System",
    page_icon="💰",
    layout="wide"
)

# Add custom CSS for responsiveness - properly enclosed in style tags
st.markdown("""
<style>
    /* Make text responsive */
    h1, h2, h3 {
        margin-top: 0;
    }
    /* Improve form input fields */
    div[data-baseweb="input"], div[data-baseweb="textarea"] {
        width: 100%;
    }

    /* --- MODIFIED TABLE STYLING --- */
    /* Enhance table styling */
    .stDataFrame {
        border: 1px solid #e6e6e6;
        border-radius: 5px;
        margin-bottom: 1.5rem;
    }

    /* Adjust font sizes for better readability */
    .dataframe { 
        font-size: 0.85rem;
    }

    /* Improve table display */
    [data-testid="stTable"] {
        max-width: 100%;
        display: block;
    }

    /* Improve table column sizes */
    table.dataframe th { 
        padding: 0.5rem !important;
        min-width: 80px; 
        white-space: normal; 
        text-align: left; 
    }

    table.dataframe td { 
        padding: 0.5rem !important;
        white-space: normal !important; 
        word-wrap: break-word; 
    }

    /* Add some spacing between sections */
    h2, h3, .stSubheader {
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    div[data-testid="stInfo"], div[data-testid="stWarning"], div[data-testid="stError"], div[data-testid="stSuccess"] {
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1.5rem;
    }
    /* Improve button layout */
    .stButton > button {
        width: 100%;
    }

    /* Better container spacing */
    .main .block-container {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    /* Force column wrapping on medium screens (laptops) */
    @media screen and (max-width: 1200px) {
        .medium-stack {
            flex-direction: column !important;
        }
        .medium-stack > div {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            margin-bottom: 1rem;
        }
        /* Reduce table font size on medium screens */
        .dataframe {
            font-size: 0.8rem;
        }
    }
    /* Adjust metrics for small screens */
    @media screen and (max-width: 992px) {
        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.8rem !important;
        }
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
    /* Adjust metrics for mobile */
    @media screen and (max-width: 640px) {
        [data-testid="stMetricValue"] {
            font-size: 1rem !important;
        }
        [data-testid="stMetricDelta"] {
            font-size: 0.7rem !important;
        }
    }
    /* Fix sidebar on small screens */
    @media screen and (max-width: 768px) {
        section[data-testid="stSidebar"] > div:first-child {
             padding-left: 0.5rem !important;
             padding-right: 0.5rem !important;
        }
    }
    /* Make columns stack on mobile */
    @media screen and (max-width: 768px) {
        .mobile-stack {
            flex-direction: column !important;
        }
        .mobile-stack > div[data-testid="stVerticalBlock"] { 
            width: 100% !important;
            min-width: unset !important; 
        }
        .responsive-budget .mobile-stack > div[data-testid="stVerticalBlock"] {
             margin-bottom: 0.5rem; 
        }
    }
</style>
""", unsafe_allow_html=True)

# Password configuration
def check_credentials(username, password, user_credentials):
    """Check if username and password match stored credentials"""
    if username in user_credentials:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return hashed_password == user_credentials[username]["password_hash"]
    return False

def get_user_role(username, user_credentials):
    """Get the role for a username"""
    if username in user_credentials:
        return user_credentials[username]["role"]
    return None

# User credentials
USER_CREDENTIALS = {
    "admin": {
        "password_hash": "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",  # "password"
        "role": "admin"
    },
    "viewer": {
        "password_hash": "d35ca5051b82ffc326a3b0b6574a9a3161dee16b9478a199ee39cd803ce5b799",  # "viewer"
        "role": "viewer"
    }
}

# Detect device type for responsive design
def get_device_type():
    user_agent = platform.system()
    if 'mobile' in user_agent.lower() or 'android' in user_agent.lower() or 'ios' in user_agent.lower():
        return "mobile"
    elif 'tablet' in user_agent.lower() or 'ipad' in user_agent.lower():
        return "tablet"
    else:
        try:
            if hasattr(st, 'experimental_get_viewport_size'):
                width = st.experimental_get_viewport_size()['width']
                if width < 768:
                    return "mobile"
                elif width < 1200:
                    return "tablet"
        except:
            pass
        return "desktop"

# Initialize session state variables if they don't exist
if 'device_type' not in st.session_state:
    st.session_state.device_type = get_device_type()

if 'transactions' not in st.session_state:
    st.session_state.transactions = []

if 'budget' not in st.session_state:
    st.session_state.budget = {
        "income": {
            "Fundraising Events": {"budget": 0, "actual": 0},
            "Merchandise Sales": {"budget": 0, "actual": 0},
            "Sponsorships": {"budget": 0, "actual": 0},
            "Trip Payments": {"budget": 0, "actual": 0},  # Added for trip payments
            "Other Income": {"budget": 0, "actual": 0}
        },
        "expenses": {
            "Event Expenses": {"budget": 0, "actual": 0},
            "Merchandise Production": {"budget": 0, "actual": 0},
            "Marketing/Promotion": {"budget": 0, "actual": 0},
            "Yearbook": {"budget": 0, "actual": 0},
            "Graduation": {"budget": 0, "actual": 0},
            "School Trips": {"budget": 0, "actual": 0},
            "Transportation": {"budget": 0, "actual": 0},  # Added for trip transportation costs
            "Tickets & Admissions": {"budget": 0, "actual": 0},  # Added for trip tickets
            "Emergency Reserve": {"budget": 0, "actual": 0},
            "Other Expenses": {"budget": 0, "actual": 0}
        }
    }

if 'events' not in st.session_state:
    st.session_state.events = []

# New session state for event participants (students paying for trips)
if 'event_participants' not in st.session_state:
    st.session_state.event_participants = []

# New session state for event expenses (detailed expenses for each event)
if 'event_expenses' not in st.session_state:
    st.session_state.event_expenses = []

if 'fundraising' not in st.session_state:
    st.session_state.fundraising = []

# Authentication state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'user_role' not in st.session_state:
    st.session_state.user_role = None

if 'username' not in st.session_state:
    st.session_state.username = None

# Committee members
committee_members = {
    "Chair": "TBD",
    "Deputy Chair": "TBD",
    "Treasurer": "Deema Abououf",
    "Secretary": "TBD",
    "Events Coordinator": "TBD"
}

# Authorization levels based on the matrix
auth_levels = {
    "Under 100 KD": ["Chair"],
    "Over 100 KD": ["Chair", "School Admin"],
    "New Category": ["Committee Vote"]
}

# PDF Generation Functions
def create_pdf_content(title, content_elements):
    """Create PDF content with the given title and elements"""
    buffer = io.BytesIO()
    
    # Create the PDF object, using BytesIO as its "file"
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Container for the elements
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add title
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add date
    elements.append(Paragraph(f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add content elements
    elements.extend(content_elements)
    
    # Footer
    elements.append(Spacer(1, 0.5*inch))
    elements.append(Paragraph("Year 11 Committee Financial Management System", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    return pdf

def create_monthly_report_pdf(report, month_name, year):
    """Generate a PDF for the monthly report"""
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements = []
    
    # Add summary section
    elements.append(Paragraph("Financial Summary", subtitle_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Summary data table
    summary_data = [
        ["Metric", "Amount"],
        ["Total Income", f"KD {report['total_income']:.2f}"],
        ["Total Expenses", f"KD {report['total_expenses']:.2f}"],
        ["Net", f"KD {report['net']:.2f}"],
        ["Current Balance", f"KD {report['current_balance']:.2f}"],
        ["Emergency Reserve", f"KD {report['emergency_reserve']:.2f}"],
        ["Available Funds", f"KD {report['available_funds']:.2f}"]
    ]
    
    # Create the summary table
    summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Transactions table if there are any
    if report['transactions']:
        elements.append(Paragraph("Transactions", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        # Create a dataframe for easier manipulation
        transactions_df = pd.DataFrame(report['transactions'])
        
        # Prepare table data
        table_data = [["Date", "Description", "Category", "Income", "Expense", "Authorized By"]]
        
        for _, row in transactions_df.iterrows():
            table_data.append([
                row.get("date", ""),
                row.get("description", ""),
                row.get("category", ""),
                f"KD {row.get('income', 0):.2f}" if row.get('income', 0) > 0 else "",
                f"KD {row.get('expense', 0):.2f}" if row.get('expense', 0) > 0 else "",
                row.get("authorized_by", "")
            ])
        
        # Create the transactions table
        trans_table = Table(table_data, colWidths=[1*inch, 1.5*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(trans_table)
    else:
        elements.append(Paragraph("No transactions for this period.", normal_style))
    
    # Generate the PDF
    title = f"Monthly Financial Report - {month_name} {year}"
    return create_pdf_content(title, elements)

def create_event_report_pdf(report):
    """Generate a PDF for an individual event report"""
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements = []
    
    event = report["event"]
    event_title = f"Event Report: {event['name']}"
    
    # Event details section
    elements.append(Paragraph("Event Details", subtitle_style))
    elements.append(Spacer(1, 0.1*inch))
    
    details_data = [
        ["Detail", "Value"],
        ["Date", event['date']],
        ["Location", event['location']],
        ["Type", event.get('event_type', '')],
        ["Status", event['status']],
        ["Coordinator", event['coordinator']],
        ["Price per Person", f"KD {event.get('price_per_person', 0):.2f}"],
        ["Target Participants", str(event.get('target_participants', 0))]
    ]
    
    details_table = Table(details_data, colWidths=[2*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(details_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Financial summary
    elements.append(Paragraph("Financial Summary", subtitle_style))
    elements.append(Spacer(1, 0.1*inch))
    
    summary_data = [
        ["Metric", "Amount"],
        ["Total Income", f"KD {report['total_payments']:.2f}"],
        ["Total Expenses", f"KD {report['total_expenses']:.2f}"],
        ["Profit", f"KD {report['profit']:.2f}"],
        ["Participants", f"{report['participant_count']}"],
        ["Target", f"{event['target_participants']}"]
    ]
    
    # Calculate participation rate
    if event['target_participants'] > 0:
        participation_rate = report['participant_count'] / event['target_participants'] * 100
        summary_data.append(["Participation Rate", f"{participation_rate:.1f}%"])
    
    summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Expense breakdown by category
    if report["expense_breakdown"]:
        elements.append(Paragraph("Expense Breakdown", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        expense_data = [["Category", "Amount", "Percentage"]]
        
        for category, amount in report["expense_breakdown"].items():
            percentage = amount / report['total_expenses'] * 100 if report['total_expenses'] > 0 else 0
            expense_data.append([
                category,
                f"KD {amount:.2f}",
                f"{percentage:.1f}%"
            ])
        
        expense_table = Table(expense_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(expense_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Participant list
    if report["participants"]:
        elements.append(Paragraph("Participant List", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        participant_data = [["Name", "Amount", "Date", "Method", "Notes"]]
        
        for participant in report["participants"]:
            participant_data.append([
                participant.get("participant_name", ""),
                f"KD {participant.get('payment_amount', 0):.2f}",
                participant.get("payment_date", ""),
                participant.get("payment_method", ""),
                participant.get("notes", "")
            ])
        
        participant_table = Table(participant_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1.5*inch])
        participant_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(participant_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # Expense list
    if report["expenses"]:
        elements.append(Paragraph("Expense List", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        expense_list_data = [["Description", "Amount", "Date", "Category", "Paid To", "Receipt #"]]
        
        for expense in report["expenses"]:
            expense_list_data.append([
                expense.get("description", ""),
                f"KD {expense.get('amount', 0):.2f}",
                expense.get("date", ""),
                expense.get("category", ""),
                expense.get("paid_to", ""),
                expense.get("receipt_num", "")
            ])
        
        expense_list_table = Table(expense_list_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch, 0.8*inch])
        expense_list_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(expense_list_table)
    
    # Generate the PDF
    return create_pdf_content(event_title, elements)

def create_all_events_report_pdf(report):
    """Generate a PDF for the all events summary report"""
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    elements = []
    
    # Overall summary
    elements.append(Paragraph("Financial Summary", subtitle_style))
    elements.append(Spacer(1, 0.1*inch))
    
    summary_data = [
        ["Metric", "Amount"],
        ["Total Income", f"KD {report['total_income']:.2f}"],
        ["Total Expenses", f"KD {report['total_expenses']:.2f}"],
        ["Total Profit", f"KD {report['total_profit']:.2f}"],
        ["Total Events", f"{report['event_count']}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.2*inch))
    
    # Events table
    if report["events"]:
        elements.append(Paragraph("Event Summary", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        events_data = [["Event Name", "Date", "Type", "Participants", "Income", "Expenses", "Profit", "Status"]]
        
        for event in report["events"]:
            events_data.append([
                event.get("name", ""),
                event.get("date", ""),
                event.get("event_type", ""),
                str(event.get("participants", 0)),
                f"KD {event.get('income', 0):.2f}",
                f"KD {event.get('expenses', 0):.2f}",
                f"KD {event.get('profit', 0):.2f}",
                event.get("status", "")
            ])
        
        # Create the events table with adjusted column widths
        events_table = Table(events_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch])
        events_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(events_table)
    else:
        elements.append(Paragraph("No events found.", normal_style))
    
    # Generate the PDF
    title = "All Events Financial Summary"
    return create_pdf_content(title, elements)

def get_pdf_download_link(pdf_bytes, filename, button_text="Download PDF Report"):
    """Generate a link to download the PDF file"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}"><button style="background-color: #4CAF50; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">{button_text}</button></a>'
    return href

# Helper functions
def get_balance():
    total_income = sum(t["income"] for t in st.session_state.transactions)
    total_expenses = sum(t["expense"] for t in st.session_state.transactions)
    return total_income - total_expenses

def get_emergency_reserve():
    # Calculate 15% of total income
    total_income = sum(t["income"] for t in st.session_state.transactions)
    return total_income * 0.15

def get_required_authorization(amount, category):
    # Check if this is a new category
    is_new_category = True
    for section in ["income", "expenses"]:
        if category in st.session_state.budget[section]:
            is_new_category = False
            break
    
    if is_new_category:
        return ["Committee Vote"]
    elif float(amount) > 100:
        return auth_levels["Over 100 KD"]
    else:
        return auth_levels["Under 100 KD"]

def add_transaction(date, description, category, income=0, expense=0, authorized_by="", receipt_num="", notes="", event_id=None):
    # Validate transaction
    if not description or not category:
        return False, "Description and category are required"
    
    # Check authorization based on amount
    amount = max(income, expense)
    required_auth = get_required_authorization(amount, category)
    if authorized_by not in required_auth and "Committee Vote" not in required_auth:
        return False, f"This transaction requires authorization from: {', '.join(required_auth)}"
    
    # Add transaction
    transaction = {
        "date": date,
        "description": description,
        "category": category,
        "income": float(income),
        "expense": float(expense),
        "authorized_by": authorized_by,
        "receipt_num": receipt_num,
        "notes": notes,
        "timestamp": datetime.datetime.now().isoformat(),
        "event_id": event_id  # Link to event if applicable
    }
    st.session_state.transactions.append(transaction)
    
    # Update budget actuals
    if income > 0:
        if category in st.session_state.budget["income"]:
            st.session_state.budget["income"][category]["actual"] += float(income)
        else:
            st.session_state.budget["income"]["Other Income"]["actual"] += float(income)
    
    if expense > 0:
        if category in st.session_state.budget["expenses"]:
            st.session_state.budget["expenses"][category]["actual"] += float(expense)
        else:
            st.session_state.budget["expenses"]["Other Expenses"]["actual"] += float(expense)
    
    # If linked to an event, update the event's actual income/expense
    if event_id:
        event = next((e for e in st.session_state.events if e.get("id") == event_id), None)
        if event:
            if income > 0:
                event["actual_income"] += float(income)
            if expense > 0:
                event["actual_expenses"] += float(expense)
    
    return True, "Transaction added successfully"

def generate_monthly_report(month=None, year=None):
    now = datetime.datetime.now()
    month = month or now.month
    year = year or now.year
    
    # Filter transactions for the given month/year
    monthly_transactions = []
    for t in st.session_state.transactions:
        try:
            t_date = datetime.datetime.fromisoformat(t["timestamp"]).date()
            if t_date.month == month and t_date.year == year:
                monthly_transactions.append(t)
        except (ValueError, KeyError):
            continue
    
    monthly_income = sum(t["income"] for t in monthly_transactions)
    monthly_expenses = sum(t["expense"] for t in monthly_transactions)
    
    report = {
        "month": month,
        "year": year,
        "total_income": monthly_income,
        "total_expenses": monthly_expenses,
        "net": monthly_income - monthly_expenses,
        "transactions": monthly_transactions,
        "current_balance": get_balance(),
        "emergency_reserve": get_emergency_reserve(),
        "available_funds": get_balance() - get_emergency_reserve()
    }
    
    return report

def create_event_budget(event_name, date, location, coordinator, event_type, projected_income=0, projected_expenses=0, price_per_person=0, target_participants=0, description=""):
    # Generate a unique ID for the event
    event_id = str(uuid.uuid4())
    
    event = {
        "id": event_id,
        "name": event_name,
        "date": date,
        "location": location,
        "coordinator": coordinator,
        "event_type": event_type,  # New field: event type (e.g., "Trip", "Fundraiser", etc.)
        "price_per_person": float(price_per_person),  # New field for trip pricing
        "target_participants": int(target_participants),  # New field for target number of participants
        "description": description,  # New field for event description
        "projected_income": float(projected_income),
        "projected_expenses": float(projected_expenses),
        "actual_income": 0,
        "actual_expenses": 0,
        "income_sources": [],
        "expense_items": [],
        "status": "Planning",  # Planning, Active, Completed
        "created_at": datetime.datetime.now().isoformat()
    }
    
    st.session_state.events.append(event)
    return True, "Event budget created successfully", event_id

def add_event_participant(event_id, participant_name, payment_amount, payment_date, payment_method="Cash", notes=""):
    """Add a participant payment to an event (e.g., trip participant)"""
    if not event_id or not participant_name:
        return False, "Event and participant name are required"
    
    # Check if the event exists
    event = next((e for e in st.session_state.events if e.get("id") == event_id), None)
    if not event:
        return False, "Event not found"
    
    # Generate unique ID for this participant payment
    participant_id = str(uuid.uuid4())
    
    # Add participant payment record
    participant = {
        "id": participant_id,
        "event_id": event_id,
        "participant_name": participant_name,
        "payment_amount": float(payment_amount),
        "payment_date": payment_date,
        "payment_method": payment_method,
        "notes": notes,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    st.session_state.event_participants.append(participant)
    
    # Update event actual income and create a transaction record
    event["actual_income"] += float(payment_amount)
    
    # Add a transaction for this payment
    add_transaction(
        date=payment_date,
        description=f"Payment from {participant_name} for {event['name']}",
        category="Trip Payments",
        income=float(payment_amount),
        expense=0,
        authorized_by=event["coordinator"],
        receipt_num="",
        notes=f"Participant payment for event: {event['name']}",
        event_id=event_id
    )
    
    return True, f"Added payment from {participant_name}", participant_id

def add_event_expense(event_id, expense_description, expense_amount, expense_date, expense_category, paid_to="", receipt_num="", notes=""):
    """Add an expense to an event (e.g., trip expense)"""
    if not event_id or not expense_description:
        return False, "Event and expense description are required"
    
    # Check if the event exists
    event = next((e for e in st.session_state.events if e.get("id") == event_id), None)
    if not event:
        return False, "Event not found"
    
    # Generate unique ID for this expense
    expense_id = str(uuid.uuid4())
    
    # Add expense record
    expense = {
        "id": expense_id,
        "event_id": event_id,
        "description": expense_description,
        "amount": float(expense_amount),
        "date": expense_date,
        "category": expense_category,
        "paid_to": paid_to,
        "receipt_num": receipt_num,
        "notes": notes,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    st.session_state.event_expenses.append(expense)
    
    # Update event actual expenses and create a transaction record
    event["actual_expenses"] += float(expense_amount)
    
    # Add a transaction for this expense
    add_transaction(
        date=expense_date,
        description=f"{expense_description} - {event['name']}",
        category=expense_category,
        income=0,
        expense=float(expense_amount),
        authorized_by=event["coordinator"],
        receipt_num=receipt_num,
        notes=f"Expense for event: {event['name']}",
        event_id=event_id
    )
    
    return True, f"Added expense: {expense_description}", expense_id

def generate_event_report(event_id):
    """Generate a financial report for a specific event"""
    event = next((e for e in st.session_state.events if e.get("id") == event_id), None)
    if not event:
        return None
    
    # Get all participants for this event
    participants = [p for p in st.session_state.event_participants if p.get("event_id") == event_id]
    total_participant_payments = sum(p["payment_amount"] for p in participants)
    
    # Get all expenses for this event
    expenses = [e for e in st.session_state.event_expenses if e.get("event_id") == event_id]
    total_expenses = sum(e["amount"] for e in expenses)
    
    # Calculate profit
    profit = total_participant_payments - total_expenses
    
    # Create expense breakdown by category
    expense_categories = {}
    for expense in expenses:
        category = expense.get("category", "Other")
        if category not in expense_categories:
            expense_categories[category] = 0
        expense_categories[category] += expense["amount"]
    
    # Generate report
    report = {
        "event": event,
        "participants": participants,
        "expenses": expenses,
        "total_payments": total_participant_payments,
        "total_expenses": total_expenses,
        "profit": profit,
        "expense_breakdown": expense_categories,
        "participant_count": len(participants),
        "expense_count": len(expenses)
    }
    
    return report

def generate_all_events_report():
    """Generate a summary report for all events"""
    if not st.session_state.events:
        return None
    
    events_summary = []
    total_income = 0
    total_expenses = 0
    total_profit = 0
    
    for event in st.session_state.events:
        event_id = event.get("id")
        
        # Skip events without ID (shouldn't happen with new code)
        if not event_id:
            continue
        
        # Get participants for this event
        participants = [p for p in st.session_state.event_participants if p.get("event_id") == event_id]
        participant_count = len(participants)
        participant_income = sum(p["payment_amount"] for p in participants)
        
        # Get expenses for this event
        expenses = [e for e in st.session_state.event_expenses if e.get("event_id") == event_id]
        expense_amount = sum(e["amount"] for e in expenses)
        
        # Calculate profit
        profit = participant_income - expense_amount
        
        # Add to totals
        total_income += participant_income
        total_expenses += expense_amount
        total_profit += profit
        
        # Create summary for this event
        event_summary = {
            "id": event_id,
            "name": event["name"],
            "date": event["date"],
            "location": event["location"],
            "event_type": event.get("event_type", ""),
            "participants": participant_count,
            "income": participant_income,
            "expenses": expense_amount,
            "profit": profit,
            "status": event["status"]
        }
        
        events_summary.append(event_summary)
    
    # Sort by date (most recent first)
    events_summary.sort(key=lambda x: x["date"], reverse=True)
    
    report = {
        "events": events_summary,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "total_profit": total_profit,
        "event_count": len(events_summary)
    }
    
    return report

def add_fundraising_initiative(name, dates, coordinator, goal_amount):
    initiative = {
        "name": name,
        "dates": dates,
        "coordinator": coordinator,
        "goal_amount": float(goal_amount),
        "actual_raised": 0,
        "expenses": 0,
        "net_proceeds": 0,
        "status": "Planning"  # Planning, Active, Completed
    }
    
    st.session_state.fundraising.append(initiative)
    return True, "Fundraising initiative added successfully"

# Login screen function
def show_login():
    st.title("Year 11 Committee Financial System")
    st.subheader("Login")
    
    # Center the login form on larger screens
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Create a login form
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if check_credentials(username, password, USER_CREDENTIALS):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_role = get_user_role(username, USER_CREDENTIALS)
                    st.success(f"Login successful! Welcome {username}.")
                    st.rerun()
                else:
                    st.error("Incorrect username or password. Please try again.")
    
    # Instructions for users
    with col2:
        st.markdown("---")
        st.markdown("""
        ### Access Levels:
        - **Admin:** Full access to all features
        - **Viewer:** View dashboard and generate reports only
        
        Please enter your username and password to login.
        
        Default accounts:
        - Username: admin (full access)
        - Username: viewer (view-only access)
        """)

# Dashboard function - FIXED to avoid string formatting issues
def show_dashboard():
    st.header("Financial Dashboard")
    
    # Get the financial metrics
    balance = get_balance()
    reserve = get_emergency_reserve()
    available = balance - reserve
    
    # Use Streamlit's built-in metrics instead of custom HTML/CSS
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Current Balance", f"KD {balance:.2f}")
    
    with col2:
        st.metric("Emergency Reserve (15%)", f"KD {reserve:.2f}")
    
    with col3:
        st.metric("Available Funds", f"KD {available:.2f}")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    if st.session_state.transactions:
        transactions_df = pd.DataFrame(st.session_state.transactions)
        # Sort by timestamp (newest first)
        if "timestamp" in transactions_df.columns:
            transactions_df = transactions_df.sort_values(by="timestamp", ascending=False)
        # Limit to last 5
        recent_transactions = transactions_df.head(5)
        # Select only the columns we want to display
        display_columns = [col for col in ["date", "description", "category", "income", "expense", "authorized_by"] 
                           if col in recent_transactions.columns]
        
        # Display the dataframe
        st.dataframe(recent_transactions[display_columns], use_container_width=True)
    else:
        st.info("No transactions recorded yet.")
    
    # Budget overview with tables
    st.subheader("Budget Overview")
    
    # Income budget vs actual
    st.subheader("Income: Budget vs. Actual")
    income_data = []
    for category, values in st.session_state.budget["income"].items():
        income_data.append({
            "Category": category,
            "Budget": f"KD {values['budget']:.2f}",
            "Actual": f"KD {values['actual']:.2f}",
            "Variance": f"KD {values['actual'] - values['budget']:.2f}"
        })
    
    if income_data:
        income_df = pd.DataFrame(income_data)
        st.dataframe(income_df, use_container_width=True)
    
    # Expense budget vs actual
    st.subheader("Expenses: Budget vs. Actual")
    expense_data = []
    for category, values in st.session_state.budget["expenses"].items():
        expense_data.append({
            "Category": category,
            "Budget": f"KD {values['budget']:.2f}",
            "Actual": f"KD {values['actual']:.2f}",
            "Variance": f"KD {values['actual'] - values['budget']:.2f}"
        })
    
    if expense_data:
        expense_df = pd.DataFrame(expense_data)
        st.dataframe(expense_df, use_container_width=True)
    
    # Upcoming Events
    st.subheader("Upcoming Events")
    
    # Filter for active and planned events
    upcoming_events = [e for e in st.session_state.events if e.get("status") in ["Planning", "Active"]]
    
    if upcoming_events:
        # Display upcoming events in a table
        events_data = []
        for event in upcoming_events:
            # Calculate profit (actual income - actual expenses)
            profit = event.get("actual_income", 0) - event.get("actual_expenses", 0)
            
            # Get participant count
            participants = [p for p in st.session_state.event_participants if p.get("event_id") == event.get("id")]
            
            events_data.append({
                "Event Name": event.get("name", ""),
                "Date": event.get("date", ""),
                "Location": event.get("location", ""),
                "Type": event.get("event_type", ""),
                "Participants": len(participants),
                "Income": f"KD {event.get('actual_income', 0):.2f}",
                "Expenses": f"KD {event.get('actual_expenses', 0):.2f}",
                "Profit": f"KD {profit:.2f}",
                "Status": event.get("status", "")
            })
        
        if events_data:
            events_df = pd.DataFrame(events_data)
            st.dataframe(events_df, use_container_width=True)
    else:
        st.info("No upcoming events scheduled.")
    
    # Quick actions (shown only to admin users)
    if st.session_state.user_role == "admin":
        st.subheader("Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("Add Transaction", use_container_width=True):
                st.session_state.page = "transactions"
        
        with col2:
            if st.button("Manage Events", use_container_width=True):
                st.session_state.page = "events"
        
        with col3:
            if st.button("Generate Report", use_container_width=True):
                st.session_state.page = "reports"
        
        with col4:
            if st.button("Manage Budget", use_container_width=True):
                st.session_state.page = "budget"
    else:
        # For viewer role, only show report generation button
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Report", use_container_width=True):
                st.session_state.page = "reports"
        
        with col2:
            if st.button("View Events", use_container_width=True):
                st.session_state.page = "events"

# Transactions function
def show_transactions():
    st.header("Transactions Management")
    
    # Add new transaction form
    with st.expander("Add New Transaction", expanded=True):
        # Add the responsive-form class
        st.markdown('<div class="responsive-form">', unsafe_allow_html=True)
        
        with st.form("transaction_form"):
            # Use the mobile-stack class for responsive columns
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date", value=datetime.date.today())
                description = st.text_input("Description")
                
                # Get all categories
                categories = list(st.session_state.budget["income"].keys()) + list(st.session_state.budget["expenses"].keys())
                category = st.selectbox("Category", categories)
                
                income = st.number_input("Income (KD)", min_value=0.0, format="%.2f")
            
            with col2:
                expense = st.number_input("Expense (KD)", min_value=0.0, format="%.2f")
                
                # Get all possible authorizers
                authorizers = list(committee_members.keys()) + ["School Admin", "Committee Vote"]
                authorized_by = st.selectbox("Authorized By", authorizers)
                
                receipt_num = st.text_input("Receipt #")
                # FIX: Remove the height parameter
                notes = st.text_area("Notes")
                
                # Option to link to an event
                event_options = [("None", None)] + [(e.get("name", "Unnamed Event"), e.get("id")) for e in st.session_state.events]
                event_names, event_ids = zip(*event_options)
                event_index = st.selectbox("Link to Event (optional)", event_names)
                event_id = event_ids[event_names.index(event_index)] if event_index != "None" else None
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
            
            submit = st.form_submit_button("Add Transaction", use_container_width=True)
            
            if submit:
                success, message = add_transaction(
                    date.strftime("%Y-%m-%d"),
                    description,
                    category,
                    income,
                    expense,
                    authorized_by,
                    receipt_num,
                    notes,
                    event_id
                )
                
                if success:
                    st.success(message)
                else:
                    st.error(message)
        
        # Close the responsive-form div
        st.markdown('</div>', unsafe_allow_html=True)
    
    # View transactions
    st.subheader("Transaction History")
    
    if st.session_state.transactions:
        transactions_df = pd.DataFrame(st.session_state.transactions)
        # Sort by date (newest first)
        if "timestamp" in transactions_df.columns:
            transactions_df = transactions_df.sort_values(by="timestamp", ascending=False)
        
        # Add event name for linked transactions
        if "event_id" in transactions_df.columns:
            def get_event_name(event_id):
                if not event_id:
                    return ""
                event = next((e for e in st.session_state.events if e.get("id") == event_id), None)
                return event.get("name", "") if event else ""
            
            transactions_df["event_name"] = transactions_df["event_id"].apply(get_event_name)
        
        # Format currency columns
        if "income" in transactions_df.columns:
            transactions_df["income"] = transactions_df["income"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
        if "expense" in transactions_df.columns:
            transactions_df["expense"] = transactions_df["expense"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
        
        # Select columns to display
        display_columns = [col for col in ["date", "description", "category", "income", "expense", "authorized_by", "event_name", "receipt_num", "notes"]
                           if col in transactions_df.columns]
        
        st.dataframe(transactions_df[display_columns], use_container_width=True)
        
        # Export options
        st.subheader("Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export Transactions to CSV", use_container_width=True):
                csv = transactions_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="transactions.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        with col2:
            if st.button("Export Transactions to PDF", use_container_width=True):
                # Generate PDF content
                styles = getSampleStyleSheet()
                title_style = styles['Heading1']
                subtitle_style = styles['Heading2']
                normal_style = styles['Normal']
                
                elements = []
                
                # Transaction table
                elements.append(Paragraph("Transaction History", subtitle_style))
                elements.append(Spacer(1, 0.1*inch))
                
                table_data = [["Date", "Description", "Category", "Income", "Expense", "Authorized By"]]
                
                for _, row in transactions_df.iterrows():
                    table_data.append([
                        row.get("date", ""),
                        row.get("description", ""),
                        row.get("category", ""),
                        row.get("income", ""),
                        row.get("expense", ""),
                        row.get("authorized_by", "")
                    ])
                
                # Create the table
                trans_table = Table(table_data)
                trans_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(trans_table)
                
                # Generate the PDF
                pdf = create_pdf_content("Transaction History", elements)
                
                # Create download link
                st.markdown(
                    get_pdf_download_link(pdf, "transactions.pdf", "Download PDF Report"),
                    unsafe_allow_html=True
                )
    else:
        st.info("No transactions recorded yet.")

# Budget function
def show_budget():
    st.header("Budget Management")
    
    # Add new budget category
    with st.expander("Add New Budget Category"):
        # Add the responsive-form class
        st.markdown('<div class="responsive-form">', unsafe_allow_html=True)
        
        with st.form("new_category_form"):
            # Use the mobile-stack class for responsive columns
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                category_name = st.text_input("Category Name")
                category_type = st.radio("Category Type", ["Income", "Expenses"])
            
            with col2:
                initial_budget = st.number_input("Initial Budget (KD)", min_value=0.0, format="%.2f")
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
            
            submit = st.form_submit_button("Add Category", use_container_width=True)
            
            if submit:
                if not category_name:
                    st.error("Category name is required")
                else:
                    category_type = category_type.lower()
                    if category_type == "income":
                        if category_name in st.session_state.budget["income"]:
                            st.error(f"Category '{category_name}' already exists in income categories")
                        else:
                            st.session_state.budget["income"][category_name] = {"budget": initial_budget, "actual": 0}
                            st.success(f"Added '{category_name}' to income categories")
                    else:
                        if category_name in st.session_state.budget["expenses"]:
                            st.error(f"Category '{category_name}' already exists in expense categories")
                        else:
                            st.session_state.budget["expenses"][category_name] = {"budget": initial_budget, "actual": 0}
                            st.success(f"Added '{category_name}' to expense categories")
        
        # Close the responsive-form div
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Adjust existing budget categories
    with st.expander("Adjust Budget Amounts"):
        st.subheader("Income Categories")
        
        # Make the budget adjustment layout responsive
        st.markdown('<div class="responsive-budget">', unsafe_allow_html=True)
        
        for category, values in st.session_state.budget["income"].items():
            # Use the mobile-stack class for responsive columns on small screens
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.text(category)
            
            with col2:
                current_budget = values["budget"]
                st.text(f"Current: KD {current_budget:.2f}")
            
            with col3:
                new_budget = st.number_input(f"New budget for {category}", 
                                            min_value=0.0, 
                                            value=float(current_budget),
                                            key=f"income_{category}",
                                            format="%.2f")
                if new_budget != current_budget:
                    st.session_state.budget["income"][category]["budget"] = new_budget
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.subheader("Expense Categories")
        
        for category, values in st.session_state.budget["expenses"].items():
            # Use the mobile-stack class for responsive columns on small screens
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.text(category)
            
            with col2:
                current_budget = values["budget"]
                st.text(f"Current: KD {current_budget:.2f}")
            
            with col3:
                new_budget = st.number_input(f"New budget for {category}", 
                                            min_value=0.0, 
                                            value=float(current_budget),
                                            key=f"expense_{category}",
                                            format="%.2f")
                if new_budget != current_budget:
                    st.session_state.budget["expenses"][category]["budget"] = new_budget
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Close the responsive-budget div
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Budget overview
    st.subheader("Budget Summary")
    
    # Calculate totals
    total_income_budget = sum(values["budget"] for values in st.session_state.budget["income"].values())
    total_income_actual = sum(values["actual"] for values in st.session_state.budget["income"].values())
    total_expense_budget = sum(values["budget"] for values in st.session_state.budget["expenses"].values())
    total_expense_actual = sum(values["actual"] for values in st.session_state.budget["expenses"].values())
    
    # Display summary metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Income Budget", f"KD {total_income_budget:.2f}")
        st.metric("Total Income Actual", f"KD {total_income_actual:.2f}", 
                f"{(total_income_actual - total_income_budget):.2f}")
    
    with col2:
        st.metric("Total Expense Budget", f"KD {total_expense_budget:.2f}")
        st.metric("Total Expense Actual", f"KD {total_expense_actual:.2f}", 
                f"{(total_expense_actual - total_expense_budget):.2f}")
    
    # Budget tables
    # Income Budget
    st.subheader("Income Budget")
    income_data = []
    for category, values in st.session_state.budget["income"].items():
        income_data.append({
            "Category": category,
            "Budget": f"KD {values['budget']:.2f}",
            "Actual": f"KD {values['actual']:.2f}",
            "Variance": f"KD {values['actual'] - values['budget']:.2f}"
        })
    
    if income_data:
        income_df = pd.DataFrame(income_data)
        st.dataframe(income_df, use_container_width=True)
    
    # Expense Budget
    st.subheader("Expense Budget")
    expense_data = []
    for category, values in st.session_state.budget["expenses"].items():
        expense_data.append({
            "Category": category,
            "Budget": f"KD {values['budget']:.2f}",
            "Actual": f"KD {values['actual']:.2f}",
            "Variance": f"KD {values['actual'] - values['budget']:.2f}"
        })
    
    if expense_data:
        expense_df = pd.DataFrame(expense_data)
        st.dataframe(expense_df, use_container_width=True)
    
    # Budget visualization as text
    st.subheader("Budget Visualization")
    
    # Use a container to make this section responsive
    with st.container():
        st.write(f"Income Budget: KD {total_income_budget:.2f}, Actual: KD {total_income_actual:.2f}")
        st.write(f"Expense Budget: KD {total_expense_budget:.2f}, Actual: KD {total_expense_actual:.2f}")
        st.write(f"Net Budget: KD {total_income_budget - total_expense_budget:.2f}, Actual: KD {total_income_actual - total_expense_actual:.2f}")
    
    # Export Budget as PDF
    st.subheader("Export Options")
    
    if st.button("Export Budget to PDF", use_container_width=True):
        # Generate PDF content
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        subtitle_style = styles['Heading2']
        normal_style = styles['Normal']
        
        elements = []
        
        # Budget Summary
        elements.append(Paragraph("Budget Summary", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        summary_data = [
            ["Metric", "Amount"],
            ["Total Income Budget", f"KD {total_income_budget:.2f}"],
            ["Total Income Actual", f"KD {total_income_actual:.2f}"],
            ["Total Expense Budget", f"KD {total_expense_budget:.2f}"],
            ["Total Expense Actual", f"KD {total_expense_actual:.2f}"],
            ["Net Budget", f"KD {total_income_budget - total_expense_budget:.2f}"],
            ["Net Actual", f"KD {total_income_actual - total_expense_actual:.2f}"]
        ]
        
        # Create the summary table
        summary_table = Table(summary_data, colWidths=[3*inch, 1.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Income Categories
        elements.append(Paragraph("Income Budget", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        income_table_data = [["Category", "Budget", "Actual", "Variance"]]
        
        for category, values in st.session_state.budget["income"].items():
            income_table_data.append([
                category,
                f"KD {values['budget']:.2f}",
                f"KD {values['actual']:.2f}",
                f"KD {values['actual'] - values['budget']:.2f}"
            ])
        
        # Create the income table
        income_table = Table(income_table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
        income_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(income_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Expense Categories
        elements.append(Paragraph("Expense Budget", subtitle_style))
        elements.append(Spacer(1, 0.1*inch))
        
        expense_table_data = [["Category", "Budget", "Actual", "Variance"]]
        
        for category, values in st.session_state.budget["expenses"].items():
            expense_table_data.append([
                category,
                f"KD {values['budget']:.2f}",
                f"KD {values['actual']:.2f}",
                f"KD {values['actual'] - values['budget']:.2f}"
            ])
        
        # Create the expense table
        expense_table = Table(expense_table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
        expense_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(expense_table)
        
        # Generate the PDF
        pdf = create_pdf_content("Budget Report", elements)
        
        # Create download link
        st.markdown(
            get_pdf_download_link(pdf, "budget_report.pdf", "Download Budget PDF Report"),
            unsafe_allow_html=True
        )

# Events function - Completely Revised for Trip Management
def show_events():
    st.header("Event & Trip Management")
    
    # Add tabs for different event management sections
    tab1, tab2, tab3 = st.tabs(["Create Events", "Manage Events", "Event Reports"])
    
    # TAB 1: Create new event
    with tab1:
        st.subheader("Create New Event/Trip")
        
        # Add the responsive-form class
        st.markdown('<div class="responsive-form">', unsafe_allow_html=True)
        
        with st.form("event_form"):
            # Use the mobile-stack class for responsive columns
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                event_name = st.text_input("Event Name")
                event_date = st.date_input("Event Date")
                location = st.text_input("Location")
                event_type = st.selectbox("Event Type", 
                                         ["School Trip", "Field Trip", "Museum Visit", "Park Visit", 
                                          "Cultural Event", "Sports Event", "Workshop", "Other"])
                # FIX: Remove the height parameter
                description = st.text_area("Event Description")
            
            with col2:
                coordinator = st.selectbox("Event Coordinator", list(committee_members.keys()))
                
                # For trip-specific fields
                price_per_person = st.number_input("Price per Person (KD)", min_value=0.0, format="%.2f")
                target_participants = st.number_input("Target Participants", min_value=0, step=1)
                
                # Calculate projected income and expenses
                projected_income = price_per_person * target_participants
                st.write(f"Projected Income: KD {projected_income:.2f}")
                
                projected_expenses = st.number_input("Projected Expenses (KD)", min_value=0.0, format="%.2f")
                projected_profit = projected_income - projected_expenses
                st.write(f"Projected Profit: KD {projected_profit:.2f}")
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
            
            submit = st.form_submit_button("Create Event", use_container_width=True)
            
            if submit:
                if not event_name or not event_date:
                    st.error("Event name and date are required")
                else:
                    success, message, event_id = create_event_budget(
                        event_name,
                        event_date.strftime("%Y-%m-%d"),
                        location,
                        coordinator,
                        event_type,
                        projected_income,
                        projected_expenses,
                        price_per_person,
                        target_participants,
                        description
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # Close the responsive-form div
        st.markdown('</div>', unsafe_allow_html=True)
    
    # TAB 2: Manage existing events
    with tab2:
        st.subheader("Manage Existing Events")
        
        if not st.session_state.events:
            st.info("No events created yet. Use the 'Create Events' tab to add an event.")
        else:
            # Create a selectbox to choose an event to manage
            event_options = [(e.get("name", "Unnamed Event"), e.get("id")) for e in st.session_state.events]
            event_names, event_ids = zip(*event_options)
            selected_event_name = st.selectbox("Select event to manage", event_names)
            selected_event_id = event_ids[event_names.index(selected_event_name)]
            
            # Get the selected event
            event = next((e for e in st.session_state.events if e.get("id") == selected_event_id), None)
            
            if event:
                # Display event details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Date:** {event['date']}")
                    st.write(f"**Location:** {event['location']}")
                    st.write(f"**Event Type:** {event['event_type']}")
                    st.write(f"**Coordinator:** {event['coordinator']}")
                
                with col2:
                    st.write(f"**Price per Person:** KD {event['price_per_person']:.2f}")
                    st.write(f"**Target Participants:** {event['target_participants']}")
                    st.write(f"**Status:** {event['status']}")
                    
                    # Calculate actual profit
                    profit = event["actual_income"] - event["actual_expenses"]
                    st.write(f"**Current Profit:** KD {profit:.2f}")
                
                st.write(f"**Description:** {event.get('description', '')}")
                
                # Show financial summary
                st.subheader("Financial Summary")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Income", f"KD {event['actual_income']:.2f}", 
                             f"{event['actual_income'] - event['projected_income']:.2f}")
                
                with col2:
                    st.metric("Expenses", f"KD {event['actual_expenses']:.2f}", 
                             f"{event['actual_expenses'] - event['projected_expenses']:.2f}")
                
                with col3:
                    st.metric("Profit", f"KD {profit:.2f}", 
                             f"{profit - (event['projected_income'] - event['projected_expenses']):.2f}")
                
                # Update event status
                new_status = st.selectbox("Update Status", 
                                         ["Planning", "Active", "Completed"],
                                         index=["Planning", "Active", "Completed"].index(event["status"]))
                
                if new_status != event["status"]:
                    event["status"] = new_status
                    st.success(f"Updated {event['name']} status to {new_status}")
                
                # Add tabs for participants and expenses
                participant_tab, expense_tab = st.tabs(["Manage Participants", "Manage Expenses"])
                
                # TAB: Manage participants
                with participant_tab:
                    st.subheader("Participant Payments")
                    
                    # Add new participant payment
                    with st.expander("Add Participant Payment", expanded=True):
                        with st.form(f"participant_form_{event['id']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                participant_name = st.text_input("Participant Name")
                                payment_date = st.date_input("Payment Date", value=datetime.date.today())
                            
                            with col2:
                                payment_amount = st.number_input("Payment Amount (KD)", 
                                                              min_value=0.0, 
                                                              value=float(event["price_per_person"]),
                                                              format="%.2f")
                                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Check", "Other"])
                            
                            # FIX: Remove the height parameter
                            notes = st.text_area("Notes")
                            
                            submit = st.form_submit_button("Add Payment", use_container_width=True)
                            
                            if submit:
                                if not participant_name:
                                    st.error("Participant name is required")
                                else:
                                    success, message, _ = add_event_participant(
                                        event["id"],
                                        participant_name,
                                        payment_amount,
                                        payment_date.strftime("%Y-%m-%d"),
                                        payment_method,
                                        notes
                                    )
                                    
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                    
                    # View existing participants
                    participants = [p for p in st.session_state.event_participants if p.get("event_id") == event["id"]]
                    
                    if participants:
                        st.subheader(f"Participants ({len(participants)})")
                        
                        # Create dataframe for display
                        participants_df = pd.DataFrame(participants)
                        
                        # Format currency columns
                        participants_df["payment_amount"] = participants_df["payment_amount"].apply(lambda x: f"KD {x:.2f}")
                        
                        # Rename columns for display
                        display_df = participants_df.rename(columns={
                            "participant_name": "Name",
                            "payment_amount": "Amount",
                            "payment_date": "Date",
                            "payment_method": "Method",
                            "notes": "Notes"
                        })
                        
                        # Select columns to display
                        display_columns = ["Name", "Amount", "Date", "Method", "Notes"]
                        display_columns = [col for col in display_columns if col in display_df.columns]
                        
                        st.dataframe(display_df[display_columns], use_container_width=True)
                        
                        # Summary metrics
                        total_received = sum(p["payment_amount"] for p in participants)
                        avg_payment = total_received / len(participants) if participants else 0
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Received", f"KD {total_received:.2f}")
                        
                        with col2:
                            st.metric("Average Payment", f"KD {avg_payment:.2f}")
                        
                        with col3:
                            st.metric("Participation", f"{len(participants)}/{event['target_participants']}")
                        
                        # Export participant list
                        st.subheader("Export Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Export Participants to CSV", key="part_csv", use_container_width=True):
                                csv = participants_df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"{event['name']}_participants.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                        
                        with col2:
                            if st.button("Export Participants to PDF", key="part_pdf", use_container_width=True):
                                # Generate PDF content
                                styles = getSampleStyleSheet()
                                title_style = styles['Heading1']
                                subtitle_style = styles['Heading2']
                                normal_style = styles['Normal']
                                
                                elements = []
                                
                                # Event details
                                elements.append(Paragraph("Event Details", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                details_data = [
                                    ["Event Name", event['name']],
                                    ["Date", event['date']],
                                    ["Location", event['location']],
                                    ["Price per Person", f"KD {event['price_per_person']:.2f}"]
                                ]
                                
                                details_table = Table(details_data, colWidths=[2*inch, 3*inch])
                                details_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                elements.append(details_table)
                                elements.append(Spacer(1, 0.2*inch))
                                
                                # Participant list
                                elements.append(Paragraph("Participant List", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                table_data = [["Name", "Amount", "Date", "Method", "Notes"]]
                                
                                for participant in participants:
                                    table_data.append([
                                        participant.get("participant_name", ""),
                                        f"KD {participant.get('payment_amount', 0):.2f}",
                                        participant.get("payment_date", ""),
                                        participant.get("payment_method", ""),
                                        participant.get("notes", "")
                                    ])
                                
                                # Create the table
                                part_table = Table(table_data, colWidths=[1*inch, 1*inch, 1*inch, 1*inch, 2*inch])
                                part_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                elements.append(part_table)
                                elements.append(Spacer(1, 0.2*inch))
                                
                                # Summary section
                                elements.append(Paragraph("Payment Summary", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                summary_data = [
                                    ["Metric", "Value"],
                                    ["Total Participants", str(len(participants))],
                                    ["Total Received", f"KD {total_received:.2f}"],
                                    ["Average Payment", f"KD {avg_payment:.2f}"],
                                    ["Target Participants", str(event['target_participants'])],
                                    ["Participation Rate", f"{len(participants) / event['target_participants'] * 100:.1f}%" if event['target_participants'] > 0 else "0%"]
                                ]
                                
                                summary_table = Table(summary_data, colWidths=[2*inch, 3*inch])
                                summary_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                elements.append(summary_table)
                                
                                # Generate the PDF
                                pdf = create_pdf_content(f"Participant List - {event['name']}", elements)
                                
                                # Create download link
                                st.markdown(
                                    get_pdf_download_link(pdf, f"{event['name']}_participants.pdf", "Download PDF Report"),
                                    unsafe_allow_html=True
                                )
                    else:
                        st.info("No participant payments recorded yet.")
                
                # TAB: Manage expenses
                with expense_tab:
                    st.subheader("Event Expenses")
                    
                    # Add new expense
                    with st.expander("Add Expense", expanded=True):
                        with st.form(f"expense_form_{event['id']}"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                expense_description = st.text_input("Expense Description")
                                expense_date = st.date_input("Expense Date", value=datetime.date.today())
                                expense_amount = st.number_input("Amount (KD)", min_value=0.0, format="%.2f")
                            
                            with col2:
                                # Get expense categories from budget
                                expense_categories = list(st.session_state.budget["expenses"].keys())
                                expense_category = st.selectbox("Expense Category", expense_categories)
                                
                                paid_to = st.text_input("Paid To")
                                receipt_num = st.text_input("Receipt #")
                            
                            # FIX: Remove the height parameter
                            notes = st.text_area("Notes")
                            
                            submit = st.form_submit_button("Add Expense", use_container_width=True)
                            
                            if submit:
                                if not expense_description:
                                    st.error("Expense description is required")
                                else:
                                    success, message, _ = add_event_expense(
                                        event["id"],
                                        expense_description,
                                        expense_amount,
                                        expense_date.strftime("%Y-%m-%d"),
                                        expense_category,
                                        paid_to,
                                        receipt_num,
                                        notes
                                    )
                                    
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                    
                    # View existing expenses
                    expenses = [e for e in st.session_state.event_expenses if e.get("event_id") == event["id"]]
                    
                    if expenses:
                        st.subheader(f"Expenses ({len(expenses)})")
                        
                        # Create dataframe for display
                        expenses_df = pd.DataFrame(expenses)
                        
                        # Format currency columns
                        expenses_df["amount"] = expenses_df["amount"].apply(lambda x: f"KD {x:.2f}")
                        
                        # Rename columns for display
                        display_df = expenses_df.rename(columns={
                            "description": "Description",
                            "amount": "Amount",
                            "date": "Date",
                            "category": "Category",
                            "paid_to": "Paid To",
                            "receipt_num": "Receipt #",
                            "notes": "Notes"
                        })
                        
                        # Select columns to display
                        display_columns = ["Description", "Amount", "Date", "Category", "Paid To", "Receipt #", "Notes"]
                        display_columns = [col for col in display_columns if col in display_df.columns]
                        
                        st.dataframe(display_df[display_columns], use_container_width=True)
                        
                        # Expense breakdown by category
                        st.subheader("Expense Breakdown by Category")
                        
                        # Group expenses by category
                        expense_categories = {}
                        for expense in expenses:
                            category = expense.get("category", "Other")
                            if category not in expense_categories:
                                expense_categories[category] = 0
                            expense_categories[category] += expense["amount"]
                        
                        # Create dataframe for category breakdown
                        category_data = []
                        for category, amount in expense_categories.items():
                            category_data.append({
                                "Category": category,
                                "Amount": f"KD {amount:.2f}",
                                "Percentage": f"{amount / sum(expense_categories.values()) * 100:.1f}%"
                            })
                        
                        if category_data:
                            category_df = pd.DataFrame(category_data)
                            st.dataframe(category_df, use_container_width=True)
                        
                        # Export expense list
                        st.subheader("Export Options")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("Export Expenses to CSV", key="exp_csv", use_container_width=True):
                                csv = expenses_df.to_csv(index=False)
                                st.download_button(
                                    label="Download CSV",
                                    data=csv,
                                    file_name=f"{event['name']}_expenses.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                        
                        with col2:
                            if st.button("Export Expenses to PDF", key="exp_pdf", use_container_width=True):
                                # Generate PDF content
                                styles = getSampleStyleSheet()
                                title_style = styles['Heading1']
                                subtitle_style = styles['Heading2']
                                normal_style = styles['Normal']
                                
                                elements = []
                                
                                # Event details
                                elements.append(Paragraph("Event Details", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                details_data = [
                                    ["Event Name", event['name']],
                                    ["Date", event['date']],
                                    ["Location", event['location']],
                                    ["Type", event['event_type']]
                                ]
                                
                               details_table = Table(details_data, colWidths=[2*inch, 3*inch])
                               details_table.setStyle(TableStyle([
                                  ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                     ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                                     ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                 ]))
                                
                                elements.append(details_table)
                                elements.append(Spacer(1, 0.2*inch))
                                
                                # Expense list
                                elements.append(Paragraph("Expense List", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                table_data = [["Description", "Amount", "Date", "Category", "Paid To", "Receipt #"]]
                                
                                for expense in expenses:
                                    table_data.append([
                                        expense.get("description", ""),
                                        f"KD {expense.get('amount', 0):.2f}",
                                        expense.get("date", ""),
                                        expense.get("category", ""),
                                        expense.get("paid_to", ""),
                                        expense.get("receipt_num", "")
                                    ])
                                
                                # Create the table with adjusted widths
                                exp_table = Table(table_data, colWidths=[1.5*inch, 0.8*inch, 0.8*inch, 1*inch, 1*inch, 0.8*inch])
                                exp_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                elements.append(exp_table)
                                elements.append(Spacer(1, 0.2*inch))
                                
                                # Expense breakdown by category
                                elements.append(Paragraph("Expense Breakdown by Category", subtitle_style))
                                elements.append(Spacer(1, 0.1*inch))
                                
                                category_table_data = [["Category", "Amount", "Percentage"]]
                                
                                total_expense_amount = sum(expense_categories.values())
                                
                                for category, amount in expense_categories.items():
                                    percentage = amount / total_expense_amount * 100 if total_expense_amount > 0 else 0
                                    category_table_data.append([
                                        category,
                                        f"KD {amount:.2f}",
                                        f"{percentage:.1f}%"
                                    ])
                                
                                # Create the category breakdown table
                                cat_table = Table(category_table_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
                                cat_table.setStyle(TableStyle([
                                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                                ]))
                                
                                elements.append(cat_table)
                                
                                # Generate the PDF
                                pdf = create_pdf_content(f"Expense Report - {event['name']}", elements)
                                
                                # Create download link
                                st.markdown(
                                    get_pdf_download_link(pdf, f"{event['name']}_expenses.pdf", "Download PDF Report"),
                                    unsafe_allow_html=True
                                )
                    else:
                        st.info("No expenses recorded yet.")
    
    # TAB 3: Event Reports
    with tab3:
        st.subheader("Event Reports")
        
        # Create tabs for different report types
        report_tab1, report_tab2 = st.tabs(["Individual Event Report", "All Events Summary"])
        
        # Individual event report
        with report_tab1:
            if not st.session_state.events:
                st.info("No events to report on. Please create events first.")
            else:
                # Create a selectbox to choose an event to report on
                event_options = [(e.get("name", "Unnamed Event"), e.get("id")) for e in st.session_state.events]
                event_names, event_ids = zip(*event_options)
                selected_event_name = st.selectbox("Select event for report", event_names, key="report_event_select")
                selected_event_id = event_ids[event_names.index(selected_event_name)]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Generate Event Report", use_container_width=True):
                        # Generate the report
                        report = generate_event_report(selected_event_id)
                        
                        if report:
                            event = report["event"]
                            
                            # Display report header
                            st.header(f"Event Report: {event['name']}")
                            st.write(f"**Date:** {event['date']}")
                            st.write(f"**Location:** {event['location']}")
                            st.write(f"**Type:** {event['event_type']}")
                            st.write(f"**Status:** {event['status']}")
                            
                            # Financial summary
                            st.subheader("Financial Summary")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Total Income", f"KD {report['total_payments']:.2f}")
                            
                            with col2:
                                st.metric("Total Expenses", f"KD {report['total_expenses']:.2f}")
                            
                            with col3:
                                st.metric("Profit", f"KD {report['profit']:.2f}")
                            
                            # Additional metrics
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric("Participants", f"{report['participant_count']}")
                            
                            with col2:
                                st.metric("Target", f"{event['target_participants']}")
                            
                            with col3:
                                participation_rate = report['participant_count'] / event['target_participants'] * 100 if event['target_participants'] > 0 else 0
                                st.metric("Participation Rate", f"{participation_rate:.1f}%")
                            
                            # Expense breakdown by category
                            st.subheader("Expense Breakdown")
                            
                            if report["expense_breakdown"]:
                                expense_data = []
                                for category, amount in report["expense_breakdown"].items():
                                    expense_data.append({
                                        "Category": category,
                                        "Amount": f"KD {amount:.2f}",
                                        "Percentage": f"{amount / report['total_expenses'] * 100:.1f}%" if report['total_expenses'] > 0 else "0%"
                                    })
                                
                                expense_df = pd.DataFrame(expense_data)
                                st.dataframe(expense_df, use_container_width=True)
                            else:
                                st.info("No expense data available.")
                            
                            # Participant list
                            st.subheader("Participant List")
                            
                            if report["participants"]:
                                participants_df = pd.DataFrame(report["participants"])
                                participants_df["payment_amount"] = participants_df["payment_amount"].apply(lambda x: f"KD {x:.2f}")
                                
                                # Rename columns for display
                                display_df = participants_df.rename(columns={
                                    "participant_name": "Name",
                                    "payment_amount": "Amount",
                                    "payment_date": "Date",
                                    "payment_method": "Method",
                                    "notes": "Notes"
                                })
                                
                                # Select columns to display
                                display_columns = ["Name", "Amount", "Date", "Method", "Notes"]
                                display_columns = [col for col in display_columns if col in display_df.columns]
                                
                                st.dataframe(display_df[display_columns], use_container_width=True)
                            else:
                                st.info("No participants recorded.")
                            
                            # Expense list
                            st.subheader("Expense List")
                            
                            if report["expenses"]:
                                expenses_df = pd.DataFrame(report["expenses"])
                                expenses_df["amount"] = expenses_df["amount"].apply(lambda x: f"KD {x:.2f}")
                                
                                # Rename columns for display
                                display_df = expenses_df.rename(columns={
                                    "description": "Description",
                                    "amount": "Amount",
                                    "date": "Date",
                                    "category": "Category",
                                    "paid_to": "Paid To",
                                    "receipt_num": "Receipt #",
                                    "notes": "Notes"
                                })
                                
                                # Select columns to display
                                display_columns = ["Description", "Amount", "Date", "Category", "Paid To", "Receipt #", "Notes"]
                                display_columns = [col for col in display_columns if col in display_df.columns]
                                
                                st.dataframe(display_df[display_columns], use_container_width=True)
                            else:
                                st.info("No expenses recorded.")
                            
                            # Export options
                            st.subheader("Export Options")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                if st.button("Export Participants to CSV", key="report_part_csv", use_container_width=True):
                                    if report["participants"]:
                                        participants_df = pd.DataFrame(report["participants"])
                                        csv = participants_df.to_csv(index=False)
                                        st.download_button(
                                            label="Download Participants CSV",
                                            data=csv,
                                            file_name=f"{event['name']}_participants.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                            
                            with col2:
                                if st.button("Export Expenses to CSV", key="report_exp_csv", use_container_width=True):
                                    if report["expenses"]:
                                        expenses_df = pd.DataFrame(report["expenses"])
                                        csv = expenses_df.to_csv(index=False)
                                        st.download_button(
                                            label="Download Expenses CSV",
                                            data=csv,
                                            file_name=f"{event['name']}_expenses.csv",
                                            mime="text/csv",
                                            use_container_width=True
                                        )
                            
                            with col3:
                                if st.button("Export Full Report to PDF", key="full_report_pdf", use_container_width=True):
                                    # Generate the PDF report
                                    pdf = create_event_report_pdf(report)
                                    
                                    # Create download link
                                    st.markdown(
                                        get_pdf_download_link(pdf, f"{event['name']}_full_report.pdf", "Download Full PDF Report"),
                                        unsafe_allow_html=True
                                    )
                        else:
                            st.error("Could not generate report. Please try again.")
                
                with col2:
                    # Export the report directly to PDF without generating the visual report first
                    if st.button("Export Event Report PDF", key="direct_pdf_export", use_container_width=True):
                        report = generate_event_report(selected_event_id)
                        
                        if report:
                            # Generate the PDF
                            pdf = create_event_report_pdf(report)
                            
                            # Create download link
                            st.markdown(
                                get_pdf_download_link(pdf, f"{report['event']['name']}_report.pdf", "Download PDF Report"),
                                unsafe_allow_html=True
                            )
                        else:
                            st.error("Could not generate report. Please try again.")
        
        # All events summary report
        with report_tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Generate All Events Summary", use_container_width=True):
                    # Generate the summary report
                    report = generate_all_events_report()
                    
                    if report:
                        st.header("All Events Financial Summary")
                        
                        # Overall metrics
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Total Income", f"KD {report['total_income']:.2f}")
                        
                        with col2:
                            st.metric("Total Expenses", f"KD {report['total_expenses']:.2f}")
                        
                        with col3:
                            st.metric("Total Profit", f"KD {report['total_profit']:.2f}")
                        
                        # Event summary table
                        st.subheader(f"Event Summary ({report['event_count']} events)")
                        
                        if report["events"]:
                            # Create a DataFrame for display
                            events_df = pd.DataFrame(report["events"])
                            
                            # Format currency columns
                            events_df["income"] = events_df["income"].apply(lambda x: f"KD {x:.2f}")
                            events_df["expenses"] = events_df["expenses"].apply(lambda x: f"KD {x:.2f}")
                            events_df["profit"] = events_df["profit"].apply(lambda x: f"KD {x:.2f}")
                            
                            # Rename columns for display
                            display_df = events_df.rename(columns={
                                "name": "Event Name",
                                "date": "Date",
                                "location": "Location",
                                "event_type": "Type",
                                "participants": "Participants",
                                "income": "Income",
                                "expenses": "Expenses",
                                "profit": "Profit",
                                "status": "Status"
                            })
                            
                            # Select columns to display
                            display_columns = ["Event Name", "Date", "Type", "Participants", 
                                             "Income", "Expenses", "Profit", "Status"]
                            display_columns = [col for col in display_columns if col in display_df.columns]
                            
                            st.dataframe(display_df[display_columns], use_container_width=True)
                            
                            # Export options
                            st.subheader("Export Options")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("Export Events Summary to CSV", key="all_events_csv", use_container_width=True):
                                    csv = display_df.to_csv(index=False)
                                    st.download_button(
                                        label="Download Events Summary CSV",
                                        data=csv,
                                        file_name="events_summary.csv",
                                        mime="text/csv",
                                        use_container_width=True
                                    )
                            
                            with col2:
                                if st.button("Export All Events Report to PDF", key="all_events_pdf", use_container_width=True):
                                    # Generate the PDF
                                    pdf = create_all_events_report_pdf(report)
                                    
                                    # Create download link
                                    st.markdown(
                                        get_pdf_download_link(pdf, "all_events_report.pdf", "Download PDF Report"),
                                        unsafe_allow_html=True
                                    )
                        else:
                            st.info("No events data available.")
                    else:
                        st.error("Could not generate report. Please try again.")
            
            with col2:
                # Export all events report directly to PDF without generating the visual report first
                if st.button("Export All Events PDF", key="direct_all_events_pdf", use_container_width=True):
                    report = generate_all_events_report()
                    
                    if report:
                        # Generate the PDF
                        pdf = create_all_events_report_pdf(report)
                        
                        # Create download link
                        st.markdown(
                            get_pdf_download_link(pdf, "all_events_report.pdf", "Download PDF Report"),
                            unsafe_allow_html=True
                        )
                    else:
                        st.error("Could not generate report. Please try again.")

# Reports function (enhanced with PDF export)
def show_reports():
    st.header("Financial Reports")
    
    # Report type selection - use a container for responsiveness
    with st.container():
        report_type = st.radio("Report Type", 
                              ["Monthly Summary", "Year-to-Date", "Event Analysis", "Fundraising Results"],
                              horizontal=True if st.session_state.device_type != "mobile" else False)
    
    if report_type == "Monthly Summary":
        # Month and year selection
        # Use the mobile-stack class for responsive columns
        cols_div = '<div class="mobile-stack">'
        st.markdown(cols_div, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            month_names = [
                "January", "February", "March", "April", "May", "June", 
                "July", "August", "September", "October", "November", "December"
            ]
            selected_month = st.selectbox("Month", month_names)
            month_index = month_names.index(selected_month) + 1
        
        with col2:
            current_year = datetime.datetime.now().year
            selected_year = st.selectbox("Year", 
                                        list(range(current_year-2, current_year+3)))
        
        # Close the mobile-stack div
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Generate report buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Report", use_container_width=True):
                report = generate_monthly_report(month_index, selected_year)
                
                # Display report
                st.subheader(f"Monthly Financial Report - {selected_month} {selected_year}")
                
                # Summary metrics
                # Use the mobile-stack class for responsive columns
                cols_div = '<div class="mobile-stack">'
                st.markdown(cols_div, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Income", f"KD {report['total_income']:.2f}")
                
                with col2:
                    st.metric("Total Expenses", f"KD {report['total_expenses']:.2f}")
                
                with col3:
                    st.metric("Net", f"KD {report['net']:.2f}")
                
                # Close the mobile-stack div
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Overall financial position
                st.subheader("Overall Financial Position")
                
                # Use the mobile-stack class for responsive columns
                cols_div = '<div class="mobile-stack">'
                st.markdown(cols_div, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Balance", f"KD {report['current_balance']:.2f}")
                
                with col2:
                    st.metric("Emergency Reserve", f"KD {report['emergency_reserve']:.2f}")
                
                with col3:
                    st.metric("Available Funds", f"KD {report['available_funds']:.2f}")
                
                # Close the mobile-stack div
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Transactions
                st.subheader("Transactions")
                
                if report['transactions']:
                    transactions_df = pd.DataFrame(report['transactions'])
                    # Format currency columns
                    transactions_df["income"] = transactions_df["income"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
                    transactions_df["expense"] = transactions_df["expense"].apply(lambda x: f"KD {x:.2f}" if x > 0 else "")
                    # Select columns to display
                    display_columns = [col for col in ["date", "description", "category", "income", "expense", "authorized_by"]
                                    if col in transactions_df.columns]
                    st.dataframe(transactions_df[display_columns], use_container_width=True)
                    
                    # Export options
                    st.subheader("Export Options")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("Export to CSV", key="monthly_csv", use_container_width=True):
                            csv = transactions_df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"monthly_report_{selected_month}_{selected_year}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                    with col2:
                        if st.button("Export to PDF", key="monthly_pdf", use_container_width=True):
                            # Generate the PDF
                            pdf = create_monthly_report_pdf(report, selected_month, selected_year)
                            
                            # Create download link
                            st.markdown(
                                get_pdf_download_link(pdf, f"monthly_report_{selected_month}_{selected_year}.pdf", "Download PDF Report"),
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No transactions for this period.")
        
        with col2:
            # Direct PDF export without generating the visual report first
            if st.button("Export Monthly Report PDF", key="direct_monthly_pdf", use_container_width=True):
                report = generate_monthly_report(month_index, selected_year)
                
                # Generate the PDF
                pdf = create_monthly_report_pdf(report, selected_month, selected_year)
                
                # Create download link
                st.markdown(
                    get_pdf_download_link(pdf, f"monthly_report_{selected_month}_{selected_year}.pdf", "Download PDF Report"),
                    unsafe_allow_html=True
                )
    
    elif report_type == "Event Analysis":
        # Redirect to the events report tab
        st.info("Please use the Events section for detailed event reports.")
        
        if st.button("Go to Event Reports", use_container_width=True):
            st.session_state.page = "events"
            st.rerun()
    
    else:
        st.info(f"{report_type} reports are available in the full version.")
        st.write("Please add transactions and events to generate more detailed reports.")

# Fundraising function (simplified)
def show_fundraising():
    st.header("Fundraising Management")
    
    # Add new fundraising initiative
    with st.expander("Add New Fundraising Initiative", expanded=True):
        # Add the responsive-form class
        st.markdown('<div class="responsive-form">', unsafe_allow_html=True)
        
        with st.form("fundraising_form"):
            # Use the mobile-stack class for responsive columns
            cols_div = '<div class="mobile-stack">'
            st.markdown(cols_div, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Initiative Name")
                dates = st.text_input("Dates (e.g., Apr 15-20)")
            
            with col2:
                coordinator = st.selectbox("Coordinator", list(committee_members.keys()))
                goal_amount = st.number_input("Goal Amount (KD)", min_value=0.0, format="%.2f")
            
            # Close the mobile-stack div
            st.markdown('</div>', unsafe_allow_html=True)
            
            submit = st.form_submit_button("Add Initiative", use_container_width=True)
            
            if submit:
                if not name:
                    st.error("Initiative name is required")
                else:
                    success, message = add_fundraising_initiative(
                        name,
                        dates,
                        coordinator,
                        goal_amount
                    )
                    
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        # Close the responsive-form div
        st.markdown('</div>', unsafe_allow_html=True)
    
    # View fundraising initiatives
    st.subheader("Fundraising Initiatives")
    
    if st.session_state.fundraising:
        try:
            fundraising_df = pd.DataFrame(st.session_state.fundraising)
            # Format currency columns
            fundraising_df["goal_amount"] = fundraising_df["goal_amount"].apply(lambda x: f"KD {x:.2f}")
            fundraising_df["actual_raised"] = fundraising_df["actual_raised"].apply(lambda x: f"KD {x:.2f}")
            fundraising_df["expenses"] = fundraising_df["expenses"].apply(lambda x: f"KD {x:.2f}")
            fundraising_df["net_proceeds"] = fundraising_df["net_proceeds"].apply(lambda x: f"KD {x:.2f}")
            # Rename columns for display
            display_df = fundraising_df.rename(columns={
                "name": "Initiative Name",
                "dates": "Dates",
                "coordinator": "Coordinator",
                "goal_amount": "Goal Amount",
                "actual_raised": "Amount Raised",
                "expenses": "Expenses",
                "net_proceeds": "Net Proceeds",
                "status": "Status"
            })
            # Select columns to display
            display_columns = [col for col in ["Initiative Name", "Dates", "Coordinator", 
                              "Goal Amount", "Amount Raised", "Status"]
                              if col in display_df.columns]
            st.dataframe(display_df[display_columns], use_container_width=True)
            
            # Export options
            st.subheader("Export Options")
            
            if st.button("Export Fundraising Initiatives to PDF", use_container_width=True):
                # Generate PDF content
                styles = getSampleStyleSheet()
                title_style = styles['Heading1']
                subtitle_style = styles['Heading2']
                normal_style = styles['Normal']
                
                elements = []
                
                # Fundraising initiatives table
                elements.append(Paragraph("Fundraising Initiatives", subtitle_style))
                elements.append(Spacer(1, 0.1*inch))
                
                table_data = [["Initiative Name", "Dates", "Coordinator", "Goal Amount", "Amount Raised", "Status"]]
                
                for _, row in display_df.iterrows():
                    table_data.append([
                        row.get("Initiative Name", ""),
                        row.get("Dates", ""),
                        row.get("Coordinator", ""),
                        row.get("Goal Amount", ""),
                        row.get("Amount Raised", ""),
                        row.get("Status", "")
                    ])
                
                # Create the table
                fund_table = Table(table_data)
                fund_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                elements.append(fund_table)
                
                # Generate the PDF
                pdf = create_pdf_content("Fundraising Initiatives", elements)
                
                # Create download link
                st.markdown(
                    get_pdf_download_link(pdf, "fundraising_initiatives.pdf", "Download PDF Report"),
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.error(f"Error displaying fundraising initiatives: {e}")
            st.write(fundraising_df)
    else:
        st.info("No fundraising initiatives created yet.")

# Save and load functions
def save_data():
    data = {
        "budget": st.session_state.budget,
        "transactions": st.session_state.transactions,
        "events": st.session_state.events,
        "event_participants": st.session_state.event_participants,
        "event_expenses": st.session_state.event_expenses,
        "fundraising": st.session_state.fundraising
    }
    
    # Convert to JSON
    json_data = json.dumps(data, indent=4)
    
    # Provide download link
    st.download_button(
        label="Download Data Backup",
        data=json_data,
        file_name="financial_system_backup.json",
        mime="application/json",
        use_container_width=True
    )
    
    st.success("Data prepared for download")

def load_data():
    uploaded_file = st.file_uploader("Upload backup file", type=["json"])
    
    if uploaded_file:
        try:
            # Read the file
            data = json.load(uploaded_file)
            
            # Update session state
            st.session_state.budget = data.get("budget", st.session_state.budget)
            st.session_state.transactions = data.get("transactions", st.session_state.transactions)
            st.session_state.events = data.get("events", st.session_state.events)
            st.session_state.event_participants = data.get("event_participants", st.session_state.event_participants)
            st.session_state.event_expenses = data.get("event_expenses", st.session_state.event_expenses)
            st.session_state.fundraising = data.get("fundraising", st.session_state.fundraising)
            
            st.success("Data loaded successfully")
            st.rerun()
        except Exception as e:
            st.error(f"Error loading data: {e}")

# Logout function
def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()

# Settings functions
def show_settings():
    st.header("Settings")
    
    # Save/Load data
    st.subheader("Data Backup and Restore")
    
    # Use the mobile-stack class for responsive columns
    cols_div = '<div class="mobile-stack">'
    st.markdown(cols_div, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Save current data to a file:")
        if st.button("Prepare Backup File", use_container_width=True):
            save_data()
    
    with col2:
        st.write("Load data from a backup file:")
        load_data()
    
    # Close the mobile-stack div
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Password management
    st.subheader("User Management")
    st.info("For security reasons, user credentials can only be modified directly in the source code.")
    st.write("Please contact the system administrator to add or update user accounts.")
    
    # Display current user info
    st.subheader("Current Login Information")
    st.write(f"**Username:** {st.session_state.username}")
    st.write(f"**Role:** {st.session_state.user_role}")
    st.write(f"**Login time:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Main app
def main():
    # Check if user is authenticated
    if not st.session_state.authenticated:
        show_login()
        return
    
    # Sidebar navigation
    st.sidebar.title("Year 11 Committee")
    st.sidebar.subheader("Financial Management System")
    
    # Display user role
    st.sidebar.info(f"Logged in as: {st.session_state.username.upper()} ({st.session_state.user_role})")
    
    # Add logout button
    if st.sidebar.button("Logout", use_container_width=True):
        logout()
    
    # Set default page if not exists
    if 'page' not in st.session_state:
        st.session_state.page = 'dashboard'
    
    # Navigate based on user role
    if st.session_state.user_role == "admin":
        # Full access for admin
        page = st.sidebar.radio("Navigation", 
                               ["Dashboard", "Transactions", "Budget", "Events", 
                                "Fundraising", "Reports", "Settings"],
                               index=["dashboard", "transactions", "budget", "events", 
                                     "fundraising", "reports", "settings"].index(st.session_state.page))
    else:
        # Limited access for viewer
        page = st.sidebar.radio("Navigation", 
                               ["Dashboard", "Events", "Reports"],
                               index=["dashboard", "events", "reports"].index(st.session_state.page)
                               if st.session_state.page in ["dashboard", "events", "reports"] else 0)
    
    # Store the current page
    st.session_state.page = page.lower()
    
    # Display the selected page based on user role
    if st.session_state.page == 'dashboard':
        show_dashboard()
    elif st.session_state.page == 'events':
        show_events()
    elif st.session_state.page == 'reports':
        show_reports()
    elif st.session_state.user_role == "admin":
        # Only admin can access these pages
        if st.session_state.page == 'transactions':
            show_transactions()
        elif st.session_state.page == 'budget':
            show_budget()
        elif st.session_state.page == 'fundraising':
            show_fundraising()
        elif st.session_state.page == 'settings':
            show_settings()
    
    # Display footer
    st.sidebar.markdown("---")
    st.sidebar.info(
        "Developed by Deema Abououf\n\n"
        "Treasurer/Finance Manager\n"
        "Year 11 Committee"
    )

if __name__ == '__main__':
    main()
