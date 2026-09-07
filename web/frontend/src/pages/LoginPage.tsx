import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useUser } from "../context/UserContext";

export function LoginPage() {
  const { login } = useUser();
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(name, email);
      navigate("/library");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <header className="app-header">
        <h1>Discussion Prep</h1>
        <Link to="/about" className="knowledge-graph-link">
          About
        </Link>
      </header>
      <div className="login-page">
      <form className="login-card" onSubmit={handleSubmit}>
        <h1>Sign in</h1>
        <p>
          Enter your name and MIT email to start practicing. This is a demo login (no password) — it
          will be replaced by MIT Touchstone.
        </p>
        <div className="login-field">
          <label htmlFor="name">Name</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} required autoFocus />
        </div>
        <div className="login-field">
          <label htmlFor="email">MIT email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        {error && <div className="bubble system">Error: {error}</div>}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Continue"}
        </button>
      </form>
      </div>
    </div>
  );
}
