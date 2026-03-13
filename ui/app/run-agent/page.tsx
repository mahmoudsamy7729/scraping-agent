"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import styles from "./page.module.css";

type RunItem = {
  id: number;
  prompt: string;
  startedAt: string;
  response: unknown;
  error?: string;
};

const DEFAULT_API_BASE = "http://localhost:8000";

const normalizeBaseUrl = (value: string): string => value.replace(/\/+$/, "");

export default function RunAgentPage() {
  const [apiBase, setApiBase] = useState(DEFAULT_API_BASE);
  const [prompt, setPrompt] = useState("");
  const [running, setRunning] = useState(false);
  const [runs, setRuns] = useState<RunItem[]>([]);
  const [runError, setRunError] = useState<string | null>(null);

  const canRun = useMemo(() => !running && prompt.trim().length > 0, [prompt, running]);

  const onRun = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const cleanedPrompt = prompt.trim();
    if (!cleanedPrompt) {
      return;
    }

    setRunning(true);
    setRunError(null);
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

      const payload = (await response.json()) as { error?: string; response?: unknown };
      if (!response.ok) {
        throw new Error(payload.error ?? `HTTP ${response.status}`);
      }

      setRuns((prev) => [
        {
          id: Date.now(),
          prompt: cleanedPrompt,
          startedAt,
          response: payload.response ?? payload
        },
        ...prev
      ]);
      setPrompt("");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Run failed";
      setRunError(message);
      setRuns((prev) => [
        {
          id: Date.now(),
          prompt: cleanedPrompt,
          startedAt,
          response: null,
          error: message
        },
        ...prev
      ]);
    } finally {
      setRunning(false);
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.shell}>
        <header className={styles.topbar}>
          <div className={styles.titleWrap}>
            <p>Scraping Agent</p>
            <h1>Run Console</h1>
            <span>Send prompt, execute run, and inspect output in one place.</span>
          </div>
          <Link href="/" className={styles.back}>
            Back To Dashboard
          </Link>
        </header>

        <form className={styles.card} onSubmit={onRun}>
          <div className={styles.field}>
            <label htmlFor="api-base">Agent API Base URL</label>
            <input
              id="api-base"
              className={styles.input}
              value={apiBase}
              onChange={(event) => setApiBase(event.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="prompt">Prompt</label>
            <textarea
              id="prompt"
              className={styles.textarea}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Example: Find the latest electronics deals from Amazon and Noon."
            />
          </div>

          <div className={styles.actions}>
            <button type="submit" className={styles.button} disabled={!canRun}>
              {running ? "Running..." : "Run Scraping Agent"}
            </button>
          </div>
        </form>

        <section className={styles.card}>
          {runError ? <p className={`${styles.state} ${styles.error}`}>{runError}</p> : null}
          {!runError && runs.length === 0 ? <p className={styles.state}>No runs yet.</p> : null}

          <div className={styles.history}>
            {runs.map((item) => (
              <article key={item.id} className={styles.item}>
                <p>
                  <strong>Time:</strong> {new Date(item.startedAt).toLocaleString()}
                </p>
                <p>
                  <strong>Prompt:</strong> {item.prompt}
                </p>
                {item.error ? (
                  <p className={styles.error}>
                    <strong>Error:</strong> {item.error}
                  </p>
                ) : (
                  <pre className={styles.output}>{JSON.stringify(item.response, null, 2)}</pre>
                )}
              </article>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
