import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./styles.css";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fleetflow_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

function Login({ done }) {
  const [email, setEmail] = useState("admin@fleetflow.com");
  const [password, setPassword] = useState("Admin@123");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();

    try {
      const r = await api.post("/api/auth/login", {
        email,
        password
      });

      localStorage.setItem("fleetflow_token", r.data.access_token);
      localStorage.setItem("fleetflow_role", r.data.role);

      done();
    } catch (e) {
      setErr(
        e.response?.data?.detail || "Invalid email or password."
      );
    }
  }

  return (
    <div className="login">
      <form onSubmit={submit} className="loginbox">
        <h1>FleetFlow</h1>

        <p>Fleet Management & Logistics Tracking Platform</p>

        {err && <div className="error">{err}</div>}

        <label>Email</label>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <label>Password</label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        <button>Sign in</button>

        <small>
          Demo: admin@fleetflow.com / Admin@123
        </small>
      </form>
    </div>
  );
}

function Dashboard() {
  const [d, setD] = useState(null);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setError("");

    try {
      const r = await api.get("/api/dashboard/summary");
      setD(r.data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        "Unable to load dashboard data."
      );
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  if (error) {
    return (
      <section>
        <h1>Fleet Monitoring Dashboard</h1>

        <div className="error">
          {error}
        </div>

        <button onClick={loadDashboard}>
          Retry
        </button>
      </section>
    );
  }

  if (!d) {
    return (
      <section>
        <h2>Loading dashboard...</h2>
      </section>
    );
  }

  return (
    <section>
      <h1>Fleet Monitoring Dashboard</h1>

      <p className="muted">
        Milestone 1 operational overview
      </p>

      <div className="cards">
        {[
          ["Total Vehicles", d.total_vehicles],
          ["Active Vehicles", d.active_vehicles],
          ["Available Vehicles", d.available_vehicles],
          ["Maintenance", d.maintenance_vehicles],
          ["Active Drivers", d.active_drivers]
        ].map((x) => (
          <div className="card" key={x[0]}>
            <span>{x[0]}</span>
            <strong>{x[1]}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function Drivers() {
  const [rows, setRows] = useState([]);
  const [f, setF] = useState({
    driver_id: "",
    name: "",
    license_number: "",
    phone: ""
  });
  const [msg, setMsg] = useState("");

  const load = () =>
    api.get("/api/drivers").then((r) => setRows(r.data));

  useEffect(() => {
    load();
  }, []);

  async function add(e) {
    e.preventDefault();

    try {
      await api.post("/api/drivers", f);

      setF({
        driver_id: "",
        name: "",
        license_number: "",
        phone: ""
      });

      setMsg("Driver added.");
      load();
    } catch (e) {
      setMsg(
        e.response?.data?.detail || "Error"
      );
    }
  }

  return (
    <section>
      <h1>Driver Management</h1>

      <div className="grid">
        <form className="panel" onSubmit={add}>
          <h3>Register Driver</h3>

          {Object.keys(f).map((k) => (
            <input
              key={k}
              placeholder={k.replaceAll("_", " ").toUpperCase()}
              value={f[k]}
              onChange={(e) =>
                setF({
                  ...f,
                  [k]: e.target.value
                })
              }
            />
          ))}

          <button>Add Driver</button>

          <p className="muted">{msg}</p>
        </form>

        <div className="panel">
          <h3>Drivers</h3>

          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>License</th>
                <th>Phone</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((x) => (
                <tr key={x.id}>
                  <td>{x.driver_id}</td>
                  <td>{x.name}</td>
                  <td>{x.license_number}</td>
                  <td>{x.phone}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function Vehicles() {
  const [rows, setRows] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [msg, setMsg] = useState("");

  const [f, setF] = useState({
    vehicle_id: "",
    registration_number: "",
    vehicle_type: "Truck",
    capacity: "10",
    fuel_type: "Diesel",
    current_status: "Available",
    driver_id: ""
  });

  const load = () =>
    Promise.all([
      api.get("/api/vehicles"),
      api.get("/api/drivers")
    ]).then(([v, d]) => {
      setRows(v.data);
      setDrivers(d.data);
    });

  useEffect(() => {
    load();
  }, []);

  async function add(e) {
    e.preventDefault();

    try {
      await api.post("/api/vehicles", {
        ...f,
        capacity: Number(f.capacity),
        driver_id: f.driver_id
          ? Number(f.driver_id)
          : null
      });

      setMsg("Vehicle registered.");

      setF({
        ...f,
        vehicle_id: "",
        registration_number: "",
        driver_id: ""
      });

      load();
    } catch (e) {
      setMsg(
        e.response?.data?.detail || "Error"
      );
    }
  }

  return (
    <section>
      <h1>Fleet Management</h1>

      <div className="grid">
        <form className="panel" onSubmit={add}>
          <h3>Vehicle Registration</h3>

          <input
            placeholder="Vehicle ID"
            value={f.vehicle_id}
            onChange={(e) =>
              setF({
                ...f,
                vehicle_id: e.target.value
              })
            }
          />

          <input
            placeholder="Registration Number"
            value={f.registration_number}
            onChange={(e) =>
              setF({
                ...f,
                registration_number: e.target.value
              })
            }
          />

          <select
            value={f.vehicle_type}
            onChange={(e) =>
              setF({
                ...f,
                vehicle_type: e.target.value
              })
            }
          >
            <option>Truck</option>
            <option>Van</option>
            <option>Car</option>
            <option>Container Truck</option>
          </select>

          <input
            type="number"
            min="1"
            value={f.capacity}
            onChange={(e) =>
              setF({
                ...f,
                capacity: e.target.value
              })
            }
          />

          <select
            value={f.fuel_type}
            onChange={(e) =>
              setF({
                ...f,
                fuel_type: e.target.value
              })
            }
          >
            <option>Diesel</option>
            <option>Petrol</option>
            <option>Electric</option>
            <option>CNG</option>
          </select>

          <select
            value={f.current_status}
            onChange={(e) =>
              setF({
                ...f,
                current_status: e.target.value
              })
            }
          >
            <option>Available</option>
            <option>Active</option>
            <option>Maintenance</option>
          </select>

          <select
            value={f.driver_id}
            onChange={(e) =>
              setF({
                ...f,
                driver_id: e.target.value
              })
            }
          >
            <option value="">No driver</option>

            {drivers.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name} ({d.driver_id})
              </option>
            ))}
          </select>

          <button>Register Vehicle</button>

          <p className="muted">{msg}</p>
        </form>

        <div className="panel">
          <h3>Fleet Vehicles</h3>

          <table>
            <thead>
              <tr>
                <th>Vehicle</th>
                <th>Registration</th>
                <th>Type</th>
                <th>Fuel</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {rows.map((x) => (
                <tr key={x.id}>
                  <td>{x.vehicle_id}</td>
                  <td>{x.registration_number}</td>
                  <td>{x.vehicle_type}</td>
                  <td>{x.fuel_type}</td>
                  <td>
                    <span className="badge">
                      {x.current_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

function App() {
  const [ok, setOk] = useState(
    !!localStorage.getItem("fleetflow_token")
  );

  const [page, setPage] = useState("dashboard");

  if (!ok) {
    return (
      <Login
        done={() => setOk(true)}
      />
    );
  }

  function logout() {
    localStorage.clear();
    setOk(false);
  }

  return (
    <div className="app">
      <aside>
        <h2>FleetFlow</h2>

        <small>
          {localStorage.getItem("fleetflow_role")}
        </small>

        <button
          onClick={() => setPage("dashboard")}
        >
          Dashboard
        </button>

        <button
          onClick={() => setPage("vehicles")}
        >
          Vehicles
        </button>

        <button
          onClick={() => setPage("drivers")}
        >
          Drivers
        </button>

        <button
          className="logout"
          onClick={logout}
        >
          Logout
        </button>
      </aside>

      <main>
        {page === "dashboard" ? (
          <Dashboard />
        ) : page === "vehicles" ? (
          <Vehicles />
        ) : (
          <Drivers />
        )}
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(
  <App />
);