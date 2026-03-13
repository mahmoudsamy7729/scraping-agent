import { NextResponse } from "next/server";
import { getAgentBaseUrl } from "@/lib/agentApi";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const base = getAgentBaseUrl(searchParams.get("base"));
    const response = await fetch(`${base}/api/agents`, {
      cache: "no-store"
    });
    const payload = await response.json();
    return NextResponse.json(payload, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : "Failed to load agents"
      },
      { status: 500 }
    );
  }
}
