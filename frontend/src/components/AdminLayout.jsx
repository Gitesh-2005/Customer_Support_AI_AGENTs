import { Link, Outlet } from 'react-router-dom'
import './AdminLayout.css'

function AdminLayout() {
  return (
    <div className="admin-layout">
      <nav className="admin-sidebar">
        <div className="admin-logo">
          AI Support Admin
        </div>
        <div className="nav-links">
          <Link to="/" className="nav-item">Dashboard</Link>
          <Link to="/teams" className="nav-item">Team Management</Link>
          <Link to="/metrics" className="nav-item">Performance Metrics</Link>
        </div>
      </nav>
      <main className="admin-content">
        <Outlet />
      </main>
    </div>
  )
}

export default AdminLayout
