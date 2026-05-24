import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const sessionToken = process.env.GENERATION_SESSION_TOKEN;
  const apiBase = process.env.GENERATION_API_BASE;

  if (sessionToken && apiBase) {
    const body = await req.json();
    const res = await fetch(`${apiBase}/api/audio/youtube`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${sessionToken}`,
      },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  }

  return NextResponse.json({ error: 'Backend not configured' }, { status: 501 });
}
