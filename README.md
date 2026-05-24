# Music Video Generator — Personal Scaffold

Extracted from VisualEssential's production bundles and rebuilt as a solo-use Next.js app.
No auth, no credits, no billing — just the generation flow.

## Stack
- **Next.js 14.2.35** App Router
- **TypeScript**
- **Tailwind CSS 3.4.19**
- **Framer Motion 11**
- **Supabase** (storage only — photos + audio uploads)

## Setup

```bash
cp .env.local.example .env.local
# Fill in your env vars (see below)

npm install
npm run dev
```

Open http://localhost:3000

## Environment Variables

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public anon key |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-side uploads (never exposed to client) |
| `GENERATION_API_BASE` | Base URL of your generation backend (e.g. `https://www.visualessential.com`) |
| `GENERATION_SESSION_TOKEN` | Bearer token for generation API calls |

## Pages

| Route | Description |
|---|---|
| `/` | Homepage — hero, before/after compare, popular scenes, FAQ |
| `/shots` | Browse all 101 scenes with search + tag filter |
| `/create` | Full 6-step generation flow |
| `/create?scene={id}` | Pre-select a scene and jump straight to the flow |

## Create Flow Steps

1. **Photos** — Drag-drop up to 5 selfies, uploaded to Supabase storage
2. **Audio** — Upload MP3/WAV or paste a YouTube URL
3. **Scene** — Pick from 101 scenes (searchable)
4. **Outfit** — Optional: 43 tops, 42 bottoms, 40 shoes, 21 hats; 3 presets
5. **Lyrics** — Optional overlay with 15 fonts, position, case, blend mode
6. **Generate** — Submits job, polls every 5s up to 15 min, shows progress per pipeline step

## API Routes

| Route | Description |
|---|---|
| `POST /api/clips/generate` | Submit generation job — proxies to `GENERATION_API_BASE` |
| `GET /api/clips/[id]` | Poll clip status |
| `POST /api/upload` | Upload photo/audio to Supabase storage |
| `POST /api/audio/youtube` | Fetch audio from YouTube URL |

## Supabase Storage Setup

Create these buckets in your Supabase project (public read):
- `photos` — uploaded selfies
- `audio` — uploaded audio files

Or update `app/api/upload/route.ts` to use a single bucket with path prefixes.

## AI Generation Backend

The `POST /api/clips/generate` route is a proxy stub. Two options:

**Option A — Proxy** (easiest): set `GENERATION_API_BASE` and `GENERATION_SESSION_TOKEN`
to a working VisualEssential session. The route forwards the request verbatim.

**Option B — DIY**: implement the generation pipeline in `app/api/clips/generate/route.ts`
using Kling AI for video generation and Google Gemini for scene image generation.
The payload schema and pipeline steps are documented in `17-ai-generation-pipeline` in the toolchest.

## What Was Left Out

- Auth (login, signup, session management)
- Credits and billing (Stripe, plan tiers)
- Affiliate tracking (PromoteKit)
- Analytics (GA4, Meta Pixel)
- Admin pages
- Clip history / dashboard
- Blog

## Data Sources (from toolchest)

- `lib/data/shots.ts` — All 101 scenes with real Supabase CDN thumbnail URLs and AI prompts
- `lib/data/outfits.ts` — 146 outfit items with real Supabase CDN image URLs and AI descriptions
- `lib/data/lyrics.ts` — 15 font options and config types
