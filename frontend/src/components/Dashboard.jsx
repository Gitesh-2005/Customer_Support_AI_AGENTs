import { useEffect, useState } from 'react'
import axios from 'axios'
import './Dashboard.css'

function Dashboard() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    console.log('Fetching tickets...')
    axios.get('/api/get_tickets/')
      .then((response) => {
        console.log('Received tickets:', response.data)
        if (response.data && response.data.tickets) {
          setTickets(response.data.tickets)
        } else {
          setError('Invalid response format')
        }
        setLoading(false)
      })
      .catch((error) => {
        console.error("Error details:", error.response || error)
        setError(error.response?.data?.detail || "Failed to fetch tickets.")
        setLoading(false)
      })
  }, [])

  if (loading) return <p>Loading tickets...</p>
  if (error) return <p>{error}</p>

  return (
    <div className="dashboard-container">
      <h1 className="dashboard-title">AI Support Dashboard</h1>
      {tickets.length > 0 ? (
        <div className="tickets-container">
          {tickets.map((ticket) => (
            <div key={ticket.id} className="ticket-card">
              <h2>Ticket #{ticket.id}</h2>
              <div className="ticket-details">
                <p><strong>Customer:</strong> {ticket.customer_name}</p>
                <p><strong>Issue:</strong> {ticket.issue_text}</p>
                <p><strong>Status:</strong> {ticket.status}</p>
                <p><strong>Summary:</strong> {ticket.summary || "N/A"}</p>
                <p><strong>Actions:</strong> {ticket.actions || "N/A"}</p>
                <p><strong>Resolution:</strong> {ticket.resolution || "N/A"}</p>
                <p><strong>Estimated Time:</strong> {ticket.estimated_time || "N/A"}</p>
                <p><strong>Prevention:</strong> {ticket.prevention || "N/A"}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p>No tickets available.</p>
      )}
    </div>
  )
}

export default Dashboard
