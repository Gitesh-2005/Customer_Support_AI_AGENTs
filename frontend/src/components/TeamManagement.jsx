import { useState, useEffect } from 'react'
import axios from 'axios'
import './TeamManagement.css'

function TeamManagement() {
  const [teams, setTeams] = useState([])
  const [newTeam, setNewTeam] = useState({ name: '', specialty: '' })

  useEffect(() => {
    fetchTeams()
  }, [])

  const fetchTeams = async () => {
    const response = await axios.get('/api/admin/teams')
    setTeams(response.data)
  }

  const handleAddTeam = async (e) => {
    e.preventDefault()
    await axios.post('/api/admin/teams', newTeam)
    fetchTeams()
    setNewTeam({ name: '', specialty: '' })
  }

  return (
    <div className="team-management">
      <div className="team-header">
        <h2>Team Management</h2>
        <form onSubmit={handleAddTeam} className="add-team-form">
          <input
            type="text"
            placeholder="Team Name"
            value={newTeam.name}
            onChange={(e) => setNewTeam({...newTeam, name: e.target.value})}
          />
          <input
            type="text"
            placeholder="Specialty"
            value={newTeam.specialty}
            onChange={(e) => setNewTeam({...newTeam, specialty: e.target.value})}
          />
          <button type="submit">Add Team</button>
        </form>
      </div>

      <div className="teams-grid">
        {teams.map(team => (
          <div key={team.id} className="team-card">
            <h3>{team.name}</h3>
            <p>Specialty: {team.specialty}</p>
            <div className="team-stats">
              <div className="stat">
                <label>Active Tickets</label>
                <span>{team.active_tickets || 0}</span>
              </div>
              <div className="stat">
                <label>Resolution Rate</label>
                <span>{team.resolution_rate || 0}%</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default TeamManagement;
