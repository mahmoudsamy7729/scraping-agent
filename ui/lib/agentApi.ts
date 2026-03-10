const DEFAULT_AGENT_BASE = "http://127.0.0.1:8000";

export const getAgentBaseUrl = (input?: string | null): string => {
  const raw = (input && input.trim()) || process.env.AGENT_API_BASE_URL || DEFAULT_AGENT_BASE;
  const url = new URL(raw);
  return url.toString().replace(/\/+$/, "");
};
