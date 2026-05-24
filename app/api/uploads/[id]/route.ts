import { NextRequest, NextResponse } from 'next/server';

const NCB_API = process.env.NCB_API_URL!;
const NCB_INSTANCE = process.env.NCB_INSTANCE!;
const NCB_SECRET_KEY = process.env.NCB_SECRET_KEY!;

export async function GET(_req: NextRequest, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  const res = await fetch(`${NCB_API}/read/uploads/${id}?Instance=${NCB_INSTANCE}`, {
    headers: { Authorization: `Bearer ${NCB_SECRET_KEY}` },
  });

  if (!res.ok) return new NextResponse('Not found', { status: 404 });

  const { data } = await res.json();
  if (!data) return new NextResponse('Not found', { status: 404 });

  const binary = Buffer.from(data.data, 'base64');
  return new NextResponse(binary, {
    headers: {
      'Content-Type': data.content_type || 'application/octet-stream',
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  });
}
