import { Route, Routes } from "react-router-dom";
import { Nav } from "./components/Nav";
import { Dashboard } from "./pages/Dashboard";
import { EscalationPolicies } from "./pages/EscalationPolicies";
import { IncidentDetail } from "./pages/IncidentDetail";
import { Metrics } from "./pages/Metrics";

export function App() {
  return (
    <div className="app">
      <Nav />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents/:id" element={<IncidentDetail />} />
          <Route path="/escalation-policies" element={<EscalationPolicies />} />
          <Route path="/metrics" element={<Metrics />} />
        </Routes>
      </main>
    </div>
  );
}
