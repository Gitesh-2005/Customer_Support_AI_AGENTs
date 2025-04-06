# admin_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API_URL = "http://127.0.0.1:8000"

st.sidebar.title("Admin Navigation")
page = st.sidebar.radio("Go to", ["Admin Dashboard", "Team Management", "Agent Metrics"])

if page == "Admin Dashboard":
    st.title("Dashboard")
    st.write("Overview of tickets and system performance.")
    response = requests.get(f"{API_URL}/get_tickets/")
    if response.ok:
        tickets = response.json().get("tickets", [])
        tickets_df = pd.DataFrame(tickets)
        st.dataframe(tickets_df)
    else:
        st.error("Failed to fetch tickets")

    ticket_id = st.number_input("Enter Ticket ID", min_value=1, step=1)
    if st.button("View Ticket"):
        ticket_response = requests.get(f"{API_URL}/api/ticket/{ticket_id}")
        if ticket_response.ok:
            ticket = ticket_response.json()
            st.write(f"Ticket #{ticket['id']}")
            st.write(f"Customer: {ticket['customer_name']}")
            st.write(f"Issue: {ticket['issue_text']}")
            st.write(f"Status: {ticket['status']}")
            st.write(f"Resolution: {ticket['resolution']}")

            # Display recommended solution and actions
            recommendation = ticket.get('ai_recommendation', {}).get('solution', 'No recommendation available')
            actions = ticket.get('ai_recommendation', {}).get('actions', [])

            st.subheader("Recommended Solution")
            st.write(recommendation)

            st.subheader("Actions to Execute")
            if actions:
                for action in actions:
                    st.write(f"- {action}")
            else:
                st.write("No actions available.")
        else:
            st.error("Ticket not found or error occurred.")
    st.subheader("System Metrics")
    metrics_response = requests.get(f"{API_URL}/admin/metrics")
    if metrics_response.ok:
        metrics = metrics_response.json()
        st.metric("Active Tickets", metrics["active_tickets"])
        st.metric("Resolution Rate", f"{metrics['overall_resolution_rate']}%")
        st.metric("Avg Response Time", f"{metrics['avg_response_time']} mins")
        st.subheader("Performance Trends")
        trends_df = pd.DataFrame({
            "Timeline": metrics["timeline"],
            "Resolution Rate": metrics["resolution_rate"],
            "Customer Satisfaction": metrics["satisfaction"]
        })
        fig = px.line(trends_df, x="Timeline", y=["Resolution Rate", "Customer Satisfaction"], markers=True)
        st.plotly_chart(fig)
    else:
        st.error("Failed to fetch metrics")

elif page == "Team Management":
    st.title("Team Management")
    st.write("Manage teams and their specialties.")
    teams_response = requests.get(f"{API_URL}/admin/teams")
    if teams_response.ok:
        teams = teams_response.json()
        st.subheader("Teams Overview")
        cols = st.columns(3)
        for i, team in enumerate(teams):
            with cols[i % 3]:
                st.markdown(f"### {team['name']}")
                st.write(f"*Specialties:* {', '.join(team['specialties'])}")
                st.write(f"*Resolution Rate:* {team['resolution_rate']}%")
                st.write(f"*Total Tickets:* {team['total_tickets']}")
                st.progress(team["resolution_rate"] / 100)
        st.subheader("Add New Team")
        team_name = st.text_input("Team Name")
        specialties = st.text_area("Specialties (comma-separated)")
        if st.button("Add Team"):
            add_response = requests.post(f"{API_URL}/admin/teams", data={"name": team_name, "specialties": specialties})
            if add_response.ok:
                st.success(add_response.json().get("message", "Team added successfully"))
            else:
                st.error("Failed to add team")
    else:
        st.error("Failed to fetch teams")

elif page == "Agent Metrics":
    st.title("Agent Metrics")
    st.write("View agent performance metrics.")
    metrics_response = requests.get(f"{API_URL}/admin/agent-metrics")
    if metrics_response.ok:
        metrics = metrics_response.json()
        metrics_df = pd.DataFrame(metrics)
        st.dataframe(metrics_df)
        st.subheader("Resolution Times")
        fig = px.bar(metrics_df, x="agent_id", y="avg_resolution_time", title="Average Resolution Time (hours)")
        st.plotly_chart(fig)
    else:
        st.error("Failed to fetch agent metrics")
