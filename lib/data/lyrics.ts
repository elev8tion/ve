// Extracted from production homepage bundle — real lyrics configuration options
// 15 custom fonts, 3 position options, 4 case options, blend mode toggle

export interface LyricsConfig {
  font: LyricsFont;
  position: LyricsPosition;
  case: LyricsCase;
  difference: boolean;
}

export type LyricsPosition = 'top' | 'center' | 'bottom';
export type LyricsCase = 'uppercase' | 'lowercase' | 'capitalize' | 'none';
export type LyricsFont =
  | 'coolvetica'
  | 'relationship'
  | 'apple-garamond'
  | 'lemon-milk'
  | 'bebas'
  | 'new-romantics'
  | 'brunson'
  | 'vcr'
  | 'roblox'
  | 'the-bold-font'
  | 'doctor-glitch'
  | 'planet-kosmos'
  | 'designer'
  | 'pricedown'
  | 'hidayatullah';

export interface FontOption {
  id: LyricsFont;
  label: string;
  style: 'sans' | 'serif' | 'display' | 'script' | 'mono' | 'retro';
}

export const LYRICS_FONTS: FontOption[] = [
  { id: 'coolvetica', label: 'Coolvetica', style: 'sans' },
  { id: 'relationship', label: 'Relationship', style: 'script' },
  { id: 'apple-garamond', label: 'Apple Garamond', style: 'serif' },
  { id: 'lemon-milk', label: 'Lemon Milk', style: 'display' },
  { id: 'bebas', label: 'Bebas', style: 'display' },
  { id: 'new-romantics', label: 'New Romantics', style: 'serif' },
  { id: 'brunson', label: 'Brunson', style: 'display' },
  { id: 'vcr', label: 'VCR', style: 'mono' },
  { id: 'roblox', label: 'Roblox', style: 'display' },
  { id: 'the-bold-font', label: 'The Bold Font', style: 'sans' },
  { id: 'doctor-glitch', label: 'Doctor Glitch', style: 'retro' },
  { id: 'planet-kosmos', label: 'Planet Kosmos', style: 'display' },
  { id: 'designer', label: 'Designer', style: 'sans' },
  { id: 'pricedown', label: 'Pricedown', style: 'retro' },
  { id: 'hidayatullah', label: 'Hidayatullah', style: 'script' },
];

export const DEFAULT_LYRICS_CONFIG: LyricsConfig = {
  font: 'coolvetica',
  position: 'center',
  case: 'uppercase',
  difference: false,
};

export function applyLyricsCase(text: string, lyricsCase: LyricsCase): string {
  switch (lyricsCase) {
    case 'uppercase': return text.toUpperCase();
    case 'lowercase': return text.toLowerCase();
    case 'capitalize':
      return text.replace(/\b\w/g, (c) => c.toUpperCase());
    case 'none': return text;
  }
}

export const LYRICS_POSITION_LABELS: Record<LyricsPosition, string> = {
  top: 'Top',
  center: 'Center',
  bottom: 'Bottom',
};

export const LYRICS_CASE_LABELS: Record<LyricsCase, string> = {
  uppercase: 'ALL CAPS',
  lowercase: 'lowercase',
  capitalize: 'Title Case',
  none: 'As Written',
};
