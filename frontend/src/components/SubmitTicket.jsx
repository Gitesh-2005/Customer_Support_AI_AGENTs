import { useState } from 'react'
import axios from 'axios'
import './SubmitTicket.css'

function SubmitTicket() {
  const [customerName, setCustomerName] = useState('')
  const [issueText, setIssueText] = useState('')
  const [voiceFile, setVoiceFile] = useState(null);
  const [imageFile, setImageFile] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('customer_name', customerName);
      if (issueText) formData.append('issue_text', issueText);
      if (voiceFile) formData.append('voice', voiceFile);
      if (imageFile) formData.append('image', imageFile);

      const response = await axios.post('/api/submit_ticket/', formData);
      alert(response.data.message);
      setCustomerName('');
      setIssueText('');
      setVoiceFile(null);
      setImageFile(null);
    } catch (error) {
      alert('Failed to submit ticket. Please try again.');
    }
  }

  return (
    <form onSubmit={handleSubmit} className="submit-ticket-form">
      <h1 className="submit-ticket-title">Submit a Ticket</h1>
      <div className="form-group">
        <label>Customer Name</label>
        <input
          type="text"
          value={customerName}
          onChange={(e) => setCustomerName(e.target.value)}
          className="form-input"
        />
      </div>
      <div className="form-group">
        <label>Issue</label>
        <textarea
          value={issueText}
          onChange={(e) => setIssueText(e.target.value)}
          className="form-textarea"
        />
      </div>
      <div className="form-group">
        <label>Upload Voice</label>
        <input type="file" accept="audio/*" onChange={(e) => setVoiceFile(e.target.files[0])} />
      </div>
      <div className="form-group">
        <label>Upload Image</label>
        <input type="file" accept="image/*" onChange={(e) => setImageFile(e.target.files[0])} />
      </div>
      <button type="submit" className="submit-button">
        Submit
      </button>
    </form>
  )
}

export default SubmitTicket
