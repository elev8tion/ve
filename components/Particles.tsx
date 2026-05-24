'use client';
import { useEffect, useRef, useState } from 'react';
import { cn } from '@/lib/utils';

interface ParticlesProps {
  className?: string;
  quantity?: number;
  staticity?: number;
  ease?: number;
  size?: number;
  color?: string;
  vx?: number;
  vy?: number;
}

interface Particle {
  x: number; y: number; vx: number; vy: number;
  size: number; alpha: number; targetAlpha: number; magnetism: number;
}

function hexToRgb(hex: string): [number, number, number] {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? [parseInt(result[1], 16), parseInt(result[2], 16), parseInt(result[3], 16)]
    : [0, 0, 0];
}

export function Particles({
  className, quantity = 100, staticity = 50, ease = 50,
  size = 0.4, color = '#ffffff', vx = 0, vy = 0,
}: ParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouse = useRef({ x: 0, y: 0 });
  const particles = useRef<Particle[]>([]);
  const raf = useRef<number>(0);
  const [rgb] = useState(() => hexToRgb(color));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = window.devicePixelRatio || 1;

    const resize = () => {
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.scale(dpr, dpr);
      initParticles();
    };

    const initParticles = () => {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      particles.current = Array.from({ length: quantity }, () => ({
        x: Math.random() * w, y: Math.random() * h,
        vx: (Math.random() - 0.5) * 0.2 + vx,
        vy: (Math.random() - 0.5) * 0.2 + vy,
        size: Math.random() * size + 0.1,
        alpha: 0, targetAlpha: Math.random() * 0.6 + 0.1,
        magnetism: 0.1 + Math.random() * 4,
      }));
    };

    const edgeFade = (p: Particle, w: number, h: number) => {
      const margin = 50;
      const fx = Math.min(p.x / margin, 1, (w - p.x) / margin);
      const fy = Math.min(p.y / margin, 1, (h - p.y) / margin);
      return Math.min(fx, fy);
    };

    const draw = () => {
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      ctx.clearRect(0, 0, w, h);

      particles.current.forEach((p) => {
        const dx = mouse.current.x - p.x;
        const dy = mouse.current.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const force = (100 - Math.min(dist, 100)) / 100;

        p.x += p.vx + (dx / dist || 0) * force * p.magnetism * (100 / staticity);
        p.y += p.vy + (dy / dist || 0) * force * p.magnetism * (100 / staticity);

        if (p.x < 0) p.x = w; if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h; if (p.y > h) p.y = 0;

        const fade = edgeFade(p, w, h);
        p.alpha += (p.targetAlpha * fade - p.alpha) / ease;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${p.alpha})`;
        ctx.fill();
      });

      raf.current = requestAnimationFrame(draw);
    };

    const onMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    window.addEventListener('resize', resize);
    window.addEventListener('mousemove', onMouseMove);
    resize();
    draw();

    return () => {
      cancelAnimationFrame(raf.current);
      window.removeEventListener('resize', resize);
      window.removeEventListener('mousemove', onMouseMove);
    };
  }, [quantity, staticity, ease, size, vx, vy, rgb]);

  return <canvas ref={canvasRef} className={cn('w-full h-full', className)} />;
}
