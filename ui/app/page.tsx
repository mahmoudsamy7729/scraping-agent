 "use client";

import { useEffect, useMemo, useState } from "react";

type AgentStatus = "Active" | "Idle" | "Paused" | "Error";

type Agent = {
  id: string;
  icon: string;
  slug: string;
  model: string;
  status: AgentStatus;
  description?: string;
  lastSeenAt?: string;
  updatedAt: string;
};

type ApiAgent = {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  model: string;
  status: string;
  last_seen_at: string | null;
  updated_at: string;
};

const activity = [
  "FORGE deployed auth-service v2.1.0 to staging",
  "NEXUS delegated data validation to SENTINEL",
  "SENTINEL schema validation failed: missing field user_role",
  "SCOUT initiated market data collection for Q1 2026",
  "NEXUS re-prioritized pipeline: security audit -> deployment"
];

const throughputPath =
  "M0,140 C30,110 55,85 85,125 C115,165 145,85 175,76 C205,67 235,130 265,87 C295,44 325,90 355,65 C385,40 415,55 445,90 C475,125 505,92 535,38";

const statusClassMap: Record<AgentStatus, string> = {
  Active: "isActive",
  Idle: "isIdle",
  Paused: "isPaused",
  Error: "isError"
};

const statusFromApi = (value: string): AgentStatus => {
  const normalized = value.trim().toLowerCase();
  if (["active", "online", "running", "healthy"].includes(normalized)) {
    return "Active";
  }
  if (["paused", "stopped"].includes(normalized)) {
    return "Paused";
  }
  if (["error", "failed", "offline", "down"].includes(normalized)) {
    return "Error";
  }
  return "Idle";
};

const formatDate = (value?: string): string => {
  if (!value) {
    return "N/A";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "N/A";
  }
  return date.toLocaleString();
};

export default function Home() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [agentsLoading, setAgentsLoading] = useState(true);
  const [agentsError, setAgentsError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadAgents = async () => {
      setAgentsLoading(true);
      setAgentsError(null);
      try {
        const response = await fetch("/api/agents", { cache: "no-store" });
        const payload = (await response.json()) as ApiAgent[] | { error?: string };
        if (!response.ok) {
          throw new Error(
            typeof payload === "object" && !Array.isArray(payload) ? payload.error ?? "Failed to load agents" : "Failed to load agents"
          );
        }

        const mapped = (payload as ApiAgent[]).map((agent) => ({
          id: agent.name,
          icon: agent.slug.slice(0, 2).toUpperCase(),
          slug: agent.slug,
          model: agent.model,
          status: statusFromApi(agent.status),
          description: agent.description ?? undefined,
          lastSeenAt: agent.last_seen_at ?? undefined,
          updatedAt: agent.updated_at
        }));

        if (!cancelled) {
          setAgents(mapped);
        }
      } catch (error) {
        if (!cancelled) {
          setAgentsError(error instanceof Error ? error.message : "Failed to load agents");
          setAgents([]);
        }
      } finally {
        if (!cancelled) {
          setAgentsLoading(false);
        }
      }
    };

    void loadAgents();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeCount = useMemo(
    () => agents.filter((agent) => agent.status === "Active").length,
    [agents]
  );

  const kpis = useMemo(
    () => [
      { label: "Total Tasks", value: "6,165", hint: "Today" },
      { label: "Active Agents", value: agentsLoading ? "--/--" : `${activeCount}/${agents.length}`, hint: "Running now" },
      { label: "Avg Response", value: "1.2s", hint: "Last 50 jobs" },
      { label: "Success Rate", value: "97.3%", hint: "24h window" }
    ],
    [activeCount, agents.length, agentsLoading]
  );

  return (
    <main className="dashboardPage">
      <div className="gridBackdrop" aria-hidden="true" />

      <section className="shell">
        <header className="topBar">
          <div>
            <p className="eyebrow">Agent Command Center</p>
            <h1>Agents Dashboard</h1>
            <p className="subtitle">Multi-agent orchestration and monitoring</p>
          </div>
          <span className="systemBadge">System Online</span>
        </header>

        <section className="kpiGrid">
          {kpis.map((kpi) => (
            <article className="kpiCard" key={kpi.label}>
              <p>{kpi.label}</p>
              <h2>{kpi.value}</h2>
              <span>{kpi.hint}</span>
            </article>
          ))}
        </section>

        <section className="mainBoard">
          <div className="leftStack">
            <div className="sectionHeader">
              <h3>Agents</h3>
              <span>
                {agentsLoading ? "Loading..." : `${activeCount} active`}
              </span>
            </div>

            <div className="agentGrid">
              {agentsLoading ? <p className="agentsState">Loading agents...</p> : null}
              {agentsError ? <p className="agentsState agentsError">{agentsError}</p> : null}
              {!agentsLoading && !agentsError && agents.length === 0 ? (
                <p className="agentsState">No agents found.</p>
              ) : null}

              {!agentsLoading && !agentsError
                ? agents.map((agent) => (
                    <article key={agent.id} className={`agentCard ${statusClassMap[agent.status]}`}>
                      <div className="agentHeader">
                        <div>
                          <p className="agentName">
                            <span aria-hidden="true">{agent.icon}</span> {agent.id}
                          </p>
                          <p className="agentRole">{agent.model}</p>
                        </div>
                        <span className="agentStatus">{agent.status}</span>
                      </div>

                      <div className="metaGrid">
                        <p>
                          <strong>{agent.slug}</strong>
                          <span>Slug</span>
                        </p>
                        <p>
                          <strong>{agent.model}</strong>
                          <span>Model</span>
                        </p>
                        <p>
                          <strong>{formatDate(agent.lastSeenAt)}</strong>
                          <span>Last Seen</span>
                        </p>
                        <p>
                          <strong>{formatDate(agent.updatedAt)}</strong>
                          <span>Updated At</span>
                        </p>
                      </div>

                      <p className="noTask">{agent.description ?? "No description available"}</p>
                    </article>
                  ))
                : null}
            </div>
          </div>

          <aside className="rightStack">
            <article className="sideCard">
              <h3>Network Topology</h3>
              <div className="topology">
                <div className="node nexus">NEXUS</div>
                <div className="node scout">SCOUT</div>
                <div className="node architect">ARCHITECT</div>
                <div className="node forge">FORGE</div>
                <div className="node sentinel">SENTINEL</div>
              </div>
            </article>

            <article className="sideCard">
              <h3>Task Throughput</h3>
              <svg viewBox="0 0 540 180" role="img" aria-label="Task throughput">
                <path d={throughputPath} className="throughputLine" />
              </svg>
            </article>
          </aside>
        </section>

        <section className="activityCard">
          <h3>Activity Feed</h3>
          <ul>
            {activity.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </section>
      </section>
    </main>
  );
}
