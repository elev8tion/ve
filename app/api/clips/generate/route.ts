import { NextRequest, NextResponse } from 'next/server';
import { randomUUID } from 'crypto';
import { createJob, updateJob } from '@/lib/jobStore';
import type { GeneratePayload } from '@/lib/types';

// Pipeline runs asynchronously after we return the jobId to the client.
async function runPipeline(jobId: string, payload: GeneratePayload): Promise<void> {
  const { execFile } = await import('child_process');
  const { promisify } = await import('util');
  const { writeFile, mkdtemp, readFile, rm } = await import('fs/promises');
  const { tmpdir } = await import('os');
  const path = await import('path');
  const execFileAsync = promisify(execFile);

  const workDir = await mkdtemp(path.join(tmpdir(), `ve-${jobId}-`));

  try {
    // ── Step 1: load xAI token ──────────────────────────────────────────────
    updateJob(jobId, { pipeline_step: 'face_swap', progress: 5 });

    const NCB_API = process.env.NCB_API_URL!;
    const NCB_INSTANCE = process.env.NCB_INSTANCE!;
    const NCB_SECRET_KEY = process.env.NCB_SECRET_KEY!;

    const tokenPath =
      process.env.XAI_TOKEN_PATH ||
      path.join(process.env.HOME || '', '.xai-oauth', 'tokens.json');

    let accessToken: string;
    try {
      const raw = JSON.parse(await readFile(tokenPath, 'utf8'));
      accessToken = raw.access_token ?? raw.tokens?.access_token;
      if (!accessToken) throw new Error('access_token missing in token file');
    } catch (e: any) {
      throw new Error(`xAI token not found at ${tokenPath}. Run: cd xai-oauth-client && python -m xai_oauth login`);
    }

    const xaiHeaders = {
      Authorization: `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
    };

    // ── Step 2: generate scene image via OpenAI Codex (gpt-image-2) ────────
    updateJob(jobId, { pipeline_step: 'video_gen', progress: 15 });

    const { photoUrls, audioUrl, shotStyle, creativePrompt, customOutfitDescription } = payload;

    const scenePrompt = buildScenePrompt(shotStyle, creativePrompt, customOutfitDescription);

    // Call the Python Codex media client as a subprocess
    const codexScript = path.join(process.cwd(), 'openai-codex-client', 'generate_image_cli.py');

    const codexArgs = [
      codexScript,
      '--prompt', scenePrompt,
      '--aspect-ratio', 'portrait',
      '--quality', 'high',
    ];
    for (const url of photoUrls) {
      codexArgs.push('--reference-url', url);
    }

    let sceneImageB64: string;
    try {
      const { stdout } = await execFileAsync('python3', codexArgs, { timeout: 120_000 });
      const result = JSON.parse(stdout.trim());
      if (!result.success) throw new Error(result.error);
      sceneImageB64 = result.image_b64;
    } catch (e: any) {
      throw new Error(`Image generation failed: ${e.message}`);
    }

    // Upload scene image to NCB so xAI can reference it by URL
    const imgUploadResp = await fetch(
      `${NCB_API}/create/uploads?Instance=${NCB_INSTANCE}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-secret-key': NCB_SECRET_KEY },
        body: JSON.stringify({ file: sceneImageB64, filename: `scene_${jobId}.png`, mimetype: 'image/png' }),
      }
    );
    if (!imgUploadResp.ok) throw new Error(`Scene image NCB upload failed: ${await imgUploadResp.text()}`);
    const imgUploadData = await imgUploadResp.json();
    const sceneImgId = imgUploadData?.id ?? imgUploadData?.data?.id;
    const sceneImageUrl = `${process.env.NEXT_PUBLIC_BASE_URL || ''}/api/uploads/${sceneImgId}`;

    updateJob(jobId, { preview_image_url: sceneImageUrl, progress: 30 });

    // ── Step 3: generate video from scene image ─────────────────────────────
    updateJob(jobId, { pipeline_step: 'video_gen', progress: 35 });

    const videoGenBody: Record<string, unknown> = {
      model: 'grok-imagine-video',
      prompt: scenePrompt,
      image: sceneImageUrl,
      duration: 8,
      aspect_ratio: '9:16',
      resolution: '720p',
    };

    // xAI reference_images format: [{image: url}, ...]
    if (photoUrls.length > 0) {
      videoGenBody.reference_images = photoUrls.map((url) => ({ image: url }));
    }

    const vidResp = await fetch('https://api.x.ai/v1/videos/generations', {
      method: 'POST',
      headers: xaiHeaders,
      body: JSON.stringify(videoGenBody),
    });

    if (!vidResp.ok) {
      const err = await vidResp.text();
      throw new Error(`xAI video gen failed (${vidResp.status}): ${err}`);
    }

    const vidData = await vidResp.json();
    const requestId: string = vidData?.request_id ?? vidData?.id;
    if (!requestId) throw new Error('xAI video gen returned no request_id');

    // ── Step 4: poll for video completion ───────────────────────────────────
    updateJob(jobId, { progress: 40 });

    let rawVideoUrl: string | null = null;
    for (let i = 0; i < 120; i++) {
      await sleep(5000);
      const pollResp = await fetch(`https://api.x.ai/v1/videos/${requestId}`, {
        headers: xaiHeaders,
      });
      if (!pollResp.ok) continue;
      const pollData = await pollResp.json();
      const status: string = pollData?.status;

      if (status === 'done') {
        rawVideoUrl = pollData?.video?.url ?? null;
        break;
      }
      if (status === 'failed' || status === 'expired') {
        throw new Error(`xAI video generation ${status}: ${JSON.stringify(pollData)}`);
      }

      // progress 40→65 during polling
      const progress = Math.min(65, 40 + Math.floor((i / 120) * 25));
      updateJob(jobId, { progress });
    }

    if (!rawVideoUrl) throw new Error('xAI video generation timed out or returned no URL');

    // ── Step 5: download video locally for lip sync ────────────────────────
    updateJob(jobId, { pipeline_step: 'lip_sync', progress: 68 });

    const rawVideoPath = path.join(workDir, 'raw_video.mp4');
    await downloadFile(rawVideoUrl, rawVideoPath);

    const audioPath = path.join(workDir, 'audio.mp3');
    await downloadFile(audioUrl, audioPath);

    // ── Step 6: lip sync via LatentSync ────────────────────────────────────
    updateJob(jobId, { progress: 72 });

    const syncedVideoPath = path.join(workDir, 'synced.mp4');
    const lipsyncScript = path.join(process.cwd(), 'tools', 'latentsync.py');

    let lipsyncResult: { success: boolean; output?: string; error?: string };
    try {
      const { stdout } = await execFileAsync('python3', [
        lipsyncScript,
        '--video', rawVideoPath,
        '--audio', audioPath,
        '--output', syncedVideoPath,
        '--guidance-scale', '2.0',
        '--inference-steps', '20',
      ], { timeout: 1_800_000 }); // 30 min — LatentSync is slower but higher quality
      lipsyncResult = JSON.parse(stdout.trim());
    } catch (e: any) {
      // Fall back to ffmpeg audio merge if LatentSync isn't set up yet
      console.warn('[lipsync] LatentSync failed, falling back to ffmpeg audio merge:', e.message);
      await ffmpegAudioMerge(rawVideoPath, audioPath, syncedVideoPath);
      lipsyncResult = { success: true, output: syncedVideoPath };
    }

    if (!lipsyncResult.success) {
      console.warn('[lipsync] LatentSync reported failure, falling back to ffmpeg:', lipsyncResult.error);
      await ffmpegAudioMerge(rawVideoPath, audioPath, syncedVideoPath);
    }

    const finalVideoPath = lipsyncResult.output || syncedVideoPath;

    // ── Step 7: upload to NCB ───────────────────────────────────────────────
    updateJob(jobId, { pipeline_step: 'audio_merge', progress: 88 });

    const videoBuffer = await readFile(finalVideoPath);
    const base64Video = videoBuffer.toString('base64');

    const uploadResp = await fetch(
      `${NCB_API}/create/uploads?Instance=${NCB_INSTANCE}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-secret-key': NCB_SECRET_KEY,
        },
        body: JSON.stringify({
          file: base64Video,
          filename: `clip_${jobId}.mp4`,
          mimetype: 'video/mp4',
        }),
      }
    );

    if (!uploadResp.ok) {
      throw new Error(`NCB upload failed (${uploadResp.status}): ${await uploadResp.text()}`);
    }

    const uploadData = await uploadResp.json();
    const uploadId = uploadData?.id ?? uploadData?.data?.id;
    if (!uploadId) throw new Error('NCB upload returned no id');

    const outputUrl = `/api/uploads/${uploadId}`;

    updateJob(jobId, {
      status: 'completed',
      pipeline_step: 'done',
      progress: 100,
      output_url: outputUrl,
    });
  } catch (err: any) {
    console.error(`[pipeline:${jobId}]`, err.message);
    updateJob(jobId, {
      status: 'failed',
      error_message: err.message,
    });
  } finally {
    try {
      const { rm } = await import('fs/promises');
      await rm(workDir, { recursive: true, force: true });
    } catch {}
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function buildScenePrompt(
  shotStyle: string,
  creativePrompt?: string,
  outfitDescription?: string
): string {
  const parts = [`Music video scene: ${shotStyle}`];
  if (outfitDescription) parts.push(`Artist outfit: ${outfitDescription}`);
  if (creativePrompt) parts.push(creativePrompt);
  parts.push('Cinematic quality, professional lighting, 4K, vertical format.');
  return parts.join('. ');
}

async function downloadFile(url: string, dest: string): Promise<void> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed (${res.status}): ${url}`);
  const { writeFile } = await import('fs/promises');
  const buffer = Buffer.from(await res.arrayBuffer());
  await writeFile(dest, buffer);
}

async function ffmpegAudioMerge(
  videoPath: string,
  audioPath: string,
  outputPath: string
): Promise<void> {
  const { execFile } = await import('child_process');
  const { promisify } = await import('util');
  const execFileAsync = promisify(execFile);

  await execFileAsync('/opt/homebrew/bin/ffmpeg', [
    '-y',
    '-i', videoPath,
    '-i', audioPath,
    '-c:v', 'copy',
    '-c:a', 'aac',
    '-shortest',
    outputPath,
  ], { timeout: 120_000 });
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

// ── Route handler ──────────────────────────────────────────────────────────

export async function POST(req: NextRequest) {
  const payload: GeneratePayload = await req.json();

  const { photoUrls, audioUrl, shotStyle } = payload;
  if (!photoUrls?.length) {
    return NextResponse.json({ error: 'photoUrls required' }, { status: 400 });
  }
  if (!audioUrl) {
    return NextResponse.json({ error: 'audioUrl required' }, { status: 400 });
  }
  if (!shotStyle) {
    return NextResponse.json({ error: 'shotStyle required' }, { status: 400 });
  }

  const jobId = randomUUID();
  createJob(jobId);

  // Fire and forget — client polls /api/clips/[id]
  runPipeline(jobId, payload).catch((e) =>
    console.error(`[pipeline] uncaught error for job ${jobId}:`, e)
  );

  return NextResponse.json({ id: jobId, status: 'pending' }, { status: 202 });
}
