import { NextResponse } from "next/server";
import { getAgentBaseUrl } from "@/lib/agentApi";

type RunPayload = {
  prompt?: string;
  base?: string;
};

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as RunPayload;
    const prompt = body.prompt?.trim();
    if (!prompt) {
      return NextResponse.json({ error: "prompt is required" }, { status: 400 });
    }

    const base = getAgentBaseUrl(body.base);
    const endpoint = `${base}/api/scrapling-agent/run-agent?prompt=${encodeURIComponent(prompt)}`;
    const response = await fetch(endpoint, { method: "POST" });
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Failed to run agent"
      },
      { status: 500 }
    );
  }
}
