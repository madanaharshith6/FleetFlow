import React, { useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./styles.css";

// =========================================================
// API & WEBSOCKET CONFIGURATION
// =========================================================

const API_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://fleetflow-api-p7ai.onrender.com";

const WS_BASE =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "ws://127.0.0.1:8000"
    : "wss://fleetflow-api-p7ai.onrender.com";

const api = axios.create({ baseURL: API_BASE });

// Automatically attach Bearer token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fleetflow_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Automatic 401 handling: log out if token is expired or unauthorized
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem("fleetflow_token");
      localStorage.removeItem("fleetflow_role");
      window.dispatchEvent(new Event("auth_logout"));
    }
    return Promise.reject(error);
  }
);


// =========================================================
// HELPERS & BADGES
// =========================================================

function StatusBadge({ status }) {
  if (!status) return null;
  const clean = status.toLowerCase().replace(/\s+/g, "");
  return (
    <span className={`badge badge-${clean}`}>
      <span className="badge-dot"></span>
      {status}
    </span>
  );
}

function TrafficBadge({ level }) {
  if (!level) return null;
  const clean = level.toLowerCase();
  return (
    <span className={`badge badge-${clean}`}>
      Traffic: {level}
    </span>
  );
}


// =========================================================
// LOGIN COMPONENT (With 4 Role Quick-Fill Buttons)
// =========================================================

function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState("admin@fleetflow.com");
  const [password, setPassword] = useState("Admin@123");
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const demoRoles = [
    { label: "Administrator", email: "admin@fleetflow.com" },
    { label: "Fleet Manager", email: "manager@fleetflow.com" },
    { label: "Dispatcher", email: "dispatcher@fleetflow.com" },
    { label: "Driver", email: "driver@fleetflow.com" }
  ];

  async function handleLogin(e) {
    if (e) e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const res = await api.post("/api/auth/login", { email, password });
      localStorage.setItem("fleetflow_token", res.data.access_token);
      localStorage.setItem("fleetflow_role", res.data.role);
      onLoginSuccess(res.data.role);
    } catch (error) {
      if (!error.response) {
        setErr("Cannot connect to FleetFlow backend server (port 8000). Please ensure the backend is started.");
      } else {
        setErr(error.response?.data?.detail || "Invalid login credentials. Please verify your email and password.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="login-header">
          <div className="login-brand-icon">🚛</div>
          <h1 className="login-title">FleetFlow</h1>
          <p className="login-desc">Fleet Management & Logistics Tracking Platform</p>
        </div>

        {err && <div className="alert alert-error">{err}</div>}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              className="form-input"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin@fleetflow.com"
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              required
            />
          </div>

          <button className="btn btn-primary" style={{ width: "100%", padding: "11px", marginTop: "8px" }} type="submit" disabled={loading}>
            {loading ? "Authenticating..." : "Sign in to Dashboard"}
          </button>
        </form>

        <div className="role-pill-selector">
          <span style={{ fontSize: "11px", fontWeight: "600", color: "#64748b", width: "100%", display: "block" }}>
            Demo Role Quick-Fill (One-Click Testing):
          </span>
          {demoRoles.map((r) => (
            <button
              key={r.label}
              type="button"
              className="quick-role-btn"
              onClick={() => {
                setEmail(r.email);
                setPassword("Admin@123");
              }}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}


// =========================================================
// DASHBOARD COMPONENT (Milestone 1 + Milestone 2 Live KPIs)
// =========================================================

function Dashboard({ setPage, setSelectedShipmentId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  async function loadMetrics() {
    try {
      setLoading(true);
      setErr("");
      const res = await api.get("/api/dashboard/summary");
      setData(res.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to fetch fleet metrics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMetrics();
  }, []);

  if (loading) return <div className="content-panel"><p>Loading FleetFlow operational metrics...</p></div>;
  if (err) return <div className="alert alert-error">{err} <button className="btn btn-secondary btn-sm" onClick={loadMetrics}>Retry</button></div>;
  if (!data) return null;

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Operational Overview</h1>
          <p className="page-subtitle">Real-time fleet monitoring and active shipment dispatch metrics</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadMetrics}>↻ Refresh Data</button>
          <button className="btn btn-primary btn-sm" onClick={() => setPage("live_tracking")}>📡 Open Live Tracking</button>
        </div>
      </div>

      {/* KPI METRIC CARDS */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Total Fleet</span>
            <div className="stat-icon">🚛</div>
          </div>
          <div className="stat-number">{data.total_vehicles}</div>
          <span className="stat-footnote">{data.available_vehicles} available for dispatch</span>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Fleet Utilization</span>
            <div className="stat-icon" style={{ background: "#f0fdf4", color: "#16a34a" }}>📈</div>
          </div>
          <div className="stat-number">{data.fleet_utilization_percent ?? 0}%</div>
          <span className="stat-footnote">{data.active_vehicles} active / {data.total_vehicles} total assets</span>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Active Drivers</span>
            <div className="stat-icon" style={{ background: "#ecfdf5", color: "#059669" }}>👤</div>
          </div>
          <div className="stat-number">{data.active_drivers}</div>
          <span className="stat-footnote">Personnel on duty</span>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Active Shipments</span>
            <div className="stat-icon" style={{ background: "#f5f3ff", color: "#7c3aed" }}>📦</div>
          </div>
          <div className="stat-number">{data.active_shipments}</div>
          <span className="stat-footnote">{data.in_transit_shipments} in active transit</span>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Maintenance</span>
            <div className="stat-icon" style={{ background: "#fff7ed", color: "#ea580c" }}>🔧</div>
          </div>
          <div className="stat-number">{data.total_maintenance ?? 0}</div>
          <span className="stat-footnote">
            {data.overdue_maintenance > 0 ? (
              <span style={{ color: "#ef4444", fontWeight: 700 }}>{data.overdue_maintenance} overdue service(s)</span>
            ) : (
              `${data.scheduled_maintenance ?? 0} scheduled`
            )}
          </span>
        </div>

        <div className="stat-card">
          <div className="stat-header">
            <span className="stat-title">Fuel Consumed</span>
            <div className="stat-icon" style={{ background: "#fef3c7", color: "#d97706" }}>⛽</div>
          </div>
          <div className="stat-number">{(data.total_fuel_consumed_liters ?? 0).toLocaleString()} L</div>
          <span className="stat-footnote">Trip-based powertrain burn</span>
        </div>
      </div>

      {/* PROACTIVE MAINTENANCE & FLEET ALERTS */}
      {data.recent_alerts && data.recent_alerts.length > 0 && (
        <div className="content-panel" style={{ marginBottom: "24px", borderColor: "rgba(245,158,11,0.3)" }}>
          <div className="panel-header">
            <div>
              <h2 className="panel-title" style={{ display: "flex", alignItems: "center", gap: "8px", color: "#f59e0b" }}>
                <span>⚠️</span> Proactive Maintenance & Fleet Alerts
              </h2>
              <p style={{ fontSize: "12px", color: "#64748b" }}>Automated scans detecting upcoming services, high priority interventions, and overdue vehicle maintenance</p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => setPage("maintenance")}>Manage Maintenance Schedule →</button>
          </div>
          <div className="alert-list" style={{ marginTop: "12px" }}>
            {data.recent_alerts.map((al) => (
              <div key={al.id} className={`alert-item alert-${al.severity}`}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span style={{ fontSize: "18px" }}>
                    {al.severity === "critical" ? "🚨" : al.severity === "warning" ? "⚠️" : "ℹ️"}
                  </span>
                  <div>
                    <strong style={{ color: "#f8fafc" }}>
                      {al.vehicle_code} — {al.category}
                    </strong>
                    <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                      Ref #{al.maintenance_id} | Priority: <b>{al.priority}</b> | Scheduled: {al.scheduled_date}
                    </div>
                  </div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span className={`badge ${al.status === "Overdue" ? "badge-overdue" : "badge-scheduled"}`}>
                    {al.status}
                  </span>
                  <button className="btn btn-secondary btn-sm" onClick={() => setPage("maintenance")}>
                    Resolve
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* RECENT OPERATIONAL FEED */}
      <div className="content-panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title">Active Logistics Feed</h2>
            <p style={{ fontSize: "12px", color: "#64748b" }}>Live telemetry and status updates from the transit network</p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => setPage("shipments")}>View All Shipments →</button>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tracking #</th>
                <th>Shipment ID</th>
                <th>Transit Route</th>
                <th>Status</th>
                <th>Assigned Vehicle</th>
                <th>Driver</th>
                <th>ETA</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_shipments && data.recent_shipments.length > 0 ? (
                data.recent_shipments.map((s) => (
                  <tr key={s.id}>
                    <td><span className="code-font">{s.tracking_number}</span></td>
                    <td><strong>{s.shipment_id}</strong></td>
                    <td>{s.origin} → {s.destination}</td>
                    <td><StatusBadge status={s.status} /></td>
                    <td>{s.vehicle_id}</td>
                    <td>{s.driver_name}</td>
                    <td>{s.eta}</td>
                    <td>
                      <button
                        className="btn btn-primary btn-sm"
                        onClick={() => {
                          setSelectedShipmentId(s.shipment_id);
                          setPage("live_tracking");
                        }}
                      >
                        Track 📡
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", color: "#64748b" }}>
                    No shipments currently recorded.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}


// =========================================================
// VEHICLES MANAGEMENT (Milestone 1 Enhanced)
// =========================================================

function Vehicles({ userRole }) {
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("All");
  const [form, setForm] = useState({
    vehicle_id: "",
    registration_number: "",
    vehicle_type: "Truck",
    capacity: "15",
    fuel_type: "Diesel",
    current_status: "Available",
    driver_id: ""
  });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [vehicleHistory, setVehicleHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  const canWrite = userRole === "Administrator" || userRole === "Fleet Manager";

  async function handleOpenHistory(veh) {
    setSelectedVehicle(veh);
    setHistoryLoading(true);
    setShowHistoryModal(true);
    try {
      const res = await api.get(`/api/maintenance/vehicle/${veh.id}/history`);
      setVehicleHistory(res.data);
    } catch (e) {
      setVehicleHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  async function loadData() {
    try {
      const [vRes, dRes] = await Promise.all([api.get("/api/vehicles"), api.get("/api/drivers")]);
      setVehicles(vRes.data);
      setDrivers(dRes.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to load vehicle fleet.");
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAddVehicle(e) {
    e.preventDefault();
    setMsg("");
    setErr("");

    try {
      await api.post("/api/vehicles", {
        vehicle_id: form.vehicle_id.trim(),
        registration_number: form.registration_number.trim(),
        vehicle_type: form.vehicle_type,
        capacity: Number(form.capacity),
        fuel_type: form.fuel_type,
        current_status: form.current_status,
        driver_id: form.driver_id ? Number(form.driver_id) : null
      });

      setMsg("Vehicle registered successfully.");
      setForm({
        vehicle_id: "",
        registration_number: "",
        vehicle_type: "Truck",
        capacity: "15",
        fuel_type: "Diesel",
        current_status: "Available",
        driver_id: ""
      });
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to register vehicle.");
    }
  }

  async function toggleStatus(vehicle, newStatus) {
    try {
      await api.put(`/api/vehicles/${vehicle.id}/status`, {
        current_status: newStatus,
        driver_id: vehicle.driver_id
      });
      loadData();
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to update status.");
    }
  }

  const filteredVehicles = vehicles.filter((v) => {
    const matchesSearch =
      v.vehicle_id.toLowerCase().includes(search.toLowerCase()) ||
      v.registration_number.toLowerCase().includes(search.toLowerCase());
    const matchesType = typeFilter === "All" || v.vehicle_type === typeFilter;
    return matchesSearch && matchesType;
  });

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Fleet Management</h1>
          <p className="page-subtitle">Register and monitor commercial transit vehicles and assigned operators</p>
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      <div style={{ display: "grid", gridTemplateColumns: canWrite ? "360px 1fr" : "1fr", gap: "24px" }}>
        {canWrite && (
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Register Vehicle</h2>
            <form onSubmit={handleAddVehicle}>
              <div className="form-group">
                <label className="form-label">Vehicle ID</label>
                <input
                  className="form-input"
                  placeholder="e.g. VH-003"
                  value={form.vehicle_id}
                  onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Registration Number</label>
                <input
                  className="form-input"
                  placeholder="e.g. AP39CQ5678"
                  value={form.registration_number}
                  onChange={(e) => setForm({ ...form, registration_number: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Vehicle Category</label>
                <select
                  className="form-select"
                  value={form.vehicle_type}
                  onChange={(e) => setForm({ ...form, vehicle_type: e.target.value })}
                >
                  <option>Truck</option>
                  <option>Van</option>
                  <option>Container Truck</option>
                  <option>Car</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Cargo Capacity (Tons)</label>
                <input
                  className="form-input"
                  type="number"
                  min="0.5"
                  step="0.5"
                  value={form.capacity}
                  onChange={(e) => setForm({ ...form, capacity: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Fuel Type</label>
                <select
                  className="form-select"
                  value={form.fuel_type}
                  onChange={(e) => setForm({ ...form, fuel_type: e.target.value })}
                >
                  <option>Diesel</option>
                  <option>Petrol</option>
                  <option>CNG</option>
                  <option>Electric</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Initial Status</label>
                <select
                  className="form-select"
                  value={form.current_status}
                  onChange={(e) => setForm({ ...form, current_status: e.target.value })}
                >
                  <option>Available</option>
                  <option>Active</option>
                  <option>Maintenance</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Assign Driver (Optional)</label>
                <select
                  className="form-select"
                  value={form.driver_id}
                  onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                >
                  <option value="">No Driver Assigned</option>
                  {drivers.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name} ({d.driver_id})
                    </option>
                  ))}
                </select>
              </div>

              <button className="btn btn-primary" style={{ width: "100%", marginTop: "8px" }} type="submit">
                Register Vehicle
              </button>
            </form>
          </div>
        )}

        <div className="content-panel">
          <div className="panel-header">
            <h2 className="panel-title">Fleet Vehicles ({filteredVehicles.length})</h2>
            <div className="filter-bar">
              <input
                className="search-input"
                placeholder="Search vehicle or registration..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select className="select-filter" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
                <option value="All">All Types</option>
                <option value="Truck">Truck</option>
                <option value="Van">Van</option>
                <option value="Container Truck">Container Truck</option>
                <option value="Car">Car</option>
              </select>
              <button className="btn btn-secondary btn-sm" onClick={loadData}>↻ Refresh</button>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Vehicle ID</th>
                  <th>Registration</th>
                  <th>Type</th>
                  <th>Capacity</th>
                  <th>Fuel</th>
                  <th>Assigned Driver</th>
                  <th>Status</th>
                  <th>Service History</th>
                  {canWrite && <th>Quick Action</th>}
                </tr>
              </thead>
              <tbody>
                {filteredVehicles.map((v) => (
                  <tr key={v.id}>
                    <td><span className="code-font">{v.vehicle_id}</span></td>
                    <td><strong>{v.registration_number}</strong></td>
                    <td>{v.vehicle_type}</td>
                    <td>{v.capacity} Tons</td>
                    <td>{v.fuel_type}</td>
                    <td>{v.driver_name ? <span style={{ color: "#0284c7", fontWeight: 600 }}>{v.driver_name}</span> : <span style={{ color: "#94a3b8" }}>None</span>}</td>
                    <td><StatusBadge status={v.current_status} /></td>
                    <td>
                      <button
                        className="btn btn-secondary btn-sm"
                        style={{ padding: "4px 8px", fontSize: "11px" }}
                        onClick={() => handleOpenHistory(v)}
                      >
                        History 🛠️
                      </button>
                    </td>
                    {canWrite && (
                      <td>
                        <select
                          className="select-filter"
                          style={{ padding: "4px 8px", fontSize: "11px" }}
                          value={v.current_status}
                          onChange={(e) => toggleStatus(v, e.target.value)}
                        >
                          <option value="Available">Set Available</option>
                          <option value="Active">Set Active</option>
                          <option value="Maintenance">Set Maintenance</option>
                        </select>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* VEHICLE SERVICE HISTORY MODAL */}
      {showHistoryModal && selectedVehicle && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: "680px" }}>
            <div className="modal-header">
              <h3 className="modal-title">
                Service History — {selectedVehicle.vehicle_id} ({selectedVehicle.registration_number})
              </h3>
              <button className="modal-close" onClick={() => setShowHistoryModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              {historyLoading ? (
                <p>Loading vehicle service logs...</p>
              ) : vehicleHistory.length === 0 ? (
                <div style={{ textAlign: "center", padding: "24px", color: "#64748b" }}>
                  No maintenance records or service logs registered for this vehicle yet.
                </div>
              ) : (
                <div className="table-responsive">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Event Type</th>
                        <th>Status Transition</th>
                        <th>Logged Cost</th>
                        <th>Operational Notes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {vehicleHistory.map((h) => (
                        <tr key={h.id}>
                          <td>{new Date(h.created_at).toLocaleDateString()}</td>
                          <td><strong>{h.event_type}</strong></td>
                          <td>
                            {h.previous_status ? `${h.previous_status} → ` : ""}
                            <b>{h.new_status}</b>
                          </td>
                          <td>{h.cost ? `₹${h.cost.toLocaleString()}` : "—"}</td>
                          <td><span style={{ fontSize: "12px", color: "#94a3b8" }}>{h.notes || "—"}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowHistoryModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}


// =========================================================
// DRIVERS MANAGEMENT (Milestone 1 Enhanced)
// =========================================================

function Drivers({ userRole }) {
  const [drivers, setDrivers] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({
    driver_id: "",
    name: "",
    license_number: "",
    phone: ""
  });
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [assignVehicleId, setAssignVehicleId] = useState("");

  const canWrite = userRole === "Administrator" || userRole === "Fleet Manager" || userRole === "Dispatcher";

  async function loadData() {
    try {
      const [dRes, vRes] = await Promise.all([
        api.get("/api/drivers/monitoring"),
        api.get("/api/vehicles")
      ]);
      setDrivers(dRes.data);
      setVehicles(vRes.data);
    } catch (e) {
      // Fallback to basic drivers if monitoring endpoint fails
      try {
        const res = await api.get("/api/drivers");
        setDrivers(res.data);
      } catch (err2) {
        setErr("Unable to load drivers list.");
      }
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleAddDriver(e) {
    e.preventDefault();
    setMsg("");
    setErr("");

    try {
      await api.post("/api/drivers", {
        driver_id: form.driver_id.trim(),
        name: form.name.trim(),
        license_number: form.license_number.trim(),
        phone: form.phone.trim()
      });

      setMsg("Driver registered successfully in database.");
      setForm({ driver_id: "", name: "", license_number: "", phone: "" });
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to register driver.");
    }
  }

  async function handleAssignVehicle(e) {
    e.preventDefault();
    if (!selectedDriver || !assignVehicleId) return;
    setMsg("");
    setErr("");
    try {
      const res = await api.post(`/api/drivers/${selectedDriver.id}/assign-vehicle`, {
        vehicle_id: parseInt(assignVehicleId)
      });
      setMsg(res.data.message || "Vehicle assigned successfully.");
      setShowAssignModal(false);
      setSelectedDriver(null);
      setAssignVehicleId("");
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Vehicle assignment failed.");
    }
  }

  async function handleUnassignVehicle(driverId) {
    setMsg("");
    setErr("");
    try {
      const res = await api.post(`/api/drivers/${driverId}/unassign-vehicle`);
      setMsg(res.data.message || "Vehicle unassigned.");
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to unassign vehicle.");
    }
  }

  const filtered = drivers.filter(
    (d) =>
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.driver_id.toLowerCase().includes(search.toLowerCase()) ||
      d.phone.includes(search)
  );

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Driver Personnel & Asset Assignment</h1>
          <p className="page-subtitle">Track certified driver roster, compliance, attendance, operational dispatch, and vehicle pairing</p>
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      <div style={{ display: "grid", gridTemplateColumns: canWrite ? "360px 1fr" : "1fr", gap: "24px" }}>
        {canWrite && (
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Register Driver</h2>
            <form onSubmit={handleAddDriver}>
              <div className="form-group">
                <label className="form-label">Driver ID</label>
                <input
                  className="form-input"
                  placeholder="e.g. DR-102"
                  value={form.driver_id}
                  onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Full Name</label>
                <input
                  className="form-input"
                  placeholder="e.g. Ramesh Kumar"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Commercial License Number</label>
                <input
                  className="form-input"
                  placeholder="e.g. AP1620210045"
                  value={form.license_number}
                  onChange={(e) => setForm({ ...form, license_number: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone Contact</label>
                <input
                  className="form-input"
                  placeholder="e.g. 9876543210"
                  value={form.phone}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  required
                />
              </div>

              <button className="btn btn-primary" style={{ width: "100%", marginTop: "8px" }} type="submit">
                Register Driver
              </button>
            </form>
          </div>
        )}

        <div className="content-panel">
          <div className="panel-header">
            <h2 className="panel-title">Active Roster & Operational Monitoring ({filtered.length})</h2>
            <div className="filter-bar">
              <input
                className="search-input"
                placeholder="Search driver by name, ID, or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <button className="btn btn-secondary btn-sm" onClick={loadData}>↻ Refresh</button>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Driver ID</th>
                  <th>Name</th>
                  <th>Contact</th>
                  <th>Assigned Vehicle</th>
                  <th>Attendance</th>
                  <th>Performance</th>
                  <th>Live Status</th>
                  {canWrite && <th>Assignment Actions</th>}
                </tr>
              </thead>
              <tbody>
                {filtered.map((d) => (
                  <tr key={d.id}>
                    <td><span className="code-font">{d.driver_id}</span></td>
                    <td>
                      <strong>{d.name}</strong>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>Lic: {d.license_number}</div>
                    </td>
                    <td>{d.phone}</td>
                    <td>
                      {d.assigned_vehicle_code || d.assigned_vehicle ? (
                        <div>
                          <strong style={{ color: "#38bdf8" }}>{d.assigned_vehicle_code || d.assigned_vehicle}</strong>
                          {d.assigned_registration && (
                            <div style={{ fontSize: "11px", color: "#94a3b8" }}>{d.assigned_registration}</div>
                          )}
                        </div>
                      ) : (
                        <span style={{ color: "#94a3b8" }}>Unassigned</span>
                      )}
                    </td>
                    <td><span style={{ fontWeight: 600, color: "#059669" }}>{d.attendance}%</span></td>
                    <td>★ {d.performance > 0 ? d.performance.toFixed(1) : "5.0"}</td>
                    <td>
                      <span className={`badge ${d.status_label === "On Trip" ? "badge-transit" : (d.status_label === "Assigned" ? "badge-scheduled" : "badge-available")}`}>
                        {d.status_label || (d.is_active ? "Available" : "Inactive")}
                      </span>
                    </td>
                    {canWrite && (
                      <td>
                        <div style={{ display: "flex", gap: "6px" }}>
                          <button
                            className="btn btn-secondary btn-sm"
                            style={{ padding: "4px 8px", fontSize: "11px" }}
                            onClick={() => {
                              setSelectedDriver(d);
                              setAssignVehicleId(d.assigned_vehicle_id ? String(d.assigned_vehicle_id) : (vehicles[0]?.id ? String(vehicles[0].id) : ""));
                              setShowAssignModal(true);
                            }}
                          >
                            {d.assigned_vehicle_code || d.assigned_vehicle ? "Reassign ⇄" : "Assign 🚛"}
                          </button>
                          {(d.assigned_vehicle_code || d.assigned_vehicle) && (
                            <button
                              className="btn btn-danger btn-sm"
                              style={{ padding: "4px 8px", fontSize: "11px" }}
                              onClick={() => handleUnassignVehicle(d.id)}
                            >
                              Release
                            </button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ASSIGN VEHICLE MODAL */}
      {showAssignModal && selectedDriver && (
        <div className="modal-overlay">
          <div className="modal-card" style={{ maxWidth: "480px" }}>
            <div className="modal-header">
              <h3 className="modal-title">Assign Vehicle to Driver</h3>
              <button className="modal-close" onClick={() => setShowAssignModal(false)}>✕</button>
            </div>
            <form onSubmit={handleAssignVehicle}>
              <div className="modal-body">
                <p style={{ fontSize: "13px", color: "#94a3b8", marginBottom: "16px" }}>
                  Pair certified operator <strong>{selectedDriver.name}</strong> ({selectedDriver.driver_id}) with an active commercial transit asset.
                </p>

                <div className="form-group">
                  <label className="form-label">Select Commercial Vehicle *</label>
                  <select
                    className="form-select"
                    value={assignVehicleId}
                    onChange={(e) => setAssignVehicleId(e.target.value)}
                    required
                  >
                    <option value="">-- Choose Fleet Vehicle --</option>
                    {vehicles.map((v) => {
                      const isMaint = v.current_status === "Maintenance";
                      return (
                        <option key={v.id} value={v.id} disabled={isMaint}>
                          {v.vehicle_id} ({v.registration_number}) - {v.vehicle_type} [{v.current_status}]{isMaint ? " (MAINTENANCE - LOCKED)" : ""}
                        </option>
                      );
                    })}
                  </select>
                </div>

                <div className="methodology-box" style={{ marginTop: "12px" }}>
                  <strong>Safety Rule:</strong> Vehicles currently tagged in <code>Maintenance</code> status cannot be dispatched or assigned to drivers until inspection sign-off.
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowAssignModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={!assignVehicleId}>Confirm Assignment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}


// =========================================================
// SHIPMENTS MODULE (Milestone 2 Core)
// =========================================================

function Shipments({ setPage, setSelectedShipmentId, userRole }) {
  const [shipments, setShipments] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [historyModalShipment, setHistoryModalShipment] = useState(null);
  const [historyEvents, setHistoryEvents] = useState([]);
  const [statusModalShipment, setStatusModalShipment] = useState(null);
  const [newStatusVal, setNewStatusVal] = useState("");

  const [form, setForm] = useState({
    shipment_id: "",
    tracking_number: "",
    origin: "Vijayawada",
    destination: "Hyderabad",
    customer_name: "Acme Logistics",
    customer_phone: "+91 98765 43210",
    description: "General cargo consignment",
    vehicle_id: "",
    driver_id: "",
    route_type: "Fastest Route",
    traffic_level: "Moderate"
  });

  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const canCreate = userRole === "Administrator" || userRole === "Fleet Manager" || userRole === "Dispatcher";

  async function loadAll() {
    try {
      const [sRes, vRes, dRes] = await Promise.all([
        api.get("/api/shipments"),
        api.get("/api/vehicles"),
        api.get("/api/drivers")
      ]);
      setShipments(sRes.data);
      setVehicles(vRes.data);
      setDrivers(dRes.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to load shipments.");
    }
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function handleCreateShipment(e) {
    e.preventDefault();
    setMsg("");
    setErr("");

    try {
      const payload = {
        origin: form.origin.trim(),
        destination: form.destination.trim(),
        customer_name: form.customer_name.trim(),
        customer_phone: form.customer_phone.trim(),
        description: form.description.trim(),
        vehicle_id: form.vehicle_id ? Number(form.vehicle_id) : null,
        driver_id: form.driver_id ? Number(form.driver_id) : null,
        route_type: form.route_type,
        traffic_level: form.traffic_level
      };
      if (form.shipment_id && form.shipment_id.trim()) {
        payload.shipment_id = form.shipment_id.trim();
      }
      if (form.tracking_number && form.tracking_number.trim()) {
        payload.tracking_number = form.tracking_number.trim();
      }

      const res = await api.post("/api/shipments", payload);

      setMsg(`Shipment ${res.data.shipment_id} created successfully with tracking #${res.data.tracking_number}.`);
      setShowCreateModal(false);
      setForm({
        shipment_id: "",
        tracking_number: "",
        origin: "Vijayawada",
        destination: "Hyderabad",
        customer_name: "Acme Logistics",
        customer_phone: "+91 98765 43210",
        description: "General cargo consignment",
        vehicle_id: "",
        driver_id: "",
        route_type: "Fastest Route",
        traffic_level: "Moderate"
      });
      loadAll();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to create shipment.");
    }
  }

  async function openHistory(s) {
    setHistoryModalShipment(s);
    try {
      const res = await api.get(`/api/shipments/${s.shipment_id}/history`);
      setHistoryEvents(res.data);
    } catch (e) {
      setHistoryEvents([]);
    }
  }

  async function handleUpdateStatus(e) {
    e.preventDefault();
    if (!statusModalShipment || !newStatusVal) return;

    try {
      await api.put(`/api/shipments/${statusModalShipment.shipment_id}/status`, {
        status: newStatusVal,
        description: `Status changed to ${newStatusVal} via dispatcher console.`
      });
      setStatusModalShipment(null);
      setMsg(`Shipment status updated to ${newStatusVal}.`);
      loadAll();
    } catch (error) {
      setErr(error.response?.data?.detail || "Invalid status transition.");
    }
  }

  const filteredShipments = shipments.filter((s) => {
    const term = search.toLowerCase();
    const matchesSearch =
      s.shipment_id.toLowerCase().includes(term) ||
      s.tracking_number.toLowerCase().includes(term) ||
      s.customer_name.toLowerCase().includes(term) ||
      s.origin.toLowerCase().includes(term) ||
      s.destination.toLowerCase().includes(term);

    const matchesStatus = statusFilter === "All" || s.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Shipment Management</h1>
          <p className="page-subtitle">Track, dispatch, and manage end-to-end commercial freight consignments</p>
        </div>
        <div className="header-actions">
          {canCreate && (
            <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
              + Create Shipment
            </button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={loadAll}>↻ Refresh</button>
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      <div className="content-panel">
        <div className="panel-header">
          <h2 className="panel-title">Active Consignments ({filteredShipments.length})</h2>
          <div className="filter-bar">
            <input
              className="search-input"
              placeholder="Search tracking #, customer, origin, or destination..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select className="select-filter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="All">All Statuses</option>
              <option value="Created">Created</option>
              <option value="Assigned">Assigned</option>
              <option value="In Transit">In Transit</option>
              <option value="Delayed">Delayed</option>
              <option value="Delivered">Delivered</option>
              <option value="Cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Tracking #</th>
                <th>Shipment ID</th>
                <th>Route Corridor</th>
                <th>Customer</th>
                <th>Vehicle & Driver</th>
                <th>Status</th>
                <th>ETA</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredShipments.length > 0 ? (
                filteredShipments.map((s) => (
                  <tr key={s.id}>
                    <td><span className="code-font">{s.tracking_number}</span></td>
                    <td><strong>{s.shipment_id}</strong></td>
                    <td>{s.origin} → {s.destination}</td>
                    <td>{s.customer_name}</td>
                    <td>
                      <div>
                        {s.vehicle_info ? <span>🚛 {s.vehicle_info.vehicle_id}</span> : <span style={{ color: "#94a3b8" }}>No vehicle</span>}
                      </div>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>
                        {s.driver_info ? `👤 ${s.driver_info.name}` : "No driver"}
                      </div>
                    </td>
                    <td><StatusBadge status={s.status} /></td>
                    <td>{s.estimated_duration || "TBD"}</td>
                    <td>
                      <div style={{ display: "flex", gap: "6px" }}>
                        <button
                          className="btn btn-primary btn-sm"
                          title="Open Live Telemetry & GPS Tracking"
                          onClick={() => {
                            setSelectedShipmentId(s.shipment_id);
                            setPage("live_tracking");
                          }}
                        >
                          Track 📡
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="View Event Audit History"
                          onClick={() => openHistory(s)}
                        >
                          History 📜
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="Transition Status"
                          onClick={() => {
                            setStatusModalShipment(s);
                            setNewStatusVal(s.status);
                          }}
                        >
                          Status ⚙
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="8" style={{ textAlign: "center", padding: "32px", color: "#64748b" }}>
                    No shipments match the current filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* CREATE SHIPMENT MODAL */}
      {showCreateModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">New Freight Shipment</h3>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateShipment}>
              <div className="modal-body">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Shipment ID (Optional)</label>
                    <input
                      className="form-input"
                      value={form.shipment_id}
                      onChange={(e) => setForm({ ...form, shipment_id: e.target.value })}
                      placeholder="Auto-generated if empty"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Tracking Number (Optional)</label>
                    <input
                      className="form-input"
                      value={form.tracking_number}
                      onChange={(e) => setForm({ ...form, tracking_number: e.target.value })}
                      placeholder="Auto-generated if empty"
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Origin Hub</label>
                    <input
                      className="form-input"
                      value={form.origin}
                      onChange={(e) => setForm({ ...form, origin: e.target.value })}
                      placeholder="e.g. Vijayawada"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Destination Hub</label>
                    <input
                      className="form-input"
                      value={form.destination}
                      onChange={(e) => setForm({ ...form, destination: e.target.value })}
                      placeholder="e.g. Hyderabad"
                      required
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Customer / Client Name</label>
                    <input
                      className="form-input"
                      value={form.customer_name}
                      onChange={(e) => setForm({ ...form, customer_name: e.target.value })}
                      placeholder="e.g. Vizag Steel Ltd"
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Customer Phone</label>
                    <input
                      className="form-input"
                      value={form.customer_phone}
                      onChange={(e) => setForm({ ...form, customer_phone: e.target.value })}
                      placeholder="+91 98765 43210"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Cargo Description</label>
                  <input
                    className="form-input"
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    placeholder="e.g. Heavy electronics and components"
                  />
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Assign Vehicle</label>
                    <select
                      className="form-select"
                      value={form.vehicle_id}
                      onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}
                    >
                      <option value="">Select Fleet Vehicle</option>
                      {vehicles.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.vehicle_id} - {v.vehicle_type} ({v.current_status})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Assign Driver</label>
                    <select
                      className="form-select"
                      value={form.driver_id}
                      onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                    >
                      <option value="">Select Driver</option>
                      {drivers.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.driver_id})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Routing Strategy</label>
                    <select
                      className="form-select"
                      value={form.route_type}
                      onChange={(e) => setForm({ ...form, route_type: e.target.value })}
                    >
                      <option>Fastest Route</option>
                      <option>Shortest Route</option>
                      <option>Traffic Avoidance</option>
                      <option>Fuel Efficient Route</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Traffic Expectation</label>
                    <select
                      className="form-select"
                      value={form.traffic_level}
                      onChange={(e) => setForm({ ...form, traffic_level: e.target.value })}
                    >
                      <option>Low</option>
                      <option>Moderate</option>
                      <option>High</option>
                      <option>Severe</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Dispatch Shipment</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SHIPMENT AUDIT HISTORY MODAL */}
      {historyModalShipment && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Event Audit Trail</h3>
                <p style={{ fontSize: "12px", color: "#64748b" }}>
                  Shipment: <strong>{historyModalShipment.shipment_id}</strong> | Tracking: <span className="code-font">{historyModalShipment.tracking_number}</span> | Corridor: {historyModalShipment.origin} → {historyModalShipment.destination}
                </p>
              </div>
              <button className="modal-close" onClick={() => setHistoryModalShipment(null)}>✕</button>
            </div>
            <div className="modal-body">
              {historyEvents.length > 0 ? (
                <div className="timeline">
                  {historyEvents.map((evt) => (
                    <div key={evt.id} className="timeline-item">
                      <div className="timeline-time">{new Date(evt.created_at).toLocaleString()}</div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", margin: "2px 0 4px 0" }}>
                        <span className="timeline-title">{evt.event_type}</span>
                        {(evt.previous_status || evt.new_status) && (
                          <span style={{ fontSize: "11px", fontWeight: 600, color: "#4f46e5" }}>
                            ({evt.previous_status || "Created"} ➔ {evt.new_status || evt.status})
                          </span>
                        )}
                      </div>
                      <div className="timeline-desc">{evt.description}</div>
                      {evt.latitude && evt.longitude && (
                        <div style={{ fontSize: "11px", color: "#0284c7", marginTop: "4px" }}>
                          📍 Lat: {evt.latitude}, Lon: {evt.longitude} ({evt.current_location})
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "#64748b", textAlign: "center" }}>No event history recorded yet.</p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setHistoryModalShipment(null)}>Close</button>
            </div>
          </div>
        </div>
      )}

      {/* UPDATE STATUS MODAL */}
      {statusModalShipment && (() => {
        const allowedTransitionsMap = {
          "Created": ["Assigned", "In Transit", "Cancelled"],
          "Assigned": ["In Transit", "Delayed", "Created", "Cancelled"],
          "In Transit": ["Delayed", "Delivered", "Cancelled"],
          "Delayed": ["In Transit", "Delivered", "Cancelled"],
          "Delivered": [],
          "Cancelled": []
        };
        const allowedNext = allowedTransitionsMap[statusModalShipment.status] || [];
        const isTerminal = allowedNext.length === 0;

        return (
          <div className="modal-backdrop">
            <div className="modal-card" style={{ maxWidth: "450px" }}>
              <div className="modal-header">
                <div>
                  <h3 className="modal-title">Update Shipment Status</h3>
                  <p style={{ fontSize: "12px", color: "#64748b" }}>
                    {statusModalShipment.shipment_id} (Tracking: {statusModalShipment.tracking_number})
                  </p>
                </div>
                <button className="modal-close" onClick={() => setStatusModalShipment(null)}>✕</button>
              </div>
              <form onSubmit={handleUpdateStatus}>
                <div className="modal-body">
                  <p style={{ fontSize: "13px", color: "#64748b", marginBottom: "14px" }}>
                    Current Status: <StatusBadge status={statusModalShipment.status} />
                  </p>

                  {isTerminal ? (
                    <div className="alert alert-info" style={{ fontSize: "12px" }}>
                      This shipment has reached terminal state (<strong>{statusModalShipment.status}</strong>) and cannot transition further.
                    </div>
                  ) : (
                    <div className="form-group">
                      <label className="form-label">Next Operational Status</label>
                      <select
                        className="form-select"
                        value={newStatusVal}
                        onChange={(e) => setNewStatusVal(e.target.value)}
                        required
                      >
                        <option value="">Select next status</option>
                        {allowedNext.map((st) => (
                          <option key={st} value={st}>{st}</option>
                        ))}
                      </select>
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setStatusModalShipment(null)}>Cancel</button>
                  <button type="submit" className="btn btn-primary" disabled={isTerminal || !newStatusVal}>
                    Save Transition
                  </button>
                </div>
              </form>
            </div>
          </div>
        );
      })()}
    </section>
  );
}


// =========================================================
// =========================================================
// LIVE TRACKING MODULE (Leaflet Map + WebSocket + Simulation)
// =========================================================

function LiveTracking({ shipmentId, userRole }) {
  const [shipments, setShipments] = useState([]);
  const [activeShipmentId, setActiveShipmentId] = useState(shipmentId || "");
  const [telemetry, setTelemetry] = useState(null);
  const [wsStatus, setWsStatus] = useState("Connecting...");
  const [simulating, setSimulating] = useState(false);
  const [trafficSelect, setTrafficSelect] = useState("Moderate");
  const [recalculating, setRecalculating] = useState(false);
  const [showLiveHistoryModal, setShowLiveHistoryModal] = useState(false);
  const [liveHistoryEvents, setLiveHistoryEvents] = useState([]);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const mapRef = useRef(null);
  const leafletMap = useRef(null);
  const vehicleMarker = useRef(null);
  const routeLine = useRef(null);
  const originMarker = useRef(null);
  const destMarker = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimeout = useRef(null);

  // Load available shipments
  async function loadShipmentsList() {
    try {
      const res = await api.get("/api/shipments");
      setShipments(res.data);
      if (!activeShipmentId && res.data.length > 0) {
        setActiveShipmentId(res.data[0].shipment_id);
      }
    } catch (e) {
      setErr("Unable to load shipments list.");
    }
  }

  useEffect(() => {
    loadShipmentsList();
  }, []);

  // Fetch telemetry for current shipment
  async function fetchTelemetry(sid) {
    if (!sid) return;
    try {
      const res = await api.get(`/api/tracking/${sid}`);
      setTelemetry(res.data);
      if (res.data.traffic_level) {
        setTrafficSelect(res.data.traffic_level);
      }
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to fetch live telemetry.");
    }
  }

  // Active shipment change handler
  useEffect(() => {
    if (activeShipmentId) {
      fetchTelemetry(activeShipmentId);
      connectWebSocket(activeShipmentId);
    }
    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    };
  }, [activeShipmentId]);

  // WebSocket connection management with auto-reconnect
  function connectWebSocket(sid) {
    if (wsRef.current) {
      wsRef.current.close();
    }
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }

    try {
      setWsStatus("Connecting...");
      const wsUrl = `${WS_BASE}/ws/shipments/${sid}`;
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setWsStatus("Connected");
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "location_updated") {
            setTelemetry((prev) => ({
              ...prev,
              latitude: data.latitude,
              longitude: data.longitude,
              progress: data.progress,
              current_location: data.location_name,
              remaining_km: data.remaining_km,
              eta: data.eta,
              status: data.status,
              gps_status: data.gps_status || "Simulated GPS: Active Corridor"
            }));
          } else if (data.type === "status_changed") {
            setTelemetry((prev) => ({ ...prev, status: data.status, eta: data.eta }));
          } else if (data.type === "route_recalculated") {
            setTelemetry((prev) => ({
              ...prev,
              traffic_level: data.traffic_level,
              route_type: data.route_type,
              estimated_duration: data.estimated_duration,
              eta: data.eta,
              remaining_km: data.remaining_km,
              progress: data.progress
            }));
          }
        } catch (ex) {}
      };

      socket.onerror = () => {
        setWsStatus("Disconnected");
      };

      socket.onclose = () => {
        setWsStatus("Disconnected");
        reconnectTimeout.current = setTimeout(() => {
          if (activeShipmentId === sid) {
            connectWebSocket(sid);
          }
        }, 3000);
      };
    } catch (ex) {
      setWsStatus("Disconnected");
    }
  }

  // City geocoding helper for map endpoints
  const cityCoords = {
    vijayawada: [16.5062, 80.6480],
    guntur: [16.3067, 80.4365],
    hyderabad: [17.3850, 78.4867],
    visakhapatnam: [17.6868, 83.2185],
    vizag: [17.6868, 83.2185],
    bengaluru: [12.9716, 77.5946],
    chennai: [13.0827, 80.2707]
  };

  function getCoords(name) {
    if (!name) return [16.5, 80.6];
    const key = name.toLowerCase().trim();
    for (const [k, v] of Object.entries(cityCoords)) {
      if (key.includes(k)) return v;
    }
    return [16.5, 80.6];
  }

  // Initialize or Update Leaflet Map when telemetry is ready
  useEffect(() => {
    if (!telemetry || !mapRef.current) return;

    function renderMap() {
      if (!window.L || !mapRef.current) return;

      const L = window.L;
      const vLat = telemetry.latitude || 16.5;
      const vLon = telemetry.longitude || 80.6;
      const origCoords = getCoords(telemetry.origin);
      const destCoords = getCoords(telemetry.destination);

      // Initialize map once
      if (!leafletMap.current) {
        if (mapRef.current._leaflet_id) {
          mapRef.current._leaflet_id = null;
        }

        const map = L.map(mapRef.current, {
          center: [vLat, vLon],
          zoom: 7,
          zoomControl: true
        });

        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: '&copy; OpenStreetMap contributors',
          maxZoom: 18
        }).addTo(map);

        leafletMap.current = map;
      }

      const map = leafletMap.current;

      // Update or create Origin Pin
      if (!originMarker.current) {
        const origIcon = L.divIcon({
          html: `<div style="background:#059669;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">A</div>`,
          className: "orig-pin",
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });
        originMarker.current = L.marker(origCoords, { icon: origIcon }).addTo(map).bindPopup(`<b>Origin Hub:</b> ${telemetry.origin}`);
      } else {
        originMarker.current.setLatLng(origCoords);
      }

      // Update or create Destination Pin
      if (!destMarker.current) {
        const destIcon = L.divIcon({
          html: `<div style="background:#dc2626;color:white;border-radius:50%;width:28px;height:28px;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;box-shadow:0 2px 8px rgba(0,0,0,0.3);border:2px solid white;">B</div>`,
          className: "dest-pin",
          iconSize: [28, 28],
          iconAnchor: [14, 14]
        });
        destMarker.current = L.marker(destCoords, { icon: destIcon }).addTo(map).bindPopup(`<b>Destination Hub:</b> ${telemetry.destination}`);
      } else {
        destMarker.current.setLatLng(destCoords);
      }

      // Draw corridor polyline
      const pathPoints = [origCoords, [vLat, vLon], destCoords];
      if (!routeLine.current) {
        routeLine.current = L.polyline(pathPoints, {
          color: "#4f46e5",
          weight: 4,
          opacity: 0.8,
          dashArray: "8, 6"
        }).addTo(map);
      } else {
        routeLine.current.setLatLngs(pathPoints);
      }

      // Update or create Vehicle marker
      const truckHtml = `
        <div style="background:#4f46e5;color:white;border-radius:50%;width:38px;height:38px;display:flex;align-items:center;justify-content:center;box-shadow:0 0 15px rgba(79,70,229,0.8);font-size:20px;border:3px solid white;animation:pulse-marker 1.8s infinite;">
          🚛
        </div>
      `;
      const truckIcon = L.divIcon({
        html: truckHtml,
        className: "truck-marker",
        iconSize: [38, 38],
        iconAnchor: [19, 19]
      });

      if (!vehicleMarker.current) {
        vehicleMarker.current = L.marker([vLat, vLon], { icon: truckIcon }).addTo(map);
      } else {
        vehicleMarker.current.setLatLng([vLat, vLon]);
      }

      vehicleMarker.current.bindPopup(`
        <div style="font-family:Inter,sans-serif;padding:4px;">
          <b>${telemetry.vehicle_info?.vehicle_id || "Fleet Vehicle"}</b><br/>
          Corridor: ${telemetry.origin} → ${telemetry.destination}<br/>
          Progress: <b>${telemetry.progress}%</b><br/>
          Remaining: <b>${telemetry.remaining_km} km</b><br/>
          Speed: <b>58 km/h</b>
        </div>
      `);

      map.panTo([vLat, vLon]);
    }

    if (window.L) {
      renderMap();
    } else {
      const timer = setInterval(() => {
        if (window.L) {
          clearInterval(timer);
          renderMap();
        }
      }, 200);
      return () => clearInterval(timer);
    }
  }, [telemetry?.latitude, telemetry?.longitude, telemetry?.origin, telemetry?.destination, activeShipmentId]);

  // Clean up Leaflet map when unmounting
  useEffect(() => {
    return () => {
      if (leafletMap.current) {
        leafletMap.current.remove();
        leafletMap.current = null;
        vehicleMarker.current = null;
        routeLine.current = null;
        originMarker.current = null;
        destMarker.current = null;
      }
    };
  }, [activeShipmentId]);

  // Simulate Next Waypoint Step
  async function handleSimulateStep() {
    if (!activeShipmentId) return;
    setSimulating(true);
    setMsg("");
    setErr("");

    try {
      const res = await api.post(`/api/tracking/${activeShipmentId}/simulate-step`);
      setMsg(`Advanced to ${res.data.location_name} (${res.data.progress}% complete).`);
      fetchTelemetry(activeShipmentId);
    } catch (e) {
      setErr("Simulation step failed.");
    } finally {
      setSimulating(false);
    }
  }

  // Dynamic Route Recalculation
  async function handleRecalculateRoute() {
    if (!activeShipmentId) return;
    setRecalculating(true);
    setMsg("");
    setErr("");
    try {
      const res = await api.post(`/api/shipments/${activeShipmentId}/recalculate-route`, {
        traffic_level: trafficSelect
      });
      setMsg(`Corridor route recalculated under '${trafficSelect}' traffic. Dynamic ETA: ${res.data.estimated_duration}.`);
      fetchTelemetry(activeShipmentId);
    } catch (e) {
      setErr(e.response?.data?.detail || "Route recalculation failed.");
    } finally {
      setRecalculating(false);
    }
  }

  // Open History modal
  async function handleOpenLiveHistory() {
    if (!activeShipmentId) return;
    try {
      const res = await api.get(`/api/shipments/${activeShipmentId}/history`);
      setLiveHistoryEvents(res.data);
      setShowLiveHistoryModal(true);
    } catch (e) {
      setErr("Unable to load event history.");
    }
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Live GPS Telemetry & Tracking</h1>
          <p className="page-subtitle">Real-time corridor monitoring with WebSocket updates, route recalculation, and waypoint simulation</p>
        </div>
        <div className="header-actions" style={{ flexWrap: "wrap", gap: "10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <label style={{ fontSize: "12px", fontWeight: "600", color: "#64748b" }}>Shipment:</label>
            <select
              className="select-filter"
              value={activeShipmentId}
              onChange={(e) => setActiveShipmentId(e.target.value)}
            >
              {shipments.map((s) => (
                <option key={s.id} value={s.shipment_id}>
                  {s.shipment_id} - {s.origin} to {s.destination} ({s.status})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <select
              className="select-filter"
              value={trafficSelect}
              onChange={(e) => setTrafficSelect(e.target.value)}
              title="Select Traffic Condition for Corridor"
            >
              <option value="Low">Low Traffic</option>
              <option value="Moderate">Moderate Traffic</option>
              <option value="High">High Traffic</option>
              <option value="Severe">Severe Traffic</option>
            </select>
            <button
              className="btn btn-secondary btn-sm"
              onClick={handleRecalculateRoute}
              disabled={recalculating || !activeShipmentId}
              title="Recalculate route and ETA with updated traffic conditions"
            >
              {recalculating ? "Recalculating..." : "🔄 Recalculate Route"}
            </button>
          </div>

          <button
            className="btn btn-success btn-sm"
            onClick={handleSimulateStep}
            disabled={simulating || (telemetry && telemetry.status === "Delivered")}
          >
            {simulating ? "Simulating..." : "▶ Simulate Next Waypoint"}
          </button>

          <button
            className="btn btn-secondary btn-sm"
            onClick={handleOpenLiveHistory}
            disabled={!activeShipmentId}
          >
            📜 Audit History
          </button>
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      {telemetry ? (
        <div className="tracking-layout">
          {/* TELEMETRY SIDEBAR CARD */}
          <div className="content-panel" style={{ margin: 0 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
              <span className="code-font">{telemetry.tracking_number}</span>
              <StatusBadge status={telemetry.status} />
            </div>

            <div style={{ fontSize: "11px", color: "#64748b", marginBottom: "12px", background: "#f8fafc", padding: "6px 10px", borderRadius: "6px", border: "1px solid #e2e8f0" }}>
              🛰️ Telemetry Source: <strong>Simulated GPS Corridor Engine</strong>
            </div>

            <h3 style={{ fontSize: "18px", fontWeight: "800", marginBottom: "4px" }}>
              {telemetry.origin} → {telemetry.destination}
            </h3>
            <p style={{ fontSize: "13px", color: "#64748b", marginBottom: "18px" }}>
              📍 {telemetry.current_location || "Transit Corridor"}
            </p>

            {/* PROGRESS BAR */}
            <div style={{ marginBottom: "18px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", fontWeight: "600", marginBottom: "6px" }}>
                <span>Route Progress</span>
                <span style={{ color: "#4f46e5" }}>{telemetry.progress}%</span>
              </div>
              <div style={{ width: "100%", height: "8px", background: "#e2e8f0", borderRadius: "9999px", overflow: "hidden" }}>
                <div
                  style={{
                    width: `${telemetry.progress}%`,
                    height: "100%",
                    background: "linear-gradient(90deg, #4f46e5 0%, #10b981 100%)",
                    transition: "width 0.4s ease"
                  }}
                />
              </div>
            </div>

            {/* DETAILS LIST */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px", fontSize: "13px", borderTop: "1px solid #f1f5f9", paddingTop: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Remaining Distance:</span>
                <strong>{telemetry.remaining_km} km</strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Estimated Arrival:</span>
                <strong style={{ color: telemetry.status === "Delivered" ? "#059669" : "#0f172a" }}>
                  {telemetry.status === "Delivered" ? "Delivered" : telemetry.eta}
                </strong>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Current Coordinates:</span>
                <span className="code-font" style={{ fontSize: "11px" }}>
                  {telemetry.latitude}, {telemetry.longitude}
                </span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#64748b" }}>Corridor Traffic:</span>
                <TrafficBadge level={telemetry.traffic_level} />
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ color: "#64748b" }}>WebSocket Stream:</span>
                <span style={{ fontWeight: 600, fontSize: "12px", color: wsStatus === "Connected" ? "#059669" : (wsStatus === "Connecting..." ? "#d97706" : "#dc2626") }}>
                  ● {wsStatus === "Connected" ? "Connected (Live Stream)" : (wsStatus === "Connecting..." ? "Connecting..." : "Disconnected")}
                </span>
              </div>
            </div>

            {/* VEHICLE & DRIVER BOX */}
            <div style={{ background: "#f8fafc", padding: "14px", borderRadius: "10px", marginTop: "18px", border: "1px solid #e2e8f0" }}>
              <div style={{ fontSize: "12px", fontWeight: 700, color: "#475569", marginBottom: "8px" }}>ASSIGNED ASSETS</div>
              <div style={{ fontSize: "13px", marginBottom: "4px" }}>
                🚛 Vehicle: <strong>{telemetry.vehicle_info?.vehicle_id || "Unassigned"}</strong> ({telemetry.vehicle_info?.registration || "N/A"})
              </div>
              <div style={{ fontSize: "13px" }}>
                👤 Driver: <strong>{telemetry.driver_info?.name || "Unassigned"}</strong> ({telemetry.driver_info?.phone || "N/A"})
              </div>
            </div>
          </div>

          {/* MAP CONTAINER */}
          <div className="map-card">
            <div
              ref={mapRef}
              className="map-viewport"
              id="leaflet-map-view"
              style={{ minHeight: "480px", zIndex: 1 }}
            ></div>
            <div className="telemetry-hud">
              <div className="hud-item">
                <span className="hud-label">Telemetry Status</span>
                <span className="hud-val" style={{ color: "#10b981", fontSize: "14px" }}>
                  {telemetry.gps_status}
                </span>
              </div>
              <div className="hud-item">
                <span className="hud-label">Transit Speed</span>
                <span className="hud-val">58 km/h</span>
              </div>
              <div className="hud-item">
                <span className="hud-label">Remaining Distance</span>
                <span className="hud-val">{telemetry.remaining_km} km</span>
              </div>
              <div className="hud-item">
                <span className="hud-label">Dynamic ETA</span>
                <span className="hud-val" style={{ color: "#4f46e5" }}>
                  {telemetry.status === "Delivered" ? "Delivered" : (telemetry.estimated_duration || "Calculating")}
                </span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="content-panel empty-state">
          <div className="empty-icon">📡</div>
          <h3>Select a shipment to begin tracking</h3>
          <p>Real-time GPS telemetry and corridor navigation will display here.</p>
        </div>
      )}

      {/* LIVE TRACKING AUDIT HISTORY MODAL */}
      {showLiveHistoryModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <h3 className="modal-title">Live Audit Trail — {activeShipmentId}</h3>
                <p style={{ fontSize: "12px", color: "#64748b" }}>
                  Historical GPS telemetry, status transitions, and corridor recalculation logs
                </p>
              </div>
              <button className="modal-close" onClick={() => setShowLiveHistoryModal(false)}>✕</button>
            </div>
            <div className="modal-body">
              {liveHistoryEvents.length > 0 ? (
                <div className="timeline">
                  {liveHistoryEvents.map((evt) => (
                    <div key={evt.id} className="timeline-item">
                      <div className="timeline-time">{new Date(evt.created_at).toLocaleString()}</div>
                      <div style={{ display: "flex", alignItems: "center", gap: "8px", margin: "2px 0 4px 0" }}>
                        <span className="timeline-title">{evt.event_type}</span>
                        {(evt.previous_status || evt.new_status) && (
                          <span style={{ fontSize: "11px", fontWeight: 600, color: "#4f46e5" }}>
                            ({evt.previous_status || "Created"} ➔ {evt.new_status || evt.status})
                          </span>
                        )}
                      </div>
                      <div className="timeline-desc">{evt.description}</div>
                      {evt.latitude && evt.longitude && (
                        <div style={{ fontSize: "11px", color: "#0284c7", marginTop: "4px" }}>
                          📍 Lat: {evt.latitude}, Lon: {evt.longitude} ({evt.current_location})
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: "#64748b", textAlign: "center" }}>No event history recorded yet.</p>
              )}
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setShowLiveHistoryModal(false)}>Close</button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}



// =========================================================
// ROUTE OPTIMIZATION MODULE (Milestone 2 Core)
// =========================================================

function RouteOptimization({ setPage }) {
  const [origin, setOrigin] = useState("Vijayawada");
  const [destination, setDestination] = useState("Hyderabad");
  const [trafficLevel, setTrafficLevel] = useState("Moderate");
  const [vehicleType, setVehicleType] = useState("Truck");

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");

  async function handleCalculate(e) {
    if (e) e.preventDefault();
    setLoading(true);
    setErr("");

    try {
      const res = await api.post("/api/routes/calculate", {
        origin,
        destination,
        traffic_level: trafficLevel,
        vehicle_type: vehicleType
      });
      setResult(res.data);
    } catch (error) {
      setErr(error.response?.data?.detail || "Route optimization calculation failed.");
    } finally {
      setLoading(false);
    }
  }

  async function handleRecalculate(e) {
    if (e) e.preventDefault();
    setLoading(true);
    setErr("");

    try {
      const res = await api.post("/api/routes/recalculate", {
        origin,
        destination,
        traffic_level: trafficLevel,
        vehicle_type: vehicleType
      });
      setResult(res.data);
    } catch (error) {
      setErr(error.response?.data?.detail || "Route recalculation failed.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    handleCalculate();
  }, []);

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Route Optimization & Traffic Planning</h1>
          <p className="page-subtitle">Multi-objective algorithmic routing comparing duration, road distance, traffic stalls, and fuel burn</p>
        </div>
      </div>

      {err && <div className="alert alert-error">{err}</div>}

      {/* INPUT PANEL */}
      <div className="content-panel">
        <form onSubmit={handleCalculate}>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", alignItems: "flex-end" }}>
            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Origin Hub</label>
              <input
                className="form-input"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder="e.g. Vijayawada"
                required
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Destination Hub</label>
              <input
                className="form-input"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder="e.g. Hyderabad"
                required
              />
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Traffic Congestion Level</label>
              <select
                className="form-select"
                value={trafficLevel}
                onChange={(e) => setTrafficLevel(e.target.value)}
              >
                <option value="Low">Low (Free Flow)</option>
                <option value="Moderate">Moderate (Normal Conditions)</option>
                <option value="High">High (Peak Highway Congestion)</option>
                <option value="Severe">Severe (Major Bottleneck)</option>
              </select>
            </div>

            <div className="form-group" style={{ margin: 0 }}>
              <label className="form-label">Fleet Vehicle Class</label>
              <select
                className="form-select"
                value={vehicleType}
                onChange={(e) => setVehicleType(e.target.value)}
              >
                <option>Truck</option>
                <option>Van</option>
                <option>Container Truck</option>
                <option>Car</option>
              </select>
            </div>

            <div style={{ display: "flex", gap: "8px" }}>
              <button className="btn btn-primary" type="submit" disabled={loading} style={{ height: "40px" }}>
                {loading ? "Calculating..." : "⚡ Optimize Corridor"}
              </button>
              <button
                className="btn btn-secondary"
                type="button"
                onClick={handleRecalculate}
                disabled={loading}
                style={{ height: "40px" }}
                title="Recalculate route alternatives with updated traffic condition"
              >
                🔄 Recalculate
              </button>
            </div>
          </div>
          <div style={{ fontSize: "12px", color: "#64748b", marginTop: "12px" }}>
            ℹ️ Traffic Model: <strong>Algorithmic Corridor Simulation</strong> (Indian Highway Networks NH44/NH16). Accurately incorporates congestion factors without paid third-party API dependencies.
          </div>
        </form>
      </div>

      {/* COMPARISON RESULTS MATRIX */}
      {result && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h2 className="panel-title">
              Route Alternatives ({origin} → {destination})
            </h2>
            <TrafficBadge level={result.traffic_level} />
          </div>

          <div className="routes-grid">
            {result.routes.map((r) => {
              const isRec = r.route_type === result.recommended_route;
              return (
                <div key={r.route_type} className={`route-card ${isRec ? "recommended" : ""}`}>
                  {isRec && <div className="recommended-ribbon">⭐ Recommended Choice</div>}
                  <h3 className="route-title">{r.route_type}</h3>
                  <p style={{ fontSize: "12px", color: "#64748b" }}>{r.name}</p>

                  <div className="route-metrics">
                    <div className="metric-block">
                      <span>Total Distance</span>
                      <strong>{r.distance_km} km</strong>
                    </div>
                    <div className="metric-block">
                      <span>Estimated Duration</span>
                      <strong style={{ color: isRec ? "#4f46e5" : "#0f172a" }}>{r.duration_text}</strong>
                    </div>
                    <div className="metric-block">
                      <span>Fuel Burn</span>
                      <strong>~{r.fuel_estimate_liters} L</strong>
                    </div>
                    <div className="metric-block">
                      <span>CO₂ Footprint</span>
                      <strong>{r.co2_emissions_kg} kg</strong>
                    </div>
                  </div>

                  <p className="route-desc">{r.description}</p>

                  <div style={{ borderTop: "1px solid #f1f5f9", paddingTop: "12px", fontSize: "12px", color: "#64748b" }}>
                    Arrival ETA: <strong>{r.eta_time}</strong>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}


// =========================================================
// TRIPS SCHEDULING MODULE (Milestone 2 Core)
// =========================================================

function Trips({ userRole }) {
  const [trips, setTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [shipments, setShipments] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");

  const [form, setForm] = useState({
    origin: "Vijayawada",
    destination: "Hyderabad",
    vehicle_id: "",
    driver_id: "",
    shipment_id: "",
    route_type: "Fastest Route",
    notes: "Scheduled transit"
  });

  const canWrite = userRole === "Administrator" || userRole === "Fleet Manager" || userRole === "Dispatcher";

  async function loadData() {
    try {
      const [tRes, vRes, dRes, sRes] = await Promise.all([
        api.get("/api/trips"),
        api.get("/api/vehicles"),
        api.get("/api/drivers"),
        api.get("/api/shipments")
      ]);
      setTrips(tRes.data);
      setVehicles(vRes.data);
      setDrivers(dRes.data);
      setShipments(sRes.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to load trips.");
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleScheduleTrip(e) {
    e.preventDefault();
    setMsg("");
    setErr("");

    try {
      const res = await api.post("/api/trips", {
        origin: form.origin.trim(),
        destination: form.destination.trim(),
        vehicle_id: Number(form.vehicle_id),
        driver_id: Number(form.driver_id),
        shipment_id: form.shipment_id ? Number(form.shipment_id) : null,
        route_type: form.route_type,
        notes: form.notes
      });

      setMsg(`Trip ${res.data.trip_id} scheduled successfully.`);
      setShowModal(false);
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Unable to schedule trip (check for asset assignment conflicts).");
    }
  }

  async function handleUpdateTripStatus(tripId, status) {
    try {
      await api.put(`/api/trips/${tripId}/status`, { trip_status: status });
      setMsg(`Trip updated to ${status}.`);
      loadData();
    } catch (e) {
      setErr(e.response?.data?.detail || "Status transition error.");
    }
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Trip Scheduling & Dispatch</h1>
          <p className="page-subtitle">Schedule journeys, verify vehicle and operator availability, and track progress</p>
        </div>
        <div className="header-actions">
          {canWrite && (
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>
              + Schedule Trip
            </button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={loadData}>↻ Refresh</button>
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}

      <div className="content-panel">
        <div className="panel-header">
          <h2 className="panel-title">Scheduled Fleet Journeys ({trips.length})</h2>
        </div>

        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>Trip ID</th>
                <th>Corridor</th>
                <th>Vehicle</th>
                <th>Driver</th>
                <th>Linked Shipment</th>
                <th>Routing Strategy</th>
                <th>Distance</th>
                <th>Trip Status</th>
                {canWrite && <th>Quick Action</th>}
              </tr>
            </thead>
            <tbody>
              {trips.length > 0 ? (
                trips.map((t) => (
                  <tr key={t.id}>
                    <td><span className="code-font">{t.trip_id}</span></td>
                    <td>{t.origin} → {t.destination}</td>
                    <td><strong>{t.vehicle_code}</strong></td>
                    <td>{t.driver_name}</td>
                    <td>{t.shipment_code ? <span className="code-font">{t.shipment_code}</span> : <span style={{ color: "#94a3b8" }}>Stand-alone</span>}</td>
                    <td>{t.route_type}</td>
                    <td>{t.distance_km} km</td>
                    <td><StatusBadge status={t.trip_status} /></td>
                    {canWrite && (
                      <td>
                        <select
                          className="select-filter"
                          style={{ padding: "4px 8px", fontSize: "11px" }}
                          value={t.trip_status}
                          onChange={(e) => handleUpdateTripStatus(t.trip_id, e.target.value)}
                        >
                          <option value="Scheduled">Scheduled</option>
                          <option value="Started">Start Journey</option>
                          <option value="In Transit">In Transit</option>
                          <option value="Completed">Mark Completed</option>
                          <option value="Cancelled">Cancel Trip</option>
                        </select>
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9" style={{ textAlign: "center", color: "#64748b" }}>
                    No trips currently scheduled.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* SCHEDULE TRIP MODAL */}
      {showModal && (
        <div className="modal-backdrop">
          <div className="modal-card">
            <div className="modal-header">
              <h3 className="modal-title">Schedule New Transit Trip</h3>
              <button className="modal-close" onClick={() => setShowModal(false)}>✕</button>
            </div>
            <form onSubmit={handleScheduleTrip}>
              <div className="modal-body">
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Origin Location</label>
                    <input
                      className="form-input"
                      value={form.origin}
                      onChange={(e) => setForm({ ...form, origin: e.target.value })}
                      required
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Destination Location</label>
                    <input
                      className="form-input"
                      value={form.destination}
                      onChange={(e) => setForm({ ...form, destination: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Select Vehicle</label>
                    <select
                      className="form-select"
                      value={form.vehicle_id}
                      onChange={(e) => setForm({ ...form, vehicle_id: e.target.value })}
                      required
                    >
                      <option value="">Choose Vehicle</option>
                      {vehicles.map((v) => (
                        <option key={v.id} value={v.id}>
                          {v.vehicle_id} - {v.vehicle_type} ({v.current_status})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Select Driver</label>
                    <select
                      className="form-select"
                      value={form.driver_id}
                      onChange={(e) => setForm({ ...form, driver_id: e.target.value })}
                      required
                    >
                      <option value="">Choose Driver</option>
                      {drivers.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.name} ({d.driver_id})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
                  <div className="form-group">
                    <label className="form-label">Link Shipment (Optional)</label>
                    <select
                      className="form-select"
                      value={form.shipment_id}
                      onChange={(e) => setForm({ ...form, shipment_id: e.target.value })}
                    >
                      <option value="">None (Dedicated Fleet Transit)</option>
                      {shipments.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.shipment_id} ({s.origin} → {s.destination})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Route Strategy</label>
                    <select
                      className="form-select"
                      value={form.route_type}
                      onChange={(e) => setForm({ ...form, route_type: e.target.value })}
                    >
                      <option>Fastest Route</option>
                      <option>Shortest Route</option>
                      <option>Traffic Avoidance</option>
                      <option>Fuel Efficient Route</option>
                    </select>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">Operational Notes</label>
                  <input
                    className="form-input"
                    value={form.notes}
                    onChange={(e) => setForm({ ...form, notes: e.target.value })}
                    placeholder="e.g. Early morning departure corridor"
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Confirm & Schedule</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </section>
  );
}


// =========================================================
// MILESTONE 3: VEHICLE MAINTENANCE MANAGEMENT
// =========================================================

function Maintenance({ userRole }) {
  const [records, setRecords] = useState([]);
  const [summary, setSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");
  const [workerMsg, setWorkerMsg] = useState("");

  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");
  const [statusFilter, setStatusFilter] = useState("All");
  const [priorityFilter, setPriorityFilter] = useState("All");

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [statusForm, setStatusForm] = useState({ status: "In Progress", notes: "", cost: 0 });

  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [historyList, setHistoryList] = useState([]);
  const [historyTitle, setHistoryTitle] = useState("");

  const [createForm, setCreateForm] = useState({
    vehicle_id: "",
    category: "Oil Change",
    description: "",
    scheduled_date: "",
    priority: "Medium",
    cost: "",
    mileage: "",
    service_center: "",
    notes: ""
  });

  const canManage = userRole === "Administrator" || userRole === "Fleet Manager";

  async function loadData() {
    setLoading(true);
    setErr("");
    try {
      const [recRes, sumRes, altRes, vehRes] = await Promise.all([
        api.get("/api/maintenance"),
        api.get("/api/maintenance/summary"),
        api.get("/api/maintenance/alerts"),
        api.get("/api/vehicles")
      ]);
      setRecords(recRes.data);
      setSummary(sumRes.data);
      setAlerts(altRes.data);
      setVehicles(vehRes.data);
      if (vehRes.data.length > 0 && !createForm.vehicle_id) {
        setCreateForm((prev) => ({ ...prev, vehicle_id: vehRes.data[0].id }));
      }
    } catch (e) {
      setErr(e.response?.data?.detail || "Unable to load maintenance records.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  async function handleCreateMaintenance(e) {
    e.preventDefault();
    setMsg("");
    setErr("");
    try {
      await api.post("/api/maintenance", {
        vehicle_id: parseInt(createForm.vehicle_id),
        category: createForm.category,
        description: createForm.description.trim() || undefined,
        scheduled_date: new Date(createForm.scheduled_date).toISOString(),
        priority: createForm.priority,
        cost: createForm.cost ? parseFloat(createForm.cost) : 0.0,
        mileage: createForm.mileage ? parseFloat(createForm.mileage) : undefined,
        service_center: createForm.service_center.trim() || undefined,
        notes: createForm.notes.trim() || undefined
      });
      setMsg("Preventative service successfully scheduled in PostgreSQL.");
      setShowCreateModal(false);
      setCreateForm({
        vehicle_id: vehicles[0]?.id || "",
        category: "Oil Change",
        description: "",
        scheduled_date: "",
        priority: "Medium",
        cost: "",
        mileage: "",
        service_center: "",
        notes: ""
      });
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to schedule maintenance.");
    }
  }

  async function handleStatusUpdate(e) {
    e.preventDefault();
    if (!selectedRecord) return;
    setMsg("");
    setErr("");
    try {
      await api.put(`/api/maintenance/${selectedRecord.id}/status`, {
        status: statusForm.status,
        notes: statusForm.notes.trim() || undefined,
        cost: statusForm.cost ? parseFloat(statusForm.cost) : undefined
      });
      setMsg(`Service #${selectedRecord.maintenance_id} transitioned to '${statusForm.status}'.`);
      setShowStatusModal(false);
      setSelectedRecord(null);
      loadData();
    } catch (error) {
      setErr(error.response?.data?.detail || "Failed to update maintenance status.");
    }
  }

  async function handleViewHistory(rec) {
    try {
      const res = await api.get(`/api/maintenance/vehicle/${rec.vehicle_id}/history`);
      setHistoryList(res.data);
      setHistoryTitle(`Service History: ${rec.vehicle_code} (${rec.registration_number})`);
      setShowHistoryModal(true);
    } catch (error) {
      setErr(error.response?.data?.detail || "Could not retrieve service history.");
    }
  }

  async function handleTriggerCeleryScan() {
    setWorkerMsg("Dispatching task to Celery background worker via Redis...");
    try {
      const res = await api.post("/api/tasks/maintenance-scan");
      setWorkerMsg(`⚡ Celery Worker Scan: Task ID ${res.data.task_id} (Status: ${res.data.status})`);
      setTimeout(() => {
        loadData();
      }, 1200);
    } catch (e) {
      setWorkerMsg(`Worker notice: ${e.response?.data?.detail || e.message}`);
    }
  }

  const filtered = records.filter((r) => {
    const term = search.toLowerCase();
    const matchesSearch =
      r.maintenance_id.toLowerCase().includes(term) ||
      (r.vehicle_code && r.vehicle_code.toLowerCase().includes(term)) ||
      (r.registration_number && r.registration_number.toLowerCase().includes(term)) ||
      r.category.toLowerCase().includes(term) ||
      (r.description && r.description.toLowerCase().includes(term));

    const matchesCat = categoryFilter === "All" || r.category === categoryFilter;
    const matchesStatus = statusFilter === "All" || r.status === statusFilter;
    const matchesPriority = priorityFilter === "All" || r.priority === priorityFilter;

    return matchesSearch && matchesCat && matchesStatus && matchesPriority;
  });

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Fleet Maintenance & Service Management</h1>
          <p className="page-subtitle">Schedule preventative servicing, track vehicle health logs, and monitor proactive maintenance alerts</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={handleTriggerCeleryScan}>
            ⚡ Run Celery Scan
          </button>
          <button className="btn btn-secondary btn-sm" onClick={loadData}>
            ↻ Refresh Data
          </button>
          {canManage && (
            <button className="btn btn-primary btn-sm" onClick={() => setShowCreateModal(true)}>
              + Schedule Service
            </button>
          )}
        </div>
      </div>

      {msg && <div className="alert alert-success">{msg}</div>}
      {err && <div className="alert alert-error">{err}</div>}
      {workerMsg && (
        <div className="alert" style={{ background: "rgba(56, 189, 248, 0.1)", border: "1px solid rgba(56, 189, 248, 0.3)", color: "#38bdf8" }}>
          {workerMsg}
        </div>
      )}

      {/* SUMMARY KPI CARDS */}
      {summary && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-title">Total Records</span>
              <div className="stat-icon">🔧</div>
            </div>
            <div className="stat-number">{summary.total_records}</div>
            <span className="stat-footnote">Active maintenance log</span>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-title">Scheduled</span>
              <div className="stat-icon" style={{ background: "#eff6ff", color: "#2563eb" }}>📅</div>
            </div>
            <div className="stat-number">{summary.scheduled_count}</div>
            <span className="stat-footnote">Upcoming preventative slots</span>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-title">In Progress</span>
              <div className="stat-icon" style={{ background: "#fef3c7", color: "#d97706" }}>⚙️</div>
            </div>
            <div className="stat-number">{summary.in_progress_count}</div>
            <span className="stat-footnote">At workshop depot</span>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-title">Overdue Alerts</span>
              <div className="stat-icon" style={{ background: "#fee2e2", color: "#ef4444" }}>⚠️</div>
            </div>
            <div className="stat-number" style={{ color: summary.overdue_count > 0 ? "#ef4444" : "inherit" }}>
              {summary.overdue_count}
            </div>
            <span className="stat-footnote">Require urgent action</span>
          </div>

          <div className="stat-card">
            <div className="stat-header">
              <span className="stat-title">Total Cost</span>
              <div className="stat-icon" style={{ background: "#ecfdf5", color: "#10b981" }}>₹</div>
            </div>
            <div className="stat-number">₹{summary.total_maintenance_cost.toLocaleString()}</div>
            <span className="stat-footnote">Persisted service expenses</span>
          </div>
        </div>
      )}

      {/* PROACTIVE ALERTS BANNER */}
      {alerts && alerts.length > 0 && (
        <div className="content-panel" style={{ borderLeft: "4px solid #ef4444", marginBottom: "24px" }}>
          <div className="panel-header" style={{ marginBottom: "12px" }}>
            <div>
              <h2 className="panel-title" style={{ color: "#ef4444", display: "flex", alignItems: "center", gap: "8px" }}>
                <span>🚨</span> Proactive Maintenance Alerts ({alerts.length})
              </h2>
              <p style={{ fontSize: "12px", color: "#64748b" }}>Automated health warnings derived from real scheduled maintenance records</p>
            </div>
          </div>
          <div className="maintenance-alerts-container">
            {alerts.map((alt) => (
              <div key={alt.id} className={`alert-item ${alt.severity}`}>
                <div>
                  <strong style={{ marginRight: "8px" }}>[{alt.alert_type}]</strong>
                  <span>{alt.message}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <span className={`alert-badge badge-${alt.severity}`}>{alt.priority}</span>
                  {canManage && (
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        const target = records.find((r) => r.id === alt.id);
                        if (target) {
                          setSelectedRecord(target);
                          setStatusForm({ status: "In Progress", notes: "Technician dispatched", cost: target.cost });
                          setShowStatusModal(true);
                        }
                      }}
                    >
                      Resolve
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* MAIN SCHEDULE TABLE & CONTROLS */}
      <div className="content-panel">
        <div className="table-controls-bar">
          <input
            className="form-input"
            style={{ maxWidth: "260px" }}
            placeholder="Search service, vehicle, ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />

          <select
            className="form-select"
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
          >
            <option value="All">All Categories</option>
            <option value="Oil Change">Oil Change</option>
            <option value="Tire Replacement">Tire Replacement</option>
            <option value="Engine Service">Engine Service</option>
            <option value="Brake Service">Brake Service</option>
            <option value="General Inspection">General Inspection</option>
          </select>

          <select
            className="form-select"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="All">All Statuses</option>
            <option value="Scheduled">Scheduled</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Overdue">Overdue</option>
            <option value="Cancelled">Cancelled</option>
          </select>

          <select
            className="form-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="All">All Priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Urgent">Urgent</option>
          </select>

          <div style={{ marginLeft: "auto", fontSize: "13px", color: "#64748b" }}>
            Showing <strong>{filtered.length}</strong> of {records.length} records
          </div>
        </div>

        {loading ? (
          <p style={{ padding: "20px", color: "#64748b" }}>Loading maintenance schedule...</p>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🔧</div>
            <p className="empty-text">No maintenance records matched your filter.</p>
          </div>
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Vehicle</th>
                  <th>Category</th>
                  <th>Scheduled Date</th>
                  <th>Priority</th>
                  <th>Cost</th>
                  <th>Status</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span className="mono-code">{r.maintenance_id}</span>
                    </td>
                    <td>
                      <strong>{r.vehicle_code}</strong>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>{r.registration_number} • {r.vehicle_type}</div>
                    </td>
                    <td>
                      <span className="badge badge-category">{r.category}</span>
                    </td>
                    <td>
                      {new Date(r.scheduled_date).toLocaleDateString()}
                      <div style={{ fontSize: "11px", color: r.is_overdue ? "#ef4444" : "#64748b" }}>
                        {r.is_overdue ? "Overdue" : r.days_until_due === 0 ? "Due Today" : `In ${r.days_until_due} days`}
                      </div>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: r.priority === "Urgent" ? "rgba(239, 68, 68, 0.2)" : r.priority === "High" ? "rgba(245, 158, 11, 0.2)" : "rgba(59, 130, 246, 0.15)",
                          color: r.priority === "Urgent" ? "#ef4444" : r.priority === "High" ? "#f59e0b" : "#3b82f6"
                        }}
                      >
                        {r.priority}
                      </span>
                    </td>
                    <td>
                      <span className="mono-code">₹{r.cost ? r.cost.toLocaleString() : "0"}</span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          background: r.status === "Completed" ? "rgba(16, 185, 129, 0.15)" : r.status === "In Progress" ? "rgba(245, 158, 11, 0.2)" : r.status === "Overdue" ? "rgba(239, 68, 68, 0.2)" : "rgba(100, 116, 139, 0.2)",
                          color: r.status === "Completed" ? "#10b981" : r.status === "In Progress" ? "#f59e0b" : r.status === "Overdue" ? "#ef4444" : "#cbd5e1"
                        }}
                      >
                        {r.status}
                      </span>
                    </td>
                    <td style={{ textAlign: "right" }}>
                      <div style={{ display: "inline-flex", gap: "6px" }}>
                        <button
                          className="btn btn-secondary btn-sm"
                          title="View Service History"
                          onClick={() => handleViewHistory(r)}
                        >
                          📜 History
                        </button>
                        {canManage && (
                          <button
                            className="btn btn-primary btn-sm"
                            title="Update Status"
                            onClick={() => {
                              setSelectedRecord(r);
                              setStatusForm({ status: r.status, notes: "", cost: r.cost });
                              setShowStatusModal(true);
                            }}
                          >
                            Update
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* MAINTENANCE REPORTS: BY CATEGORY & FLEET ASSET */}
      {summary && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginTop: "24px", marginBottom: "24px" }}>
          {/* CATEGORY BREAKDOWN */}
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Service Records by Category</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              {["Oil Change", "Tire Replacement", "Engine Service", "Brake Service", "General Inspection"].map((cat) => {
                const count = summary.records_by_category?.[cat] || 0;
                const cost = summary.cost_by_category?.[cat] || 0;
                return (
                  <div key={cat} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                    <div>
                      <strong style={{ fontSize: "13px" }}>{cat}</strong>
                      <div style={{ fontSize: "11px", color: "#64748b" }}>{count} scheduled / logged</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <span className="mono-code" style={{ fontSize: "13px" }}>₹{cost.toLocaleString()}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* VEHICLE ASSET BREAKDOWN */}
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Maintenance Expenditure by Asset</h2>
            {summary.maintenance_by_vehicle && summary.maintenance_by_vehicle.length > 0 ? (
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Vehicle</th>
                      <th>Total Services</th>
                      <th>Total Spend</th>
                      <th>Latest Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.maintenance_by_vehicle.map((v) => (
                      <tr key={v.vehicle_id}>
                        <td><strong>{v.vehicle_code}</strong> <span style={{ fontSize: "11px", color: "#64748b" }}>({v.registration_number})</span></td>
                        <td>{v.total_services} service(s)</td>
                        <td><span className="mono-code">₹{v.total_cost.toLocaleString()}</span></td>
                        <td><StatusBadge status={v.latest_status} /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div style={{ color: "#64748b", padding: "16px", textAlign: "center" }}>
                No vehicle-specific maintenance records recorded yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* SCHEDULE SERVICE MODAL */}
      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal-card" style={{ maxWidth: "560px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Schedule Preventative Service</h3>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>×</button>
            </div>
            <form onSubmit={handleCreateMaintenance}>
              <div className="form-group">
                <label className="form-label">Target Fleet Vehicle *</label>
                <select
                  className="form-select"
                  value={createForm.vehicle_id}
                  onChange={(e) => setCreateForm({ ...createForm, vehicle_id: e.target.value })}
                  required
                >
                  {vehicles.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.vehicle_id} — {v.registration_number} ({v.vehicle_type}, Status: {v.current_status})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Service Category *</label>
                  <select
                    className="form-select"
                    value={createForm.category}
                    onChange={(e) => setCreateForm({ ...createForm, category: e.target.value })}
                  >
                    <option value="Oil Change">Oil Change</option>
                    <option value="Tire Replacement">Tire Replacement</option>
                    <option value="Engine Service">Engine Service</option>
                    <option value="Brake Service">Brake Service</option>
                    <option value="General Inspection">General Inspection</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Priority Level *</label>
                  <select
                    className="form-select"
                    value={createForm.priority}
                    onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                    <option value="Urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Scheduled Date & Time *</label>
                  <input
                    type="datetime-local"
                    className="form-input"
                    value={createForm.scheduled_date}
                    onChange={(e) => setCreateForm({ ...createForm, scheduled_date: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Estimated Cost (INR ₹)</label>
                  <input
                    type="number"
                    min="0"
                    step="50"
                    className="form-input"
                    placeholder="e.g. 5000"
                    value={createForm.cost}
                    onChange={(e) => setCreateForm({ ...createForm, cost: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                <div className="form-group">
                  <label className="form-label">Odometer / Mileage (km)</label>
                  <input
                    type="number"
                    min="0"
                    className="form-input"
                    placeholder="e.g. 35000"
                    value={createForm.mileage}
                    onChange={(e) => setCreateForm({ ...createForm, mileage: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Service Workshop</label>
                  <input
                    className="form-input"
                    placeholder="e.g. Central Depot Workshop"
                    value={createForm.service_center}
                    onChange={(e) => setCreateForm({ ...createForm, service_center: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Description / Work Scope</label>
                <textarea
                  className="form-input"
                  rows="2"
                  placeholder="Details of preventative repairs, part replacements, or issues..."
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Confirm Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* UPDATE STATUS MODAL */}
      {showStatusModal && selectedRecord && (
        <div className="modal-overlay" onClick={() => setShowStatusModal(false)}>
          <div className="modal-card" style={{ maxWidth: "480px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">Update Service Lifecycle</h3>
              <button className="modal-close" onClick={() => setShowStatusModal(false)}>×</button>
            </div>
            <form onSubmit={handleStatusUpdate}>
              <div style={{ marginBottom: "16px", padding: "12px", background: "rgba(255,255,255,0.04)", borderRadius: "8px" }}>
                <div><strong>Service ID:</strong> {selectedRecord.maintenance_id}</div>
                <div><strong>Vehicle:</strong> {selectedRecord.vehicle_code} ({selectedRecord.registration_number})</div>
                <div><strong>Category:</strong> {selectedRecord.category}</div>
                <div><strong>Current Status:</strong> <span className="badge">{selectedRecord.status}</span></div>
              </div>

              <div className="form-group">
                <label className="form-label">New Status *</label>
                <select
                  className="form-select"
                  value={statusForm.status}
                  onChange={(e) => setStatusForm({ ...statusForm, status: e.target.value })}
                >
                  <option value="Scheduled">Scheduled</option>
                  <option value="In Progress">In Progress (Vehicle moves to Maintenance)</option>
                  <option value="Completed">Completed (Vehicle released to Available)</option>
                  <option value="Overdue">Overdue</option>
                  <option value="Cancelled">Cancelled</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Final Actual Cost (INR ₹)</label>
                <input
                  type="number"
                  min="0"
                  step="50"
                  className="form-input"
                  value={statusForm.cost}
                  onChange={(e) => setStatusForm({ ...statusForm, cost: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Technician Audit Notes</label>
                <textarea
                  className="form-input"
                  rows="3"
                  placeholder="Record work completed, replaced parts, or inspection notes..."
                  value={statusForm.notes}
                  onChange={(e) => setStatusForm({ ...statusForm, notes: e.target.value })}
                />
              </div>

              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowStatusModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Save Status
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* SERVICE HISTORY MODAL */}
      {showHistoryModal && (
        <div className="modal-overlay" onClick={() => setShowHistoryModal(false)}>
          <div className="modal-card" style={{ maxWidth: "650px" }} onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3 className="modal-title">{historyTitle}</h3>
              <button className="modal-close" onClick={() => setShowHistoryModal(false)}>×</button>
            </div>
            {historyList.length === 0 ? (
              <p style={{ padding: "20px", color: "#64748b" }}>No historical service records found for this vehicle.</p>
            ) : (
              <div style={{ maxHeight: "380px", overflowY: "auto" }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Event</th>
                      <th>Transition</th>
                      <th>Cost</th>
                      <th>Notes</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {historyList.map((h) => (
                      <tr key={h.id}>
                        <td><strong>{h.event_type}</strong></td>
                        <td>
                          <span style={{ fontSize: "12px", color: "#94a3b8" }}>
                            {h.previous_status || "None"} ➔ <strong>{h.new_status}</strong>
                          </span>
                        </td>
                        <td>₹{h.cost ? h.cost.toLocaleString() : "0"}</td>
                        <td style={{ fontSize: "12px", color: "#cbd5e1" }}>{h.notes || "—"}</td>
                        <td style={{ fontSize: "11px", color: "#64748b" }}>{new Date(h.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <div className="modal-actions">
              <button className="btn btn-secondary" onClick={() => setShowHistoryModal(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}


// =========================================================
// MILESTONE 3: FLEET PERFORMANCE & FUEL ANALYTICS
// =========================================================

function Analytics({ userRole }) {
  const [operational, setOperational] = useState(null);
  const [fuel, setFuel] = useState(null);
  const [utilization, setUtilization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [workerResult, setWorkerResult] = useState("");

  async function loadAnalytics() {
    setLoading(true);
    setErr("");
    try {
      const [opRes, flRes, utRes] = await Promise.all([
        api.get("/api/analytics/operational"),
        api.get("/api/analytics/fuel-monitoring"),
        api.get("/api/analytics/fleet-utilization")
      ]);
      setOperational(opRes.data);
      setFuel(flRes.data);
      setUtilization(utRes.data);
    } catch (e) {
      setErr(e.response?.data?.detail || "Failed to load operational analytics.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAnalytics();
  }, []);

  async function runCeleryTask(taskType) {
    setWorkerResult("Queueing background task to Celery via Redis broker...");
    try {
      let endpoint = "/api/tasks/analytics-aggregation";
      if (taskType === "reminders") endpoint = "/api/tasks/maintenance-reminders";
      if (taskType === "overdue") endpoint = "/api/tasks/maintenance-scan";

      const res = await api.post(endpoint);
      setWorkerResult(`⚡ Celery Worker Dispatched: [${res.data.task_name}] Task ID: ${res.data.task_id} (Status: ${res.data.status})`);
      loadAnalytics();
    } catch (e) {
      setWorkerResult(`Celery task error: ${e.response?.data?.detail || e.message}`);
    }
  }

  if (loading) {
    return <div className="content-panel"><p>Loading fleet performance and fuel analytics...</p></div>;
  }

  return (
    <section>
      <div className="page-header">
        <div>
          <h1 className="page-title">Fleet Performance & Fuel Analytics</h1>
          <p className="page-subtitle">Real-time operational KPIs, fleet utilization analytics, fuel expenditure monitoring, and Celery background workers</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary btn-sm" onClick={loadAnalytics}>
            ↻ Refresh Analytics
          </button>
        </div>
      </div>

      {err && <div className="alert alert-error">{err}</div>}

      {/* TOP UTILIZATION & EFFICIENCY METRICS */}
      {operational && fuel && (
        <div className="kpi-row">
          <div className="kpi-card">
            <span className="kpi-title">Fleet Utilization Rate</span>
            <div className="kpi-value" style={{ color: "#38bdf8" }}>
              {operational.fleet.fleet_utilization_percent}%
            </div>
            <span className="kpi-subtitle">
              {operational.fleet.active_vehicles} active / {operational.fleet.total_vehicles} total vehicles
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-title">Delivery Completion Rate</span>
            <div className="kpi-value" style={{ color: "#10b981" }}>
              {operational.shipments.completion_rate_percent}%
            </div>
            <span className="kpi-subtitle">
              {operational.shipments.delivered_shipments} of {operational.shipments.total_shipments} shipments fulfilled
            </span>
          </div>

          <div className="kpi-card">
            <span className="kpi-title">Average Fleet Fuel Economy</span>
            <div className="kpi-value" style={{ color: "#f59e0b" }}>
              {fuel.average_fleet_efficiency_kpl} km/L
            </div>
            <span className="kpi-subtitle">Commercial freight powertrain benchmark</span>
          </div>

          <div className="kpi-card">
            <span className="kpi-title">Total Fuel Burned</span>
            <div className="kpi-value">
              {fuel.total_fuel_consumed_liters.toLocaleString()} L
            </div>
            <span className="kpi-subtitle">
              Est. Cost: ₹{fuel.total_fuel_cost_estimated.toLocaleString()} (@ ₹95/L)
            </span>
          </div>
        </div>
      )}

      {/* OPERATIONAL KPIS GRID */}
      {operational && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px", marginBottom: "24px" }}>
          {/* FLEET UTILIZATION BREAKDOWN */}
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Fleet Utilization Breakdown</h2>
            <div style={{ marginBottom: "16px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "14px", marginBottom: "8px" }}>
                <span>Active Assets</span>
                <strong>{operational.fleet.active_vehicles}</strong>
              </div>
              <div style={{ width: "100%", height: "8px", background: "rgba(255,255,255,0.1)", borderRadius: "4px", overflow: "hidden" }}>
                <div style={{ width: `${operational.fleet.fleet_utilization_percent}%`, height: "100%", background: "#38bdf8" }} />
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Available Vehicles</div>
                <div style={{ fontSize: "20px", fontWeight: "700" }}>{operational.fleet.available_vehicles}</div>
              </div>
              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Under Maintenance</div>
                <div style={{ fontSize: "20px", fontWeight: "700", color: "#f59e0b" }}>{operational.fleet.maintenance_vehicles}</div>
              </div>
            </div>

            <div className="methodology-box" style={{ marginTop: "16px" }}>
              <strong>Documented Formula:</strong> {operational.fleet.utilization_formula}
            </div>
          </div>

          {/* DRIVER & LOGISTICS METRICS */}
          <div className="content-panel">
            <h2 className="panel-title" style={{ marginBottom: "16px" }}>Driver & Delivery Performance</h2>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "16px" }}>
              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Active Drivers</div>
                <div style={{ fontSize: "20px", fontWeight: "700", color: "#10b981" }}>{operational.drivers.active_drivers}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>{operational.drivers.assigned_drivers} assigned to fleet</div>
              </div>

              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Driver Attendance</div>
                <div style={{ fontSize: "20px", fontWeight: "700" }}>{operational.drivers.average_attendance}%</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>Avg. Score: {operational.drivers.average_performance}/100</div>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Dispatched Trips</div>
                <div style={{ fontSize: "20px", fontWeight: "700" }}>{operational.trips.total_trips}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>{operational.trips.completed_trips} completed</div>
              </div>

              <div style={{ padding: "12px", background: "rgba(255,255,255,0.03)", borderRadius: "6px" }}>
                <div style={{ fontSize: "12px", color: "#64748b" }}>Maintenance Cost</div>
                <div style={{ fontSize: "20px", fontWeight: "700", color: "#38bdf8" }}>₹{operational.maintenance.total_expenditure.toLocaleString()}</div>
                <div style={{ fontSize: "11px", color: "#64748b" }}>{operational.maintenance.total_records} logged services</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* FUEL CONSUMPTION BY VEHICLE */}
      {fuel && (
        <div className="content-panel" style={{ marginBottom: "24px" }}>
          <div className="panel-header">
            <div>
              <h2 className="panel-title">Fuel Monitoring & Powertrain Consumption Rankings</h2>
              <p style={{ fontSize: "12px", color: "#64748b" }}>Trip-based distance calculations mapped to engine fuel economy profiles</p>
            </div>
          </div>

          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Vehicle ID</th>
                  <th>Registration</th>
                  <th>Vehicle Type</th>
                  <th>Trips Completed</th>
                  <th>Total Odometer</th>
                  <th>Fuel Efficiency</th>
                  <th>Est. Fuel Burned</th>
                  <th>Est. Fuel Cost</th>
                </tr>
              </thead>
              <tbody>
                {fuel.vehicle_rankings.map((vr) => (
                  <tr key={vr.vehicle_id}>
                    <td><span className="mono-code">{vr.vehicle_id}</span></td>
                    <td><strong>{vr.registration}</strong></td>
                    <td><span className="badge">{vr.vehicle_type}</span></td>
                    <td>{vr.trips_completed} trips</td>
                    <td>{vr.total_distance_km.toLocaleString()} km</td>
                    <td>{vr.fuel_efficiency_kpl} km/L</td>
                    <td><strong style={{ color: "#f59e0b" }}>{vr.estimated_fuel_liters.toLocaleString()} L</strong></td>
                    <td><span className="mono-code">₹{vr.estimated_fuel_cost.toLocaleString()}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="methodology-box">
            {fuel.methodology}
          </div>
        </div>
      )}

      {/* CELERY ASYNCHRONOUS WORKER JOBS PANEL */}
      <div className="content-panel">
        <div className="panel-header">
          <div>
            <h2 className="panel-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span>⚡</span> Celery Background Worker Engine (Redis Broker)
            </h2>
            <p style={{ fontSize: "12px", color: "#64748b" }}>
              Asynchronous worker architecture for recurring maintenance reminders, overdue scans, and analytics aggregation
            </p>
          </div>
        </div>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "12px" }}>
          <button className="btn btn-primary" onClick={() => runCeleryTask("overdue")}>
            ⚡ Trigger Overdue Maintenance Scan
          </button>
          <button className="btn btn-secondary" onClick={() => runCeleryTask("reminders")}>
            🔔 Trigger 48h Service Reminders
          </button>
          <button className="btn btn-secondary" onClick={() => runCeleryTask("analytics")}>
            📊 Trigger Fleet Analytics Aggregation
          </button>
        </div>

        {workerResult && (
          <div className="worker-console">
            <div>&gt; {workerResult}</div>
          </div>
        )}
      </div>
    </section>
  );
}


// =========================================================
// MAIN APP COMPONENT (Shell, Navigation & Reactive State)
// =========================================================

function App() {
  const [token, setToken] = useState(localStorage.getItem("fleetflow_token"));
  const [userRole, setUserRole] = useState(localStorage.getItem("fleetflow_role") || "Administrator");
  const [page, setPage] = useState("dashboard");
  const [selectedShipmentId, setSelectedShipmentId] = useState("");

  useEffect(() => {
    function handleLogoutEvent() {
      setToken(null);
      setUserRole("");
      setPage("dashboard");
    }
    window.addEventListener("auth_logout", handleLogoutEvent);
    return () => window.removeEventListener("auth_logout", handleLogoutEvent);
  }, []);

  function handleLoginSuccess(role) {
    setToken(localStorage.getItem("fleetflow_token"));
    setUserRole(role);
    setPage("dashboard");
  }

  function handleLogout() {
    localStorage.removeItem("fleetflow_token");
    localStorage.removeItem("fleetflow_role");
    setToken(null);
    setUserRole("");
    setPage("dashboard");
  }

  if (!token) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app-container">
      {/* SIDEBAR NAVIGATION */}
      <aside className="sidebar">
        <div className="brand-section">
          <div className="brand-icon">🚛</div>
          <div>
            <div className="brand-title">FleetFlow</div>
            <div className="brand-subtitle">Logistics & Tracking</div>
          </div>
        </div>

        <div className="user-badge">
          <div className="user-info">
            <span className="user-role-label">Authenticated Role</span>
            <span className="user-role-val">{userRole}</span>
          </div>
          <span className="role-pill">M3</span>
        </div>

        <nav className="nav-links">
          <button
            className={`nav-btn ${page === "dashboard" ? "active" : ""}`}
            onClick={() => setPage("dashboard")}
          >
            <span className="nav-btn-icon">📊</span>
            Dashboard
          </button>

          <button
            className={`nav-btn ${page === "shipments" ? "active" : ""}`}
            onClick={() => setPage("shipments")}
          >
            <span className="nav-btn-icon">📦</span>
            Shipments
          </button>

          <button
            className={`nav-btn ${page === "live_tracking" ? "active" : ""}`}
            onClick={() => setPage("live_tracking")}
          >
            <span className="nav-btn-icon">📡</span>
            Live Tracking
          </button>

          <button
            className={`nav-btn ${page === "routes" ? "active" : ""}`}
            onClick={() => setPage("routes")}
          >
            <span className="nav-btn-icon">⚡</span>
            Route Optimization
          </button>

          <button
            className={`nav-btn ${page === "trips" ? "active" : ""}`}
            onClick={() => setPage("trips")}
          >
            <span className="nav-btn-icon">🗺️</span>
            Trip Scheduling
          </button>

          <button
            className={`nav-btn ${page === "vehicles" ? "active" : ""}`}
            onClick={() => setPage("vehicles")}
          >
            <span className="nav-btn-icon">🚛</span>
            Vehicles
          </button>

          <button
            className={`nav-btn ${page === "drivers" ? "active" : ""}`}
            onClick={() => setPage("drivers")}
          >
            <span className="nav-btn-icon">👤</span>
            Drivers
          </button>

          <button
            className={`nav-btn ${page === "maintenance" ? "active" : ""}`}
            onClick={() => setPage("maintenance")}
          >
            <span className="nav-btn-icon">🔧</span>
            Maintenance
          </button>

          <button
            className={`nav-btn ${page === "analytics" ? "active" : ""}`}
            onClick={() => setPage("analytics")}
          >
            <span className="nav-btn-icon">📈</span>
            Analytics &amp; Fuel
          </button>
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <span>🚪</span>
            Sign Out
          </button>
        </div>
      </aside>

      {/* MAIN VIEWPORT */}
      <main className="main-viewport">
        {page === "dashboard" && (
          <Dashboard setPage={setPage} setSelectedShipmentId={setSelectedShipmentId} />
        )}

        {page === "shipments" && (
          <Shipments
            setPage={setPage}
            setSelectedShipmentId={setSelectedShipmentId}
            userRole={userRole}
          />
        )}

        {page === "live_tracking" && (
          <LiveTracking shipmentId={selectedShipmentId} userRole={userRole} />
        )}

        {page === "routes" && (
          <RouteOptimization setPage={setPage} />
        )}

        {page === "trips" && (
          <Trips userRole={userRole} />
        )}

        {page === "vehicles" && (
          <Vehicles userRole={userRole} />
        )}

        {page === "drivers" && (
          <Drivers userRole={userRole} />
        )}

        {page === "maintenance" && (
          <Maintenance userRole={userRole} />
        )}

        {page === "analytics" && (
          <Analytics userRole={userRole} />
        )}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);