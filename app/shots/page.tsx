'use client';
import { useState } from 'react';
import Link from 'next/link';
import { Home, Clapperboard, Wand2, Search } from 'lucide-react';
import { FloatingNav } from '@/components/FloatingNav';
import { SHOTS } from '@/lib/data/shots';
import type { SceneTag } from '@/lib/types';

const NAV_ITEMS = [
  { name: 'Home', url: '/', icon: Home },
  { name: 'Shots', url: '/shots', icon: Clapperboard },
  { name: 'Create', url: '/create', icon: Wand2 },
];

const ALL_TAGS: (SceneTag | 'all')[] = ['all', 'music', 'urban', 'nature', 'vehicles'];

export default function ShotsPage() {
  const [query, setQuery] = useState('');
  const [tag, setTag] = useState<SceneTag | 'all'>('all');

  const filtered = SHOTS.filter(s => {
    const matchesTag = tag === 'all' || s.tag === tag;
    const q = query.toLowerCase();
    const matchesQ = !q || s.name.toLowerCase().includes(q) || s.keywords.some(k => k.includes(q));
    return matchesTag && matchesQ;
  });

  return (
    <main className="min-h-screen bg-white">
      <FloatingNav
        items={NAV_ITEMS}
        logo={<Link href="/" className="font-semibold text-sm text-gray-900">MV Generator</Link>}
        cta={<Link href="/create" className="bg-gray-900 text-white text-sm font-medium px-4 py-1.5 rounded-full hover:bg-gray-700 transition-colors">Create</Link>}
      />

      <div className="pt-32 pb-24 px-6 max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">All Scenes</h1>
        <p className="text-gray-500 mb-8">{SHOTS.length} scenes — click any to start creating</p>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3 mb-8">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Search scenes..."
              value={query}
              onChange={e => setQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-full border border-gray-200 text-sm bg-white focus:outline-none focus:border-gray-400"
            />
          </div>
          <div className="flex gap-2">
            {ALL_TAGS.map(t => (
              <button
                key={t}
                onClick={() => setTag(t)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors capitalize ${tag === t ? 'bg-gray-900 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        <p className="text-sm text-gray-400 mb-6">{filtered.length} results</p>

        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3">
          {filtered.map(shot => (
            <Link key={shot.id} href={`/create?scene=${shot.id}`} className="group block">
              <div className="aspect-square rounded-xl overflow-hidden bg-gray-100 mb-2 relative">
                <img src={shot.thumb} alt={shot.name} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                {shot.popular && (
                  <span className="absolute top-1.5 right-1.5 bg-gray-900 text-white text-[10px] font-medium px-1.5 py-0.5 rounded-full">popular</span>
                )}
              </div>
              <p className="text-xs text-gray-700 font-medium text-center truncate">{shot.name}</p>
              <p className="text-[10px] text-gray-400 text-center capitalize">{shot.tag}</p>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
