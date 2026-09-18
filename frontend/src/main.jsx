import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import axios from "axios";
import "./styles.css";

// ========================================
// API CONFIGURATION
// ========================================

const API_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://fleetflow-api-p7ai.onrender.com";

const api = axios.create({
  baseURL: API_URL
});

// Automatically send JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("fleetflow_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});


// ========================================
// LOGIN
// ========================================

function Login({ done }) {
  const [email, setEmail] = useState("admin@fleetflow.com");
  const [password, setPassword] = useState("Admin@123");
  const [err, setErr] = useState("");

  async function submit(e) {
    e.preventDefault();
    setErr("");

    try {
      const response = await api.post("/api/auth/login", {
        email,
        password
      });

      localStorage.setItem(
        "fleetflow_token",
        response.data.access_token
      );

      localStorage.setItem(
        "fleetflow_role",
        response.data.role
      );

      done();
    } catch (error) {
      setErr(
        error.response?.data?.detail ||
          "Unable to login. Please try again."
      );
    }
  }

  return (
    <div className="login">
      <form className="loginbox" onSubmit={submit}>
        <h1>FleetFlow</h1>

        <p>
          Fleet Management & Logistics Tracking Platform
        </p>

        {err && (
          <div className="error">
            {err}
          </div>
        )}

        <label>Email</label>

        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Enter email"
          required
        />

        <label>Password</label>

        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Enter password"
          required
        />

        <button type="submit">
          Sign in
        </button>

        <small>
          Demo: admin@fleetflow.com / Admin@123
        </small>
      </form>
    </div>
  );
}


// ========================================
// DASHBOARD
// ========================================

function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function loadDashboard() {
    try {
      setError("");

      const response = await api.get(
        "/api/dashboard/summary"
      );

      setData(response.data);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load dashboard."
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

  if (!data) {
    return (
      <section>
        <h1>Fleet Monitoring Dashboard</h1>

        <h2>Loading...</h2>
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

        <div className="card">
          <span>Total Vehicles</span>
          <strong>
            {data.total_vehicles}
          </strong>
        </div>

        <div className="card">
          <span>Active Vehicles</span>
          <strong>
            {data.active_vehicles}
          </strong>
        </div>

        <div className="card">
          <span>Available Vehicles</span>
          <strong>
            {data.available_vehicles}
          </strong>
        </div>

        <div className="card">
          <span>Maintenance</span>
          <strong>
            {data.maintenance_vehicles}
          </strong>
        </div>

        <div className="card">
          <span>Active Drivers</span>
          <strong>
            {data.active_drivers}
          </strong>
        </div>

      </div>
    </section>
  );
}


// ========================================
// DRIVERS
// ========================================

function Drivers() {
  const [drivers, setDrivers] = useState([]);

  const [form, setForm] = useState({
    driver_id: "",
    name: "",
    license_number: "",
    phone: ""
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadDrivers() {
    try {
      setError("");

      const response = await api.get(
        "/api/drivers"
      );

      setDrivers(response.data);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load drivers."
      );
    }
  }

  useEffect(() => {
    loadDrivers();
  }, []);

  function handleChange(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  }

  async function addDriver(e) {
    e.preventDefault();

    try {
      setMessage("");
      setError("");

      await api.post("/api/drivers", form);

      setForm({
        driver_id: "",
        name: "",
        license_number: "",
        phone: ""
      });

      setMessage("Driver added successfully.");

      await loadDrivers();
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to add driver."
      );
    }
  }

  return (
    <section>
      <h1>Driver Management</h1>

      <div className="grid">

        <form
          className="panel"
          onSubmit={addDriver}
        >
          <h3>Register Driver</h3>

          <input
            name="driver_id"
            placeholder="DRIVER ID"
            value={form.driver_id}
            onChange={handleChange}
            required
          />

          <input
            name="name"
            placeholder="NAME"
            value={form.name}
            onChange={handleChange}
            required
          />

          <input
            name="license_number"
            placeholder="LICENSE NUMBER"
            value={form.license_number}
            onChange={handleChange}
            required
          />

          <input
            name="phone"
            placeholder="PHONE"
            value={form.phone}
            onChange={handleChange}
            required
          />

          <button type="submit">
            Add Driver
          </button>

          {message && (
            <p className="muted">
              {message}
            </p>
          )}

          {error && (
            <div className="error">
              {error}
            </div>
          )}
        </form>


        <div className="panel">
          <h3>Drivers</h3>

          {error && (
            <div className="error">
              {error}
            </div>
          )}

          <button onClick={loadDrivers}>
            Refresh
          </button>

          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>License</th>
                <th>Phone</th>
                <th>Attendance</th>
                <th>Performance</th>
              </tr>
            </thead>

            <tbody>
              {drivers.map((driver) => (
                <tr key={driver.id}>
                  <td>
                    {driver.driver_id}
                  </td>

                  <td>
                    {driver.name}
                  </td>

                  <td>
                    {driver.license_number}
                  </td>

                  <td>
                    {driver.phone}
                  </td>

                  <td>
                    {driver.attendance}%
                  </td>

                  <td>
                    {driver.performance}
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


// ========================================
// VEHICLES
// ========================================

function Vehicles() {
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);

  const [form, setForm] = useState({
    vehicle_id: "",
    registration_number: "",
    vehicle_type: "Truck",
    capacity: "10",
    fuel_type: "Diesel",
    current_status: "Available",
    driver_id: ""
  });

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function loadVehicles() {
    try {
      setError("");

      const [vehiclesResponse, driversResponse] =
        await Promise.all([
          api.get("/api/vehicles"),
          api.get("/api/drivers")
        ]);

      setVehicles(vehiclesResponse.data);
      setDrivers(driversResponse.data);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load vehicles."
      );
    }
  }

  useEffect(() => {
    loadVehicles();
  }, []);

  function handleChange(e) {
    setForm({
      ...form,
      [e.target.name]: e.target.value
    });
  }

  async function addVehicle(e) {
    e.preventDefault();

    try {
      setMessage("");
      setError("");

      await api.post("/api/vehicles", {
        vehicle_id: form.vehicle_id,
        registration_number:
          form.registration_number,
        vehicle_type: form.vehicle_type,
        capacity: Number(form.capacity),
        fuel_type: form.fuel_type,
        current_status: form.current_status,
        driver_id: form.driver_id
          ? Number(form.driver_id)
          : null
      });

      setMessage(
        "Vehicle registered successfully."
      );

      setForm({
        vehicle_id: "",
        registration_number: "",
        vehicle_type: "Truck",
        capacity: "10",
        fuel_type: "Diesel",
        current_status: "Available",
        driver_id: ""
      });

      await loadVehicles();
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to register vehicle."
      );
    }
  }

  return (
    <section>
      <h1>Fleet Management</h1>

      <div className="grid">

        <form
          className="panel"
          onSubmit={addVehicle}
        >
          <h3>Vehicle Registration</h3>

          <input
            name="vehicle_id"
            placeholder="VEHICLE ID"
            value={form.vehicle_id}
            onChange={handleChange}
            required
          />

          <input
            name="registration_number"
            placeholder="REGISTRATION NUMBER"
            value={form.registration_number}
            onChange={handleChange}
            required
          />

          <select
            name="vehicle_type"
            value={form.vehicle_type}
            onChange={handleChange}
          >
            <option>Truck</option>
            <option>Van</option>
            <option>Car</option>
            <option>Container Truck</option>
          </select>

          <input
            name="capacity"
            type="number"
            min="1"
            placeholder="CAPACITY"
            value={form.capacity}
            onChange={handleChange}
            required
          />

          <select
            name="fuel_type"
            value={form.fuel_type}
            onChange={handleChange}
          >
            <option>Diesel</option>
            <option>Petrol</option>
            <option>Electric</option>
            <option>CNG</option>
          </select>

          <select
            name="current_status"
            value={form.current_status}
            onChange={handleChange}
          >
            <option>Available</option>
            <option>Active</option>
            <option>Maintenance</option>
          </select>

          <select
            name="driver_id"
            value={form.driver_id}
            onChange={handleChange}
          >
            <option value="">
              No driver
            </option>

            {drivers.map((driver) => (
              <option
                key={driver.id}
                value={driver.id}
              >
                {driver.name} (
                {driver.driver_id})
              </option>
            ))}
          </select>

          <button type="submit">
            Register Vehicle
          </button>

          {message && (
            <p className="muted">
              {message}
            </p>
          )}

          {error && (
            <div className="error">
              {error}
            </div>
          )}
        </form>


        <div className="panel">
          <h3>Fleet Vehicles</h3>

          <button onClick={loadVehicles}>
            Refresh
          </button>

          <table>
            <thead>
              <tr>
                <th>Vehicle</th>
                <th>Registration</th>
                <th>Type</th>
                <th>Capacity</th>
                <th>Fuel</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {vehicles.map((vehicle) => (
                <tr key={vehicle.id}>
                  <td>
                    {vehicle.vehicle_id}
                  </td>

                  <td>
                    {vehicle.registration_number}
                  </td>

                  <td>
                    {vehicle.vehicle_type}
                  </td>

                  <td>
                    {vehicle.capacity}
                  </td>

                  <td>
                    {vehicle.fuel_type}
                  </td>

                  <td>
                    <span className="badge">
                      {vehicle.current_status}
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


// ========================================
// MAIN APP
// ========================================

function App() {
  const [loggedIn, setLoggedIn] = useState(
    Boolean(
      localStorage.getItem(
        "fleetflow_token"
      )
    )
  );

  const [page, setPage] =
    useState("dashboard");

  if (!loggedIn) {
    return (
      <Login
        done={() => setLoggedIn(true)}
      />
    );
  }

  function logout() {
    localStorage.removeItem(
      "fleetflow_token"
    );

    localStorage.removeItem(
      "fleetflow_role"
    );

    setLoggedIn(false);
    setPage("dashboard");
  }

  return (
    <div className="app">

      <aside>
        <h2>FleetFlow</h2>

        <small>
          {localStorage.getItem(
            "fleetflow_role"
          )}
        </small>

        <button
          className={
            page === "dashboard"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("dashboard")
          }
        >
          Dashboard
        </button>

        <button
          className={
            page === "vehicles"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("vehicles")
          }
        >
          Vehicles
        </button>

        <button
          className={
            page === "drivers"
              ? "active"
              : ""
          }
          onClick={() =>
            setPage("drivers")
          }
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

        {page === "dashboard" && (
          <Dashboard />
        )}

        {page === "vehicles" && (
          <Vehicles />
        )}

        {page === "drivers" && (
          <Drivers />
        )}

      </main>

    </div>
  );
}


// ========================================
// START REACT APPLICATION
// ========================================

createRoot(
  document.getElementById("root")
).render(
  <App />
);