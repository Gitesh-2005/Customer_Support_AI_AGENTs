# admin_app.py
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx
import requests
import pandas as pd
import plotly.express as px
import time

API_URL = "http://127.0.0.1:8000"

# Force refresh on page load
if 'last_refresh' not in st.session_state:
    st.session_state['last_refresh'] = time.time()

st.sidebar.title("Admin Navigation")
page = st.sidebar.radio("Go to", ["Admin Dashboard", "Team Management", "Agent Metrics"])

if page == "Admin Dashboard":
    st.title("Support Ticket Dashboard")
    
    # Add manual refresh button
    if st.button("Refresh Data"):
        st.session_state['last_refresh'] = time.time()
    
    try:
        response = requests.get(f"{API_URL}/get_tickets/")
        if response.ok:
            tickets = response.json()
            if tickets:
                # Convert to DataFrame
                df = pd.DataFrame(tickets)
                
                # Show statistics
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Tickets", len(df))
                with col2:
                    pending = len(df[df['status'] == 'Pending']) if 'status' in df.columns else 0
                    st.metric("Pending Tickets", pending)
                
                # Display tickets
                st.subheader("Recent Tickets")
                if not df.empty:
                    # Ensure proper column order
                    columns_to_display = ['id', 'customer_name', 'issue_text', 'status', 'created_at']
                    display_df = df.sort_values('created_at', ascending=False)
                    st.dataframe(display_df[columns_to_display], height=400)
                    
                    # Ticket details viewer with formatted AI analysis
                    st.subheader("Ticket Details")
                    ticket_id = st.selectbox("Select Ticket ID", display_df['id'].tolist())
                    if ticket_id:
                        ticket = display_df[display_df['id'] == ticket_id].iloc[0]
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("### Basic Information")
                            st.write(f"**Customer:** {ticket['customer_name']}")
                            st.write(f"**Issue:** {ticket['issue_text']}")
                            st.write(f"**Status:** {ticket.get('status', 'Pending')}")
                        
                        if 'ai_response' in ticket and ticket['ai_response']:
                            with col2:
                                st.write("### AI Analysis")
                                ai_response = ticket['ai_response']
                                
                                # Display Summary
                                if 'summary' in ai_response:
                                    with st.expander("📝 Summary", expanded=True):
                                        st.write(ai_response['summary'].get('text', ''))
                                
                                # Display Actions
                                if 'actions' in ai_response:
                                    with st.expander("🔧 Recommended Actions", expanded=True):
                                        for action in ai_response['actions']:
                                            st.write(f"**{action.get('type', 'Action')}:** {action.get('description', '')}")
                                
                                # Display Recommendation
                                if 'recommendation' in ai_response:
                                    with st.expander("✅ Solution & Steps", expanded=True):
                                        st.write(f"**Solution:** {ai_response['recommendation'].get('solution', '')}")
                                        steps = ai_response['recommendation'].get('steps', [])
                                        if steps:
                                            st.write("**Steps:**")
                                            for i, step in enumerate(steps, 1):
                                                st.write(f"{i}. {step}")
                                        st.write(f"**Confidence:** {ai_response['recommendation'].get('confidence', 0)}%")
            else:
                st.info("No tickets available")
        else:
            st.error(f"Failed to fetch tickets: {response.status_code}")
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.caption(f"Last updated: {time.strftime('%H:%M:%S', time.localtime(st.session_state['last_refresh']))}")

elif page == "Team Management":
    st.title("Team Management")
    st.write("Manage teams and their specialties.")
    teams_response = requests.get(f"{API_URL}/admin/teams")
    if teams_response.ok:
        teams = teams_response.json()
        if teams:
            st.subheader("Teams Overview")
            cols = st.columns(3)
            for i, team in enumerate(teams):
                with cols[i % 3]:
                    st.markdown(f"### {team['name']}")
                    st.write(f"*Specialty:* {team['specialty']}")
                    st.write(f"*Resolution Rate:* {team['resolution_rate']}%")
                    st.write(f"*Total Tickets:* {team['total_tickets']}")
                    st.write(f"*Performance Score:* {team['performance_score']}")
                    st.progress(float(team["resolution_rate"]) / 100)
        else:
            st.warning("No teams available.")
    else:
        st.error("Failed to fetch teams")

elif page == "Agent Metrics":
    st.title("Agent Metrics")
    st.write("View agent performance metrics.")
    
    try:
        metrics_response = requests.get(f"{API_URL}/admin/agent-metrics")
        if metrics_response.ok:
            metrics = metrics_response.json()
            if metrics:
                metrics_df = pd.DataFrame(metrics)
                
                # Display overall metrics
                st.subheader("Performance Overview")
                metrics_df = metrics_df.sort_values(by='tickets_resolved', ascending=False)
                st.dataframe(metrics_df)

                # Visualization options
                chart_type = st.selectbox(
                    "Select Visualization",
                    ["Tickets Resolved", "Average Resolution Time", "Customer Satisfaction"]
                )

                if chart_type == "Tickets Resolved":
                    fig = px.bar(metrics_df, 
                                x="agent_name", 
                                y="tickets_resolved",
                                title="Tickets Resolved by Agent")
                elif chart_type == "Average Resolution Time":
                    fig = px.bar(metrics_df,
                                x="agent_name",
                                y="avg_resolution_time",
                                title="Average Resolution Time (hours)")
                else:
                    fig = px.bar(metrics_df,
                                x="agent_name",
                                y="satisfaction_score",
                                title="Customer Satisfaction Score")
                
                st.plotly_chart(fig)
            else:
                st.warning("No agent metrics available.")
        else:
            st.error("Failed to fetch agent metrics.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to server: {str(e)}")
    except Exception as e:
        st.error(f"Error processing agent metrics: {str(e)}")
