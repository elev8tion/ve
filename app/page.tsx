import Link from 'next/link';
import { Home, Clapperboard, Wand2 } from 'lucide-react';
import dynamic from 'next/dynamic';
import { FloatingNav } from '@/components/FloatingNav';
import { BeforeAfterCompare } from '@/components/BeforeAfterCompare';
import { FaqAccordion } from '@/components/FaqAccordion';
import { SHOTS } from '@/lib/data/shots';

const Particles = dynamic(() => import('@/components/Particles').then(m => ({ default: m.Particles })), { ssr: false });

const NAV_ITEMS = [
  { name: 'Home', url: '/', icon: Home },
  { name: 'Shots', url: '/shots', icon: Clapperboard },
  { name: 'Create', url: '/create', icon: Wand2 },
];

const BEFORE_AFTER = [
  { before: '/videos/armory-before.mp4', after: '/videos/armory-after.mp4', beforePoster: '/videos/armory-before-poster.jpg', afterPoster: '/videos/armory-after-poster.jpg' },
  { before: '/videos/by-the-fire-before.mp4', after: '/videos/by-the-fire-after.mp4', beforePoster: '/videos/by-the-fire-before-poster.jpg', afterPoster: '/videos/by-the-fire-after-poster.jpg' },
  { before: '/videos/in-the-city-before.mp4', after: '/videos/in-the-city-after.mp4', beforePoster: '/videos/in-the-city-before-poster.jpg', afterPoster: '/videos/in-the-city-after-poster.jpg' },
];

const FAQ = [
  { id: 1, question: 'What do I upload?', answer: 'A clear selfie photo (face forward, good lighting) and a short audio clip — 15–60 seconds works best.' },
  { id: 2, question: 'How long does generation take?', answer: 'Usually 60–90 seconds. The pipeline runs face swap → scene generation → lip sync → compositing → audio merge.' },
  { id: 3, question: 'What scenes are available?', answer: '101 scenes across urban, music, nature, and vehicle environments. Browse all of them on the Shots page.' },
  { id: 4, question: 'Can I customize the outfit?', answer: 'Yes — the create page has a full outfit picker with 43 tops, 42 bottoms, 40 shoes, and 21 hats.' },
];

const POPULAR = SHOTS.filter(s => s.popular).slice(0, 12);

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      <FloatingNav
        items={NAV_ITEMS}
        logo={<Link href="/" className="font-semibold text-sm text-gray-900 tracking-tight">MV Generator</Link>}
        cta={
          <Link href="/create" className="flex items-center gap-1.5 bg-gray-900 text-white text-sm font-medium px-4 py-1.5 rounded-full hover:bg-gray-700 transition-colors">
            Create
          </Link>
        }
      />

      <Particles className="fixed inset-0 z-0 hidden md:block" quantity={60} ease={80} color="#000000" size={0.4} staticity={40} />

      {/* Hero */}
      <section className="relative z-10 pt-40 pb-24 px-6 text-center">
        <h1 className="text-6xl md:text-8xl font-bold tracking-tight text-gray-900 mb-6">
          AI Music Videos.
        </h1>
        <p className="text-xl text-gray-500 max-w-xl mx-auto mb-10">
          Upload a selfie + audio clip, pick a scene, get a lip-synced performance clip.
        </p>
        <Link href="/create" className="inline-flex items-center gap-2 bg-gray-900 text-white text-base font-medium px-8 py-4 rounded-full hover:bg-gray-700 transition-colors">
          <Wand2 size={18} />
          Start creating
        </Link>
      </section>

      {/* Before / After */}
      <section className="relative z-10 px-6 py-16 max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">Before & After</h2>
        <div className="hidden md:grid grid-cols-3 gap-6">
          {BEFORE_AFTER.map((pair, i) => (
            <BeforeAfterCompare
              key={i}
              beforeSrc={pair.before}
              afterSrc={pair.after}
              beforePoster={pair.beforePoster}
              afterPoster={pair.afterPoster}
              className="aspect-[9/16] rounded-2xl overflow-hidden"
            />
          ))}
        </div>
        <div className="md:hidden">
          <BeforeAfterCompare
            beforeSrc={BEFORE_AFTER[1].before}
            afterSrc={BEFORE_AFTER[1].after}
            beforePoster={BEFORE_AFTER[1].beforePoster}
            afterPoster={BEFORE_AFTER[1].afterPoster}
            className="aspect-[9/16] rounded-2xl overflow-hidden max-w-xs mx-auto"
          />
        </div>
      </section>

      {/* Popular Shots */}
      <section className="relative z-10 px-6 py-16 max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-3xl font-bold">Popular Scenes</h2>
          <Link href="/shots" className="text-sm text-gray-500 hover:text-gray-900 transition-colors">View all 101 →</Link>
        </div>
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {POPULAR.map((shot) => (
            <Link key={shot.id} href={`/create?scene=${shot.id}`} className="group block">
              <div className="aspect-square rounded-xl overflow-hidden bg-gray-100 mb-2">
                <img src={shot.thumb} alt={shot.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              </div>
              <p className="text-xs text-gray-600 text-center truncate">{shot.name}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="relative z-10 px-6 py-16 max-w-3xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-10">FAQ</h2>
        <FaqAccordion data={FAQ} />
      </section>

      <footer className="relative z-10 border-t border-gray-100 py-8 text-center text-sm text-gray-400">
        Personal build — not affiliated with VisualEssential
      </footer>
    </main>
  );
}
