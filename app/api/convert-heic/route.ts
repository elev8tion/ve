import { NextRequest, NextResponse } from 'next/server';

const NCB_API = process.env.NCB_API_URL!;
const NCB_INSTANCE = process.env.NCB_INSTANCE!;
const NCB_SECRET_KEY = process.env.NCB_SECRET_KEY!;

// HEIC conversion: if the generation backend supports it, proxy there.
// Otherwise fall back to uploading the raw file and letting the backend handle it.
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const file = form.get('file') as File | null;
  if (!file) return NextResponse.json({ error: 'No file' }, { status: 400 });

  const sessionToken = process.env.GENERATION_SESSION_TOKEN;
  const apiBase = process.env.GENERATION_API_BASE;

  // Option A: proxy to generation backend's HEIC converter
  if (sessionToken && apiBase) {
    const proxyForm = new FormData();
    proxyForm.append('file', file);
    const res = await fetch(`${apiBase}/api/convert-heic`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${sessionToken}` },
      body: proxyForm,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  }

  // Option B: store raw HEIC in NCB and return the URL — backend may convert on its own
  const bytes = await file.arrayBuffer();
  const base64 = Buffer.from(bytes).toString('base64');

  const res = await fetch(`${NCB_API}/create/uploads?Instance=${NCB_INSTANCE}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${NCB_SECRET_KEY}`,
    },
    body: JSON.stringify({
      filename: file.name,
      content_type: file.type,
      data: base64,
    }),
  });

  if (!res.ok) {
    const err = await res.text();
    return NextResponse.json({ error: err }, { status: 500 });
  }

  const { id } = await res.json();
  const url = `${req.nextUrl.origin}/api/uploads/${id}`;
  return NextResponse.json({ url });
}
