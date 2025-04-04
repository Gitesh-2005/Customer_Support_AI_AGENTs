import { useState, useEffect } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import axios from 'axios';
import './AgentMetrics.css';

function AgentMetrics() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    axios.get('/api/admin/agent-metrics')
      .then(response => setMetrics(response.data))
      .catch(error => console.error('Error fetching metrics:', error));
  }, []);

  const performanceData = {
    labels: metrics?.timeline || [],
    datasets: [
      {
        label: 'Efficiency Score',
        data: metrics?.efficiency_scores || [],
        borderColor: 'rgb(75, 192, 192)',
      },
      {
        label: 'Customer Satisfaction',
        data: metrics?.satisfaction_scores || [],
        borderColor: 'rgb(255, 99, 132)',
      }
    ]
  };

  return (
    <div className="agent-metrics">
      <h2>Agent Performance Metrics</h2>
      <div className="metrics-grid">
        <div className="metric-card">
          <h3>Overall Performance</h3>
          <Line data={performanceData} />
        </div>
        <div className="metric-card">
          <h3>Resolution Times</h3>
          <Bar 
            data={{
              labels: metrics?.agents || [],
              datasets: [{
                label: 'Average Resolution Time (hours)',
                data: metrics?.resolution_times || [],
                backgroundColor: 'rgba(54, 162, 235, 0.5)'
              }]
            }}
          />
        </div>
      </div>
    </div>
  );
}

export default AgentMetrics;
