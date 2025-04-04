import { useState, useEffect } from 'react';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import axios from 'axios';
import './AdminDashboard.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [suggestions, setSuggestions] = useState([]);

  useEffect(() => {
    Promise.all([
      axios.get('/api/admin/metrics'),
      axios.get('/api/admin/teams'),
      axios.get('/api/suggestions')
    ]).then(([metricsRes, teamsRes, suggestionsRes]) => {
      setMetrics(metricsRes.data);
      setTeams(teamsRes.data);
      setSuggestions(suggestionsRes.data.suggestions);
    });
  }, []);

  const performanceData = {
    labels: metrics?.timeline || [],
    datasets: [
      {
        label: 'Resolution Rate',
        data: metrics?.resolution_rate || [],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      },
      {
        label: 'Customer Satisfaction',
        data: metrics?.satisfaction || [],
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1
      }
    ]
  };

  const teamMetrics = {
    labels: teams.map(t => t.name),
    datasets: [{
      data: teams.map(t => t.performance_score),
      backgroundColor: [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
      ]
    }]
  };

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="quick-stats">
          <div className="stat-card">
            <h3>Active Tickets</h3>
            <p>{metrics?.active_tickets || 0}</p>
          </div>
          <div className="stat-card">
            <h3>Resolution Rate</h3>
            <p>{metrics?.overall_resolution_rate || 0}%</p>
          </div>
          <div className="stat-card">
            <h3>Avg Response Time</h3>
            <p>{metrics?.avg_response_time || 0} mins</p>
          </div>
        </div>
      </div>

      <div className="charts-container">
        <div className="chart-card">
          <h2>Performance Trends</h2>
          <Line data={performanceData} />
        </div>
        <div className="chart-card">
          <h2>Team Performance</h2>
          <Pie data={teamMetrics} />
        </div>
      </div>

      <div className="team-management">
        <h2>Team Management</h2>
        <div className="team-list">
          {teams.map(team => (
            <div key={team.id} className="team-card">
              <h3>{team.name}</h3>
              <p>Specialty: {team.specialty}</p>
              <p>Current Load: {team.current_load}%</p>
              <button onClick={() => setSelectedTeam(team)}>
                View Details
              </button>
            </div>
          ))}
        </div>
      </div>

      {selectedTeam && (
        <div className="team-modal">
          <div className="modal-content">
            <h2>{selectedTeam.name} Details</h2>
            <div className="team-stats">
              {/* Team details and metrics */}
            </div>
            <button onClick={() => setSelectedTeam(null)}>Close</button>
          </div>
        </div>
      )}

      <div className="suggestions-section">
        <h2>Suggestions</h2>
        <ul>
          {suggestions.map((suggestion) => (
            <li key={suggestion.ticket_id}>
              Ticket #{suggestion.ticket_id} ({suggestion.customer_name}): {suggestion.suggested_action}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default AdminDashboard;
