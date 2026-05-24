'use client';
import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Home, Clapperboard, Wand2, Upload, X, Check, ChevronLeft, ChevronRight, Search, Music, Shirt, Type, Sparkles, Download } from 'lucide-react';
import dynamic from 'next/dynamic';
import { FloatingNav } from '@/components/FloatingNav';
import { SHOTS } from '@/lib/data/shots';
import { ALL_ITEMS, buildOutfitDescription, OUTFIT_PRESETS, getOutfitThumbnailUrl } from '@/lib/data/outfits';
import { LYRICS_FONTS, DEFAULT_LYRICS_CONFIG, applyLyricsCase } from '@/lib/data/lyrics';
import type { ClipStatus, ClipStatusResponse, OutfitSelection } from '@/lib/types';

const PhonePreview = dynamic(() => import('@/components/PhonePreview').then(m => ({ default: m.PhonePreview })), { ssr: false });

const NAV_ITEMS = [
  { name: 'Home', url: '/', icon: Home },
  { name: 'Shots', url: '/shots', icon: Clapperboard },
  { name: 'Create', url: '/create', icon: Wand2 },
];

type Step = 'photos' | 'audio' | 'scene' | 'outfit' | 'lyrics' | 'generate';
const STEPS: Step[] = ['photos', 'audio', 'scene', 'outfit', 'lyrics', 'generate'];
const STEP_LABELS: Record<Step, string> = {
  photos: 'Photos', audio: 'Audio', scene: 'Scene',
  outfit: 'Outfit', lyrics: 'Lyrics', generate: 'Generate',
};
const STEP_ICONS: Record<Step, React.ReactNode> = {
  photos: <Upload size={16} />, audio: <Music size={16} />, scene: <Clapperboard size={16} />,
  outfit: <Shirt size={16} />, lyrics: <Type size={16} />, generate: <Sparkles size={16} />,
};

const PIPELINE_LABELS: Record<string, string> = {
  face_swap: 'Matching your face',
  video_gen: 'Generating scene',
  lip_sync: 'Syncing lips',
  bg_composite: 'Compositing background',
  audio_merge: 'Merging audio',
  done: 'Done',
};

function CreatePageInner() {
  const searchParams = useSearchParams();
  const initialScene = searchParams.get('scene') || '';

  const [step, setStep] = useState<Step>('photos');
  const [photoFiles, setPhotoFiles] = useState<File[]>([]);
  const [photoUrls, setPhotoUrls] = useState<string[]>([]);
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [audioUrl, setAudioUrl] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [audioMode, setAudioMode] = useState<'upload' | 'youtube'>('upload');
  const [selectedScene, setSelectedScene] = useState(initialScene);
  const [sceneQuery, setSceneQuery] = useState('');
  const [outfit, setOutfit] = useState<OutfitSelection>({});
  const [outfitTab, setOutfitTab] = useState<'tops' | 'bottoms' | 'shoes' | 'hats'>('tops');
  const [lyricsConfig, setLyricsConfig] = useState(DEFAULT_LYRICS_CONFIG);
  const [includeLyrics, setIncludeLyrics] = useState(false);
  const [creativePrompt, setCreativePrompt] = useState('');
  const [uploading, setUploading] = useState(false);
  const [clipId, setClipId] = useState<string | null>(null);
  const [clipStatus, setClipStatus] = useState<ClipStatusResponse | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const pollCount = useRef(0);

  const activeScene = SHOTS.find(s => s.id === selectedScene);
  const filteredScenes = sceneQuery
    ? SHOTS.filter(s => s.name.toLowerCase().includes(sceneQuery.toLowerCase()) || s.keywords.some(k => k.includes(sceneQuery.toLowerCase())))
    : SHOTS;

  // Draft persistence
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem('ve_draft');
      if (saved) {
        const d = JSON.parse(saved);
        if (d.selectedScene) setSelectedScene(d.selectedScene);
        if (d.outfit) setOutfit(d.outfit);
        if (d.lyricsConfig) setLyricsConfig(d.lyricsConfig);
        if (d.includeLyrics !== undefined) setIncludeLyrics(d.includeLyrics);
        if (d.creativePrompt) setCreativePrompt(d.creativePrompt);
      }
    } catch {}
  }, []);

  useEffect(() => {
    try {
      sessionStorage.setItem('ve_draft', JSON.stringify({ selectedScene, outfit, lyricsConfig, includeLyrics, creativePrompt }));
    } catch {}
  }, [selectedScene, outfit, lyricsConfig, includeLyrics, creativePrompt]);

  // Photo upload
  const handlePhotoDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    setPhotoFiles(prev => [...prev, ...files].slice(0, 5));
  }, []);

  const handlePhotoInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const files = Array.from(e.target.files).filter(f => f.type.startsWith('image/'));
    setPhotoFiles(prev => [...prev, ...files].slice(0, 5));
  };

  const uploadPhotos = async (): Promise<string[]> => {
    const urls: string[] = [];
    for (const file of photoFiles) {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/upload', { method: 'POST', body: form });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Upload failed');
      urls.push(data.url);
    }
    return urls;
  };

  const handleYouTubeAudio = async (): Promise<string> => {
    const res = await fetch('/api/audio/youtube', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: youtubeUrl }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'YouTube fetch failed');
    return data.audioUrl;
  };

  const uploadAudio = async (): Promise<string> => {
    if (!audioFile) throw new Error('No audio file');
    const form = new FormData();
    form.append('file', audioFile);
    const res = await fetch('/api/upload', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Audio upload failed');
    return data.url;
  };

  // Polling
  const startPolling = (id: string) => {
    pollCount.current = 0;
    const poll = async () => {
      pollCount.current++;
      if (pollCount.current > 180) {
        setError('Generation timed out after 15 minutes');
        setGenerating(false);
        return;
      }
      const res = await fetch(`/api/clips/${id}`);
      const data: ClipStatusResponse = await res.json();
      setClipStatus(data);
      if (data.status === 'completed' || data.status === 'preview' || data.status === 'failed') {
        setGenerating(false);
        if (data.status === 'failed') setError(data.error_message || 'Generation failed');
        return;
      }
      pollRef.current = setTimeout(poll, 5000);
    };
    pollRef.current = setTimeout(poll, 5000);
  };

  useEffect(() => () => { if (pollRef.current) clearTimeout(pollRef.current); }, []);

  const handleGenerate = async () => {
    setError(null);
    setGenerating(true);
    setClipId(null);
    setClipStatus(null);

    try {
      setUploading(true);
      const [uploadedPhotos, uploadedAudio] = await Promise.all([
        uploadPhotos(),
        audioMode === 'youtube' ? handleYouTubeAudio() : uploadAudio(),
      ]);
      setPhotoUrls(uploadedPhotos);
      setAudioUrl(uploadedAudio);
      setUploading(false);

      const outfitDesc = buildOutfitDescription(outfit);
      const res = await fetch('/api/clips/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          photoUrls: uploadedPhotos,
          audioUrl: uploadedAudio,
          shotStyle: selectedScene,
          includeLyrics,
          lyricsFont: lyricsConfig.font,
          lyricsCase: lyricsConfig.case,
          lyricsPosition: lyricsConfig.position,
          lyricsDifference: lyricsConfig.difference,
          creativePrompt: creativePrompt || undefined,
          customOutfitDescription: outfitDesc || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Generate failed');
      setClipId(data.clipId);
      startPolling(data.clipId);
      setStep('generate');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
      setGenerating(false);
      setUploading(false);
    }
  };

  const canProceed: Record<Step, boolean> = {
    photos: photoFiles.length > 0,
    audio: audioMode === 'youtube' ? youtubeUrl.length > 0 : audioFile !== null,
    scene: selectedScene.length > 0,
    outfit: true,
    lyrics: true,
    generate: true,
  };

  const currentIdx = STEPS.indexOf(step);

  const goNext = () => {
    if (step === 'lyrics') { handleGenerate(); return; }
    const next = STEPS[currentIdx + 1];
    if (next) setStep(next);
  };
  const goPrev = () => {
    const prev = STEPS[currentIdx - 1];
    if (prev) setStep(prev);
  };

  const previewLyrics = includeLyrics
    ? { text: applyLyricsCase('Sample lyric text', lyricsConfig.case), font: lyricsConfig.font, position: lyricsConfig.position, difference: lyricsConfig.difference }
    : undefined;

  const glowColor = activeScene ? '#6366f1' : '#6366f1';

  return (
    <main className="min-h-screen bg-white">
      <FloatingNav
        items={NAV_ITEMS}
        logo={<Link href="/" className="font-semibold text-sm text-gray-900">MV Generator</Link>}
        cta={<Link href="/shots" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">Browse scenes</Link>}
      />

      <div className="pt-24 pb-16 px-4 max-w-6xl mx-auto">
        {/* Step tabs */}
        <div className="flex items-center gap-1 mb-8 overflow-x-auto pb-1">
          {STEPS.map((s, i) => (
            <button
              key={s}
              onClick={() => { if (i <= currentIdx || canProceed[STEPS[i - 1] as Step]) setStep(s); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-colors ${s === step ? 'bg-gray-900 text-white' : i < currentIdx ? 'bg-gray-100 text-gray-500 hover:bg-gray-200' : 'text-gray-300 cursor-not-allowed'}`}
            >
              {STEP_ICONS[s]}
              {STEP_LABELS[s]}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-[1fr_220px] gap-8 items-start">
          {/* Main panel */}
          <div className="bg-white border border-gray-100 rounded-2xl p-6 min-h-[480px]">

            {/* STEP: Photos */}
            {step === 'photos' && (
              <div>
                <h2 className="text-xl font-bold mb-1">Upload your photos</h2>
                <p className="text-sm text-gray-500 mb-6">Up to 5 clear selfies. Face forward, good lighting.</p>
                <div
                  onDrop={handlePhotoDrop}
                  onDragOver={e => e.preventDefault()}
                  onClick={() => document.getElementById('photo-input')?.click()}
                  className="border-2 border-dashed border-gray-200 rounded-xl p-10 text-center cursor-pointer hover:border-gray-400 transition-colors mb-4"
                >
                  <Upload className="mx-auto mb-3 text-gray-400" size={28} />
                  <p className="text-sm font-medium text-gray-700">Drop photos here or click to select</p>
                  <p className="text-xs text-gray-400 mt-1">JPG, PNG, HEIC — max 5 photos</p>
                  <input id="photo-input" type="file" accept="image/*" multiple className="hidden" onChange={handlePhotoInput} />
                </div>
                {photoFiles.length > 0 && (
                  <div className="flex flex-wrap gap-3">
                    {photoFiles.map((f, i) => (
                      <div key={i} className="relative">
                        <img src={URL.createObjectURL(f)} alt="" className="w-20 h-20 object-cover rounded-xl" />
                        <button onClick={() => setPhotoFiles(prev => prev.filter((_, j) => j !== i))} className="absolute -top-1.5 -right-1.5 bg-gray-900 text-white rounded-full w-5 h-5 flex items-center justify-center">
                          <X size={10} />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* STEP: Audio */}
            {step === 'audio' && (
              <div>
                <h2 className="text-xl font-bold mb-1">Add your audio</h2>
                <p className="text-sm text-gray-500 mb-6">Upload an audio file or paste a YouTube URL.</p>
                <div className="flex gap-2 mb-6">
                  {(['upload', 'youtube'] as const).map(m => (
                    <button key={m} onClick={() => setAudioMode(m)} className={`px-4 py-2 rounded-full text-sm font-medium capitalize transition-colors ${audioMode === m ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      {m === 'youtube' ? 'YouTube URL' : 'Upload file'}
                    </button>
                  ))}
                </div>

                {audioMode === 'upload' ? (
                  <div>
                    <div onClick={() => document.getElementById('audio-input')?.click()} className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center cursor-pointer hover:border-gray-400 transition-colors">
                      <Music className="mx-auto mb-3 text-gray-400" size={28} />
                      <p className="text-sm font-medium text-gray-700">{audioFile ? audioFile.name : 'Click to upload audio'}</p>
                      <p className="text-xs text-gray-400 mt-1">MP3, WAV, M4A, AAC</p>
                      <input id="audio-input" type="file" accept="audio/*" className="hidden" onChange={e => setAudioFile(e.target.files?.[0] || null)} />
                    </div>
                  </div>
                ) : (
                  <div>
                    <input
                      type="url"
                      placeholder="https://www.youtube.com/watch?v=..."
                      value={youtubeUrl}
                      onChange={e => setYoutubeUrl(e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-gray-400"
                    />
                    <p className="text-xs text-gray-400 mt-2">The first 60 seconds of the video will be used.</p>
                  </div>
                )}
              </div>
            )}

            {/* STEP: Scene */}
            {step === 'scene' && (
              <div>
                <h2 className="text-xl font-bold mb-1">Pick a scene</h2>
                <p className="text-sm text-gray-500 mb-4">{SHOTS.length} scenes available</p>
                <div className="relative mb-4">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                  <input type="text" placeholder="Search scenes..." value={sceneQuery} onChange={e => setSceneQuery(e.target.value)} className="w-full pl-8 pr-4 py-2 text-sm rounded-full border border-gray-200 focus:outline-none focus:border-gray-400" />
                </div>
                <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 max-h-96 overflow-y-auto pr-1">
                  {filteredScenes.map(shot => (
                    <button key={shot.id} onClick={() => setSelectedScene(shot.id)} className="group block text-left">
                      <div className={`aspect-square rounded-xl overflow-hidden bg-gray-100 mb-1 relative ring-2 transition-all ${selectedScene === shot.id ? 'ring-gray-900' : 'ring-transparent'}`}>
                        <img src={shot.thumb} alt={shot.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform" />
                        {selectedScene === shot.id && (
                          <div className="absolute inset-0 bg-gray-900/20 flex items-center justify-center">
                            <div className="bg-gray-900 text-white rounded-full p-1"><Check size={12} /></div>
                          </div>
                        )}
                      </div>
                      <p className="text-[10px] text-center text-gray-600 truncate">{shot.name}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* STEP: Outfit */}
            {step === 'outfit' && (
              <div>
                <h2 className="text-xl font-bold mb-1">Choose your outfit</h2>
                <p className="text-sm text-gray-500 mb-4">Optional — skip to use whatever looks good with your scene.</p>

                {/* Presets */}
                <div className="flex gap-2 mb-4">
                  {OUTFIT_PRESETS.map(p => (
                    <button key={p.id} onClick={() => setOutfit(p.items)} className="px-3 py-1.5 rounded-full text-xs font-medium border border-gray-200 hover:border-gray-400 transition-colors">
                      {p.label}
                    </button>
                  ))}
                  <button onClick={() => setOutfit({})} className="px-3 py-1.5 rounded-full text-xs text-gray-400 border border-gray-100 hover:border-gray-200 transition-colors">Clear</button>
                </div>

                {/* Category tabs */}
                <div className="flex gap-1 mb-4">
                  {(['tops', 'bottoms', 'shoes', 'hats'] as const).map(cat => (
                    <button key={cat} onClick={() => setOutfitTab(cat)} className={`px-3 py-1.5 rounded-full text-xs font-medium capitalize transition-colors ${outfitTab === cat ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}>
                      {cat} {outfit[cat] ? '✓' : ''}
                    </button>
                  ))}
                </div>

                <div className="grid grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 max-h-72 overflow-y-auto pr-1">
                  {ALL_ITEMS.filter(i => i.category === outfitTab).map(item => (
                    <button key={item.id} onClick={() => setOutfit(prev => ({ ...prev, [outfitTab]: outfit[outfitTab] === item.id ? undefined : item.id }))} title={item.label} className="block">
                      <div className={`aspect-square rounded-xl overflow-hidden bg-gray-50 ring-2 transition-all ${outfit[outfitTab] === item.id ? 'ring-gray-900' : 'ring-transparent hover:ring-gray-200'}`}>
                        <img src={getOutfitThumbnailUrl(item.category, item.id)} alt={item.label} className="w-full h-full object-cover" />
                      </div>
                      <p className="text-[9px] text-center text-gray-500 mt-0.5 truncate">{item.label}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* STEP: Lyrics */}
            {step === 'lyrics' && (
              <div>
                <h2 className="text-xl font-bold mb-1">Lyrics overlay</h2>
                <p className="text-sm text-gray-500 mb-6">Optionally burn lyrics onto your video.</p>

                <label className="flex items-center gap-3 mb-6 cursor-pointer">
                  <div onClick={() => setIncludeLyrics(v => !v)} className={`w-10 h-6 rounded-full transition-colors relative ${includeLyrics ? 'bg-gray-900' : 'bg-gray-200'}`}>
                    <div className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${includeLyrics ? 'translate-x-4' : 'translate-x-0.5'}`} />
                  </div>
                  <span className="text-sm font-medium text-gray-700">Include lyrics</span>
                </label>

                {includeLyrics && (
                  <div className="space-y-5">
                    <div>
                      <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Font</label>
                      <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
                        {LYRICS_FONTS.map(f => (
                          <button key={f.id} onClick={() => setLyricsConfig(prev => ({ ...prev, font: f.id }))} className={`px-2 py-1.5 rounded-lg text-xs border transition-all ${lyricsConfig.font === f.id ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 hover:border-gray-300'}`} style={{ fontFamily: f.id }}>
                            {f.label}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Position</label>
                        <div className="flex flex-col gap-1">
                          {(['top', 'center', 'bottom'] as const).map(p => (
                            <button key={p} onClick={() => setLyricsConfig(prev => ({ ...prev, position: p }))} className={`px-3 py-1.5 rounded-lg text-xs capitalize text-left border transition-all ${lyricsConfig.position === p ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 hover:border-gray-300'}`}>{p}</button>
                          ))}
                        </div>
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Case</label>
                        <div className="flex flex-col gap-1">
                          {(['uppercase', 'lowercase', 'capitalize', 'none'] as const).map(c => (
                            <button key={c} onClick={() => setLyricsConfig(prev => ({ ...prev, case: c }))} className={`px-3 py-1.5 rounded-lg text-xs text-left border transition-all ${lyricsConfig.case === c ? 'border-gray-900 bg-gray-900 text-white' : 'border-gray-200 hover:border-gray-300'}`}>{c === 'none' ? 'As written' : c}</button>
                          ))}
                        </div>
                      </div>
                    </div>

                    <label className="flex items-center gap-3 cursor-pointer">
                      <div onClick={() => setLyricsConfig(prev => ({ ...prev, difference: !prev.difference }))} className={`w-8 h-5 rounded-full transition-colors relative ${lyricsConfig.difference ? 'bg-gray-900' : 'bg-gray-200'}`}>
                        <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white shadow transition-transform ${lyricsConfig.difference ? 'translate-x-3' : 'translate-x-0.5'}`} />
                      </div>
                      <span className="text-xs text-gray-600">Blend mode (invert over background)</span>
                    </label>
                  </div>
                )}

                <div className="mt-6 pt-5 border-t border-gray-100">
                  <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 block">Creative prompt (optional)</label>
                  <textarea
                    value={creativePrompt}
                    onChange={e => setCreativePrompt(e.target.value)}
                    placeholder="Extra direction for the AI — e.g. 'golden hour lighting, moody atmosphere'"
                    rows={3}
                    className="w-full px-4 py-3 rounded-xl border border-gray-200 text-sm focus:outline-none focus:border-gray-400 resize-none"
                  />
                </div>
              </div>
            )}

            {/* STEP: Generate */}
            {step === 'generate' && (
              <div className="text-center py-8">
                {generating && (
                  <>
                    <div className="w-12 h-12 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin mx-auto mb-6" />
                    {uploading && <p className="text-sm text-gray-600 mb-2">Uploading assets...</p>}
                    {clipStatus && (
                      <>
                        <p className="text-sm font-medium text-gray-900 mb-1">
                          {PIPELINE_LABELS[clipStatus.pipeline_step || ''] || 'Processing...'}
                        </p>
                        {clipStatus.queue_position && clipStatus.queue_position > 0 && (
                          <p className="text-xs text-gray-400 mb-3">Queue position: {clipStatus.queue_position}</p>
                        )}
                        <div className="w-full max-w-xs mx-auto bg-gray-100 rounded-full h-1.5 mb-2">
                          <div className="bg-gray-900 h-1.5 rounded-full transition-all" style={{ width: `${clipStatus.progress}%` }} />
                        </div>
                        <p className="text-xs text-gray-400">{clipStatus.progress}%</p>
                      </>
                    )}
                  </>
                )}

                {!generating && clipStatus?.status === 'completed' && clipStatus.output_url && (
                  <div>
                    <div className="w-10 h-10 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-4"><Check size={20} /></div>
                    <h3 className="text-xl font-bold mb-2">Done!</h3>
                    <p className="text-sm text-gray-500 mb-6">Your clip is ready.</p>
                    <a href={clipStatus.output_url} download className="inline-flex items-center gap-2 bg-gray-900 text-white px-6 py-3 rounded-full text-sm font-medium hover:bg-gray-700 transition-colors">
                      <Download size={16} /> Download clip
                    </a>
                    <div className="mt-4">
                      <button onClick={() => { setStep('photos'); setClipId(null); setClipStatus(null); setPhotoFiles([]); setAudioFile(null); }} className="text-sm text-gray-400 hover:text-gray-700 transition-colors">
                        Make another
                      </button>
                    </div>
                  </div>
                )}

                {!generating && clipStatus?.status === 'failed' && (
                  <div>
                    <p className="text-red-500 font-medium mb-2">Generation failed</p>
                    <p className="text-sm text-gray-500 mb-4">{clipStatus.error_message || 'Unknown error'}</p>
                    <button onClick={() => { setStep('photos'); setClipStatus(null); setClipId(null); }} className="text-sm text-gray-700 underline">Try again</button>
                  </div>
                )}

                {error && !generating && !clipStatus && (
                  <div>
                    <p className="text-red-500 mb-2">{error}</p>
                    <button onClick={() => { setStep('photos'); setError(null); }} className="text-sm text-gray-700 underline">Start over</button>
                  </div>
                )}
              </div>
            )}

            {/* Nav buttons */}
            {step !== 'generate' && (
              <div className="flex justify-between mt-8 pt-4 border-t border-gray-100">
                <button onClick={goPrev} disabled={currentIdx === 0} className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
                  <ChevronLeft size={16} /> Back
                </button>
                <button
                  onClick={goNext}
                  disabled={!canProceed[step]}
                  className="flex items-center gap-1.5 bg-gray-900 text-white text-sm font-medium px-5 py-2.5 rounded-full disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-700 transition-colors"
                >
                  {step === 'lyrics' ? (
                    <><Sparkles size={14} /> Generate</>
                  ) : (
                    <>Next <ChevronRight size={16} /></>
                  )}
                </button>
              </div>
            )}
          </div>

          {/* Phone preview sidebar */}
          <div className="hidden lg:flex flex-col items-center gap-4">
            <p className="text-xs text-gray-400 font-medium uppercase tracking-wide">Preview</p>
            <PhonePreview
              width={160}
              priority
              imageSrc={activeScene ? activeScene.thumb : undefined}
              lyrics={previewLyrics}
              glowColor={glowColor}
              videoSrc={clipStatus?.status === 'completed' ? (clipStatus.output_url ?? undefined) : undefined}
            />
            {activeScene && (
              <div className="text-center">
                <p className="text-sm font-medium text-gray-900">{activeScene.name}</p>
                <p className="text-xs text-gray-400 capitalize">{activeScene.tag}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  );
}

export default function CreatePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-gray-200 border-t-gray-900 rounded-full animate-spin" />
      </div>
    }>
      <CreatePageInner />
    </Suspense>
  );
}
