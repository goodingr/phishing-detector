import React, { useMemo, useState } from 'react';
import './App.css';

type AnalyzeResponse = {
  verdict: 'safe' | 'phishing';
  probability: number;
  signals: string[];
};

const API_BASE = (process.env.REACT_APP_API_BASE || 'http://localhost:8000').replace(
  /\/$/,
  ''
);
const ANALYZE_ENDPOINT = `${API_BASE}/api/analyze`;

const initialForm = {
  subject: '',
  body: '',
  raw: '',
};

function App() {
  const [formData, setFormData] = useState(initialForm);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);

  const hasInput = useMemo(() => {
    return Object.values(formData).some((value) => value.trim().length > 0);
  }, [formData]);

  const handleChange = (
    event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!hasInput) {
      setError('Add a subject, body, or raw email text before analyzing.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(ANALYZE_ENDPOINT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || 'Failed to analyze email.');
      }

      const payload: AnalyzeResponse = await response.json();
      setResult(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unexpected error.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData(initialForm);
    setError(null);
    setResult(null);
  };

  const verdictLabel =
    result?.verdict === 'phishing' ? 'Potential Phishing' : 'Likely Safe';

  return (
    <div className="app-shell">
      <header>
        <h1>Phishing Email Analyzer</h1>
        <p>
          Paste suspicious messages below to receive a quick, model-backed risk assessment. We
          never store your text.
        </p>
      </header>

      <main>
        <form className="analyze-form" onSubmit={handleSubmit}>
          <label>
            Subject
            <input
              type="text"
              name="subject"
              value={formData.subject}
              onChange={handleChange}
              placeholder="e.g., Action required: verify your account"
            />
          </label>

          <label>
            Body
            <textarea
              name="body"
              value={formData.body}
              onChange={handleChange}
              rows={8}
              placeholder="Paste the email body or message content..."
            />
          </label>

          <label>
            Raw Email (optional)
            <textarea
              name="raw"
              value={formData.raw}
              onChange={handleChange}
              rows={6}
              placeholder="Headers, formatting, or the entire raw email if available."
            />
          </label>

          <div className="form-actions">
            <button type="submit" disabled={loading || !hasInput}>
              {loading ? 'Analyzing…' : 'Analyze Email'}
            </button>
            <button type="button" className="secondary" onClick={handleReset}>
              Clear All
            </button>
          </div>
        </form>

        <section className="results-section" aria-live="polite">
          {error && <div className="alert error">{error}</div>}

          {!error && !result && (
            <div className="placeholder">Results will appear here after you analyze an email.</div>
          )}

          {result && (
            <div className={`result-card ${result.verdict}`}>
              <h2>{verdictLabel}</h2>
              <p className="probability">Confidence: {(result.probability * 100).toFixed(1)}%</p>
              <ul>
                {result.signals.map((signal, index) => (
                  <li key={index}>{signal}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>

      <footer>
        <small>
          This tool provides heuristic guidance only. Always follow your organization's security
          policies before acting on an email.
        </small>
      </footer>
    </div>
  );
}

export default App;
