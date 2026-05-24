import { NextRequest, NextResponse } from 'next/server';
import { getJob } from '@/lib/jobStore';
import type { ClipStatusResponse } from '@/lib/types';

export async function GET(req: NextRequest, { params }: { params: { id: string } }) {
  const job = getJob(params.id);

  if (!job) {
    return NextResponse.json({ error: 'Job not found' }, { status: 404 });
  }

  const response: ClipStatusResponse = {
    status: job.status,
    pipeline_step: job.pipeline_step,
    progress: job.progress,
    queue_position: null,
    output_url: job.output_url,
    preview_image_url: job.preview_image_url,
    error_message: job.error_message,
  };

  return NextResponse.json(response);
}
