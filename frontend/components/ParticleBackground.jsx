'use client';

import { useState, useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import {
  PARTICLE_COUNT,
  PARTICLE_COUNT_MOBILE,
  PARTICLE_MAX_SPEED,
  PARTICLE_CONNECTION_DISTANCE,
  MAX_CONNECTIONS_PER_PARTICLE,
  TARGET_FPS,
  FRAME_TIME,
} from '@/lib/particleConfig';

// Inline color definitions - pre-computed as objects for performance
const PARTICLE_COLORS_LIGHT = [
  { r: 200, g: 90, b: 65, a: 0.85 },
  { r: 45, g: 48, b: 75, a: 0.75 },
  { r: 95, g: 150, b: 125, a: 0.8 },
  { r: 220, g: 170, b: 95, a: 0.75 },
  { r: 190, g: 65, b: 45, a: 0.8 },
];

const PARTICLE_COLORS_DARK = [
  { r: 255, g: 150, b: 130, a: 0.7 },
  { r: 150, g: 220, b: 200, a: 0.65 },
  { r: 255, g: 230, b: 180, a: 0.6 },
  { r: 180, g: 200, b: 220, a: 0.6 },
  { r: 244, g: 241, b: 222, a: 0.55 },
];

// Pre-compute squared distance to avoid sqrt in hot path
const CONNECTION_DISTANCE_SQ = PARTICLE_CONNECTION_DISTANCE * PARTICLE_CONNECTION_DISTANCE;

export default function ParticleBackground() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const particlesRef = useRef([]);
  const isVisibleRef = useRef(true);
  const boundsRef = useRef({ width: 0, height: 0 });

  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Pause animation when tab is hidden - critical for CPU savings
  useEffect(() => {
    if (!mounted) return;

    const handleVisibilityChange = () => {
      isVisibleRef.current = document.visibilityState === 'visible';
      if (isVisibleRef.current) {
        lastFrameTimeRef.current = 0;
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;

    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let isMounted = true;

    // Respect reduced motion preference
    const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) return;

    // Determine particle count based on device
    const isMobile = window.innerWidth < 768;
    const particleCount = isMobile ? PARTICLE_COUNT_MOBILE : PARTICLE_COUNT;
    const colors = theme === 'dark' ? PARTICLE_COLORS_DARK : PARTICLE_COLORS_LIGHT;

    const createParticle = (width, height) => {
      const color = colors[Math.floor(Math.random() * colors.length)];
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * PARTICLE_MAX_SPEED,
        vy: (Math.random() - 0.5) * PARTICLE_MAX_SPEED,
        radius: Math.random() * 1.2 + 0.8,
        color,
        colorStr: `rgba(${color.r},${color.g},${color.b},${color.a})`,
      };
    };

    const resizeCanvas = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const width = window.innerWidth;
      const height = window.innerHeight;

      canvas.width = width * dpr;
      canvas.height = height * dpr;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const prevWidth = boundsRef.current.width || width;
      const prevHeight = boundsRef.current.height || height;
      
      if (prevWidth && prevHeight && particlesRef.current.length > 0) {
        const scaleX = width / prevWidth;
        const scaleY = height / prevHeight;
        particlesRef.current.forEach(p => {
          p.x *= scaleX;
          p.y *= scaleY;
        });
      }

      boundsRef.current = { width, height };
    };

    resizeCanvas();

    // Initialize particles
    particlesRef.current = [];
    const { width, height } = boundsRef.current;
    for (let i = 0; i < particleCount; i++) {
      particlesRef.current.push(createParticle(width, height));
    }

    // Optimized animation loop with frame rate limiting
    const animate = (timestamp) => {
      if (!isMounted) return;

      // Skip if tab hidden
      if (!isVisibleRef.current) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      // Frame rate limiting for CPU savings
      const elapsed = timestamp - lastFrameTimeRef.current;
      if (elapsed < FRAME_TIME) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }
      lastFrameTimeRef.current = timestamp - (elapsed % FRAME_TIME);

      const { width, height } = boundsRef.current;
      if (!width || !height) {
        animationFrameRef.current = requestAnimationFrame(animate);
        return;
      }

      const delta = Math.min(elapsed / 1000, 0.05);
      const particles = particlesRef.current;

      ctx.clearRect(0, 0, width, height);

      // Update and draw particles
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        
        p.x += p.vx * delta;
        p.y += p.vy * delta;

        if (p.x < 0) p.x = width;
        else if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        else if (p.y > height) p.y = 0;

        ctx.beginPath();
        ctx.fillStyle = p.colorStr;
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Draw connections - optimized
      const connectionCounts = new Uint8Array(particles.length);
      
      for (let i = 0; i < particles.length; i++) {
        if (connectionCounts[i] >= MAX_CONNECTIONS_PER_PARTICLE) continue;
        
        const a = particles[i];
        
        for (let j = i + 1; j < particles.length; j++) {
          if (connectionCounts[j] >= MAX_CONNECTIONS_PER_PARTICLE) continue;
          
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distSq = dx * dx + dy * dy;
          
          if (distSq > CONNECTION_DISTANCE_SQ) continue;
          
          const dist = Math.sqrt(distSq);
          const alpha = (1 - dist / PARTICLE_CONNECTION_DISTANCE) * 0.3;
          
          if (alpha <= 0.01) continue;
          
          connectionCounts[i]++;
          connectionCounts[j]++;

          ctx.beginPath();
          ctx.strokeStyle = `rgba(${(a.color.r + b.color.r) >> 1},${(a.color.g + b.color.g) >> 1},${(a.color.b + b.color.b) >> 1},${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }

      animationFrameRef.current = requestAnimationFrame(animate);
    };

    let resizeTimeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(resizeCanvas, 100);
    };

    window.addEventListener('resize', handleResize);
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      isMounted = false;
      clearTimeout(resizeTimeout);
      window.removeEventListener('resize', handleResize);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      particlesRef.current = [];
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mounted, theme]);

  if (!mounted) return null;

  return (
    <div ref={containerRef} className="particle-container" aria-hidden="true">
      <canvas ref={canvasRef} className="particle-lines-canvas" />
    </div>
  );
}
