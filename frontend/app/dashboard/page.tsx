import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Dashboard — DocGuard",
};

export default function DashboardPage() {
  return (
    <div className="dashboard">
      <div className="toolbar">
        <h1 className="toolbar__title">Dashboard</h1>
      </div>
      <div className="dashboard__grid">
        <div className="dashboard-card">
          <span className="dashboard-card__label">Documents Processed</span>
          <span className="dashboard-card__value">—</span>
          <span className="dashboard-card__sub">Connect backend to see stats</span>
        </div>
        <div className="dashboard-card">
          <span className="dashboard-card__label">Entities Detected</span>
          <span className="dashboard-card__value">—</span>
          <span className="dashboard-card__sub">Requires database connection</span>
        </div>
        <div className="dashboard-card">
          <span className="dashboard-card__label">Risk Distribution</span>
          <span className="dashboard-card__value">—</span>
          <span className="dashboard-card__sub">Coming soon</span>
        </div>
      </div>
      <div className="dashboard__empty">
        <p>Dashboard stats will appear here</p>
        <span>
          The backend tracks processing history in a PostgreSQL database.
          Run the API server with a configured database to populate these metrics.
        </span>
      </div>
    </div>
  );
}
