import type { ClipStatus, PipelineStep } from './types';

export interface Job {
  id: string;
  status: ClipStatus;
  pipeline_step: PipelineStep | null;
  progress: number;
  output_url: string | null;
  preview_image_url: string | null;
  error_message: string | null;
  created_at: number;
  updated_at: number;
}

// Singleton in-memory store — works for solo-use Next.js dev server.
// All jobs are lost on server restart; that's acceptable for local use.
const store = new Map<string, Job>();

export function createJob(id: string): Job {
  const job: Job = {
    id,
    status: 'pending',
    pipeline_step: null,
    progress: 0,
    output_url: null,
    preview_image_url: null,
    error_message: null,
    created_at: Date.now(),
    updated_at: Date.now(),
  };
  store.set(id, job);
  return job;
}

export function getJob(id: string): Job | undefined {
  return store.get(id);
}

export function updateJob(id: string, patch: Partial<Job>): Job | undefined {
  const job = store.get(id);
  if (!job) return undefined;
  Object.assign(job, patch, { updated_at: Date.now() });
  return job;
}

export function deleteJob(id: string): void {
  store.delete(id);
}
