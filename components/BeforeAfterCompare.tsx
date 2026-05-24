'use client';
import { useState, useRef, useEffect, useCallback } from 'react';

interface BeforeAfterCompareProps {
  beforeSrc: string;
  afterSrc: string;
  beforePoster?: string;
  afterPoster?: string;
  className?: string;
}

export function BeforeAfterCompare({ beforeSrc, afterSrc, beforePoster, afterPoster, className }: BeforeAfterCompareProps) {
  const [split, setSplit] = useState(50);
  const [loaded, setLoaded] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const beforeRef = useRef<HTMLVideoElement>(null);
  const afterRef = useRef<HTMLVideoElement>(null);
  const loadCount = useRef(0);
  const dragging = useRef(false);

  const onVideoLoaded = useCallback(() => {
    loadCount.current++;
    if (loadCount.current >= 2) {
      beforeRef.current?.play().catch(() => {});
      afterRef.current?.play().catch(() => {});
    }
  }, []);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setLoaded(true); obs.disconnect(); } },
      { rootMargin: '200px' }
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const getX = (e: React.MouseEvent | React.TouchEvent) => {
    const rect = containerRef.current!.getBoundingClientRect();
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    return Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
  };

  return (
    <div
      ref={containerRef}
      className={className}
      style={{ position: 'relative', overflow: 'hidden', cursor: 'ew-resize', userSelect: 'none' }}
      onMouseDown={(e) => { dragging.current = true; setSplit(getX(e)); }}
      onMouseMove={(e) => { if (dragging.current) setSplit(getX(e)); }}
      onMouseUp={() => { dragging.current = false; }}
      onMouseLeave={() => { dragging.current = false; }}
      onTouchStart={(e) => { dragging.current = true; setSplit(getX(e)); }}
      onTouchMove={(e) => { if (dragging.current) setSplit(getX(e)); }}
      onTouchEnd={() => { dragging.current = false; }}
    >
      {loaded && (
        <>
          <video ref={beforeRef} src={beforeSrc} poster={beforePoster} loop muted playsInline onLoadedData={onVideoLoaded} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 0 ${split}%)`, pointerEvents: 'none' }}>
            <video ref={afterRef} src={afterSrc} poster={afterPoster} loop muted playsInline onLoadedData={onVideoLoaded} style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
          </div>
          <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${split}%`, width: 2, background: 'white', transform: 'translateX(-50%)', pointerEvents: 'none' }}>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', width: 32, height: 32, borderRadius: '50%', background: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 2px 8px rgba(0,0,0,0.3)' }}>
              <span style={{ fontSize: 12, color: '#333' }}>⇔</span>
            </div>
          </div>
        </>
      )}
      {!loaded && <div style={{ width: '100%', height: '100%', background: '#f5f5f5' }} />}
    </div>
  );
}
