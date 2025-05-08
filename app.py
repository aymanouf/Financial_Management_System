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
