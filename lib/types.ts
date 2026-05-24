export type SceneTag = 'music' | 'urban' | 'nature' | 'vehicles';

export interface Shot {
  id: string;
  name: string;
  tag: SceneTag;
  thumb: string;
  keywords: string[];
  motionPrompt: string;
  negativePrompt: string;
  popular?: boolean;
}

export type ClipStatus = 'pending' | 'processing' | 'completed' | 'preview' | 'failed';

export type PipelineStep =
  | 'face_swap'
  | 'video_gen'
  | 'lip_sync'
  | 'bg_composite'
  | 'audio_merge'
  | 'done';

export interface GeneratePayload {
  photoUrls: string[];
  audioUrl: string;
  shotStyle: string;
  includeLyrics: boolean;
  lyricsFont: string;
  lyricsCase: 'uppercase' | 'lowercase' | 'capitalize' | 'none';
  lyricsPosition: 'top' | 'center' | 'bottom';
  lyricsDifference: boolean;
  creativePrompt?: string;
  customOutfitDescription?: string;
  outfitTier?: string;
  outfitItemIds?: Record<string, string>;
}

export interface ClipStatusResponse {
  status: ClipStatus;
  pipeline_step: PipelineStep | null;
  progress: number;
  queue_position: number | null;
  output_url: string | null;
  preview_image_url: string | null;
  error_message: string | null;
}

export interface OutfitSelection {
  tops?: string;
  bottoms?: string;
  shoes?: string;
  hats?: string;
}
