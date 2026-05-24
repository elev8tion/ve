'use client';
import { useRef, useState, useEffect, useId } from 'react';
import { motion } from 'framer-motion';

export interface LyricsOverlay {
  text: string;
  font: string;
  position: 'top' | 'center' | 'bottom';
  difference?: boolean;
}

export interface PhonePreviewProps {
  videoSrc?: string;
  imageSrc?: string;
  lyrics?: LyricsOverlay;
  glowColor?: string;
  className?: string;
  width?: number;
  priority?: boolean;
  onClick?: () => void;
  overlay?: React.ReactNode;
}

export function PhonePreview({
  videoSrc, imageSrc, lyrics, glowColor, className,
  width, priority = false, onClick, overlay,
}: PhonePreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [loaded, setLoaded] = useState(priority);
  const containerRef = useRef<HTMLDivElement>(null);
  const uid = useId().replace(/:/g, '');
  const baseColor = glowColor || '#6366f1';
  const [currentColor, setCurrentColor] = useState(baseColor);
  const [prevColor, setPrevColor] = useState(baseColor);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    if (baseColor !== currentColor) {
      setPrevColor(currentColor);
      setIsTransitioning(true);
      setCurrentColor(baseColor);
      const t = setTimeout(() => setIsTransitioning(false), 800);
      return () => clearTimeout(t);
    }
  }, [baseColor, currentColor]);

  useEffect(() => {
    if (priority || loaded) return;
    const el = containerRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setLoaded(true); obs.disconnect(); } },
      { rootMargin: '200px' }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [priority, loaded]);

  useEffect(() => {
    if (videoRef.current && videoSrc) videoRef.current.play().catch(() => {});
  }, [videoSrc, loaded]);

  const W = width ?? 180;
  const H = Math.round(2.048 * W);
  const scale = W / 180;
  const borderRadius = Math.round(0.17 * W);
  const padding = Math.max(3, Math.round(0.035 * W));
  const buttonW = Math.max(2, 2.5 * scale);
  const buttonR = Math.max(2, Math.round(1.5 * scale));
  const volTopY = Math.round(0.19 * H);
  const volH = Math.round(28 * scale);
  const vol2Y = volTopY + volH + Math.round(5 * scale);
  const powerY = Math.round(0.22 * H);
  const powerH = Math.round(34 * scale);
  const notchW = Math.round(0.3 * W);
  const notchH = Math.round(0.24 * notchW);
  const lyricsTop = lyrics?.position === 'top' ? '15%' : lyrics?.position === 'bottom' ? '78%' : '50%';
  const auraW = Math.round(2.4 * W);
  const auraH = Math.round(1.5 * H);

  return (
    <div ref={containerRef} className={className} style={{ width: W + 20, height: H + 40, position: 'relative', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <style>{`
        @keyframes auraA_${uid} {
          0%   { transform: translate(-50%,-50%) scale(0.85); opacity: 0.55; }
          25%  { transform: translate(-44%,-45%) scale(1.12); opacity: 0.9; }
          50%  { transform: translate(-56%,-53%) scale(0.9);  opacity: 0.65; }
          75%  { transform: translate(-47%,-47%) scale(1.1);  opacity: 0.85; }
          100% { transform: translate(-50%,-50%) scale(0.85); opacity: 0.55; }
        }
        @keyframes auraB_${uid} {
          0%   { transform: translate(-50%,-50%) scale(1);    opacity: 0.45; }
          25%  { transform: translate(-56%,-54%) scale(0.85); opacity: 0.7; }
          50%  { transform: translate(-44%,-46%) scale(1.1);  opacity: 0.45; }
          75%  { transform: translate(-52%,-52%) scale(0.9);  opacity: 0.7; }
          100% { transform: translate(-50%,-50%) scale(1);    opacity: 0.45; }
        }
        @keyframes idleFloat_${uid} {
          0%, 100% { transform: translateY(0); }
          50%      { transform: translateY(-6px); }
        }
      `}</style>

      {isTransitioning && <div key={`prev-${prevColor}`} style={{ position: 'absolute', left: '50%', top: '50%', width: auraW, height: auraH, borderRadius: '50%', background: `radial-gradient(ellipse, ${prevColor}55 0%, ${prevColor}30 25%, ${prevColor}12 50%, transparent 72%)`, filter: 'blur(16px)', pointerEvents: 'none', transform: 'translate(-50%,-50%)', animation: `auraA_${uid} 5s ease-in-out infinite`, opacity: 0, transition: 'opacity 0.8s ease-out' }} />}
      <div key={`a-${currentColor}`} style={{ position: 'absolute', left: '50%', top: '50%', width: auraW, height: auraH, borderRadius: '50%', background: `radial-gradient(ellipse, ${currentColor}55 0%, ${currentColor}30 25%, ${currentColor}12 50%, transparent 72%)`, filter: 'blur(16px)', pointerEvents: 'none', animation: `auraA_${uid} 5s ease-in-out infinite` }} />
      <div key={`b-${currentColor}`} style={{ position: 'absolute', left: '50%', top: '50%', width: Math.round(1.8 * W), height: Math.round(1.2 * H), borderRadius: '50%', background: `radial-gradient(ellipse, ${currentColor}45 0%, ${currentColor}20 30%, transparent 65%)`, filter: 'blur(18px)', pointerEvents: 'none', animation: `auraB_${uid} 4s ease-in-out infinite` }} />

      {loaded && (
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center', animation: `idleFloat_${uid} 4s ease-in-out infinite` }}>
          <motion.div whileHover={{ scale: 1.06 }} whileTap={{ scale: 1.1 }} transition={{ type: 'spring', stiffness: 400, damping: 17 }} onTap={() => onClick?.()} style={{ width: W, height: H, transformOrigin: 'center center', cursor: 'pointer' }}>
            <div style={{ position: 'absolute', left: -buttonW, top: Math.round(0.12 * H), width: buttonW, height: Math.round(14 * scale), background: '#111', borderRadius: `${buttonR}px 0 0 ${buttonR}px` }} />
            <div style={{ position: 'absolute', left: -buttonW, top: volTopY, width: buttonW, height: volH, background: '#111', borderRadius: `${buttonR}px 0 0 ${buttonR}px` }} />
            <div style={{ position: 'absolute', left: -buttonW, top: vol2Y, width: buttonW, height: volH, background: '#111', borderRadius: `${buttonR}px 0 0 ${buttonR}px` }} />
            <div style={{ position: 'absolute', right: -buttonW, top: powerY, width: buttonW, height: powerH, background: '#111', borderRadius: `0 ${buttonR}px ${buttonR}px 0` }} />
            <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius, background: '#000', padding, boxShadow: '0 0 0 0.5px rgba(255,255,255,0.08), 0 8px 24px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
              <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: Math.max(borderRadius - padding, 8), overflow: 'hidden', background: '#000' }}>
                {videoSrc && <video ref={videoRef} src={videoSrc} autoPlay loop muted playsInline style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />}
                {imageSrc && !videoSrc && <img src={imageSrc} alt="" style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />}
                {lyrics && <div style={{ position: 'absolute', left: '8%', right: '8%', top: lyricsTop, transform: 'translateY(-50%)', textAlign: 'center', fontFamily: lyrics.font, fontSize: `${Math.max(8, 12 * scale)}px`, lineHeight: 1.3, color: '#fff', textShadow: '0 1px 4px rgba(0,0,0,0.6)', ...(lyrics.difference ? { mixBlendMode: 'difference' as const } : {}), pointerEvents: 'none' }}>{lyrics.text}</div>}
                {overlay && <div style={{ position: 'absolute', inset: 0, zIndex: 5 }}>{overlay}</div>}
                <div style={{ position: 'absolute', top: Math.round(padding + 6 * scale), left: '50%', transform: 'translateX(-50%)', width: notchW, height: notchH, borderRadius: Math.round(notchH / 2), background: '#000', zIndex: 10 }} />
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
