import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import AdminLayout from './components/AdminLayout'
import AdminDashboard from './components/AdminDashboard'
import TeamManagement from './components/TeamManagement'
import AgentMetrics from './components/AgentMetrics'
import UserDashboard from './components/UserDashboard'
import UserTicketView from './components/UserTicketView'

function App() {
  const isAdminPort = window.location.port === '5174'

  if (isAdminPort) {
    return (
      <Router>
        <Routes>
          <Route path="/" element={<AdminLayout />}>
            <Route index element={<AdminDashboard />} />
            <Route path="teams" element={<TeamManagement />} />
            <Route path="metrics" element={<AgentMetrics />} />
          </Route>
        </Routes>
      </Router>
    )
  }

  // User routes
  return (
    <Router>
      <Routes>
        <Route path="/" element={<UserDashboard />} />
        <Route path="/ticket/:id" element={<UserTicketView />} />
      </Routes>
    </Router>
  )
}

export default App
