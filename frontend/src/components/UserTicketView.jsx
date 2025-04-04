import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import './UserTicketView.css'

function UserTicketView() {
  const { id } = useParams()
  const [ticket, setTicket] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`/api/ticket/${id}`)
      .then(response => {
        setTicket(response.data)
        setLoading(false)
      })
      .catch(error => {
        console.error('Error fetching ticket:', error)
        setLoading(false)
      })
  }, [id])

  if (loading) return <div className="loading">Loading...</div>
  if (!ticket) return <div className="error">Ticket not found</div>

  return (
    <div className="ticket-view">
      <h1>Ticket #{ticket.id}</h1>
      <div className="ticket-status">
        Status: <span className={`status-${ticket.status.toLowerCase()}`}>
          {ticket.status}
        </span>
      </div>
      <div className="ticket-info">
        <div className="info-group">
          <h2>Issue Details</h2>
          <p>{ticket.issue_text}</p>
        </div>
        <div className="info-group">
          <h2>AI Analysis</h2>
          <p><strong>Summary:</strong> {ticket.summary}</p>
          <p><strong>Estimated Time:</strong> {ticket.estimated_time}</p>
          <p><strong>Suggested Resolution:</strong> {ticket.resolution}</p>
        </div>
      </div>
    </div>
  )
}

export default UserTicketView
