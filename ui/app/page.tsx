"use client";

import { FormEvent, useMemo, useState } from "react";

type HealthStatus = "idle" | "checking" | "online" | "offline";

type RunRecord = {
  id: number;
  prompt: string;
  startedAt: string;
  response: unknown;
  error?: string;
};

const DEFAULT_API_BASE = "http://localhost:8000";

const normalizeBaseUrl = (value: string): string => value.replace(/\/+$/, "");

export default function Home() {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [prompt, setPrompt] = useState("");
  const [health, setHealth] = useState<HealthStatus>("idle");
  const [healthMessage, setHealthMessage] = useState("Not checked yet");
  const [running, setRunning] = useState(false);
  const [history, setHistory] = useState<RunRecord[]>([]);

  const canRun = useMemo(() => !running && prompt.trim().length > 0, [running, prompt]);

  const checkHealth = async () => {
    setHealth("checking");
    setHealthMessage("Checking agent...");
    try {
      const response = await fetch(`/api/agent/health?base=${encodeURIComponent(normalizeBaseUrl(apiBase))}`);
      if (!response.ok) {
        const failed = (await response.json()) as { error?: string };
        throw new Error(failed.error ?? `HTTP ${response.status}`);
      }
      const data = (await response.json()) as { status?: string };
      setHealth("online");
      setHealthMessage(data.status ? `Agent status: ${data.status}` : "Agent is online");
    } catch (error) {
      setHealth("offline");
      setHealthMessage(error instanceof Error ? error.message : "Health check failed");
    }
  };

  const onRunAgent = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedPrompt = prompt.trim();
    if (!cleanedPrompt) {
      return;
    }

    setRunning(true);
    const startedAt = new Date().toISOString();

    try {
      const response = await fetch("/api/agent/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          prompt: cleanedPrompt,
          base: normalizeBaseUrl(apiBase)
        })
      });
      if (!response.ok) {
        const failed = (await response.json()) as { error?: string };
        throw new Error(failed.error ?? `HTTP ${response.status}`);
      }
      const data = (await response.json()) as { response?: unknown };
      setHistory((prev) => [
        {
          id: Date.now(),
          prompt: cleanedPrompt,
          startedAt,
          response: data.response ?? data
        },
        ...prev
      ]);
      setPrompt("");
    } catch (error) {
      setHistory((prev) => [
        {
          id: Date.now(),
          prompt: cleanedPrompt,
          startedAt,
          response: null,
          error: error instanceof Error ? error.message : "Request failed"
        },
        ...prev
      ]);
    } finally {
      setRunning(false);
    }
  };

  return (
    <main className="page">
      <section className="container">
        <header className="header">
          <p className="eyebrow">Deals Scraping Agent</p>
          <h1>Management Dashboard</h1>
          <p className="subtitle">Run prompts, track responses, and monitor API health from one place.</p>
        </header>

        <div className="card">
          <label htmlFor="api-base" className="label">
            Agent API Base URL
          </label>
          <div className="row">
            <input
              id="api-base"
              className="input"
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="http://localhost:8000"
            />
            <button type="button" className="button secondary" onClick={checkHealth} disabled={health === "checking"}>
              {health === "checking" ? "Checking..." : "Check Health"}
            </button>
          </div>
          <p className={`status ${health}`}>{healthMessage}</p>
        </div>

        <form className="card" onSubmit={onRunAgent}>
          <label htmlFor="prompt" className="label">
            Prompt
          </label>
          <textarea
            id="prompt"
            className="textarea"
            rows={5}
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            placeholder="Example: Find latest laptop deals from Amazon and Noon."
          />
          <div className="actions">
            <button type="submit" className="button" disabled={!canRun}>
              {running ? "Running..." : "Run Agent"}
            </button>
          </div>
        </form>

        <section className="card">
          <h2>Run History</h2>
          {history.length === 0 ? (
            <p className="muted">No runs yet.</p>
          ) : (
            <div className="history">
              {history.map((item) => (
                <article className="historyItem" key={item.id}>
                  <p>
                    <strong>Time:</strong> {new Date(item.startedAt).toLocaleString()}
                  </p>
                  <p>
                    <strong>Prompt:</strong> {item.prompt}
                  </p>
                  {item.error ? (
                    <p className="error">
                      <strong>Error:</strong> {item.error}
                    </p>
                  ) : (
                    <pre className="response">{JSON.stringify(item.response, null, 2)}</pre>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
