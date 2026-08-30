import { NavLink } from "react-router-dom";

export function Nav() {
  return (
    <nav className="nav">
      <div className="nav__brand">Incident Response</div>
      <div className="nav__links">
        <NavLink to="/" end className={({ isActive }) => (isActive ? "nav__link nav__link--active" : "nav__link")}>
          Incidents
        </NavLink>
        <NavLink
          to="/escalation-policies"
          className={({ isActive }) => (isActive ? "nav__link nav__link--active" : "nav__link")}
        >
          Escalation Policies
        </NavLink>
        <NavLink to="/metrics" className={({ isActive }) => (isActive ? "nav__link nav__link--active" : "nav__link")}>
          Metrics
        </NavLink>
      </div>
    </nav>
  );
}
