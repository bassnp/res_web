'use client';

import { useEffect, useRef } from 'react';

const TARGET_FPS = 30;
const FRAME_TIME = 1000 / TARGET_FPS;

/**
 * HeroGridDots - Grid dot effect for the Hero section
 * Uses orangish color (inverse of the About Me green dots)
 */
export default function HeroGridDots() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const animationFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const isVisibleRef = useRef(true);
  const dotsRef = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current; 
    if (!canvas) return;

    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;

    let isMounted = true;

    const DOT_SPACING = 25;
    const BASE_DOT_SIZE = 0;
    const MAX_DOT_SIZE = 5;
    const INFLUENCE_RADIUS = 80;
    const DOT_COLOR = 'rgba(129, 178, 154, 0.4)'; // Greenish

    const resizeCanvas = () => {
      const container = canvas.parentElement;
      if (!container) return;

      const width = container.offsetWidth;
      const height = container.offsetHeight;
      
      if (width === 0 || height === 0) return;
      
      const dpr = Math.min(window.devicePixelRatio || 1, 2);

      canvas.width = width * dpr;
      canvas.height = height * dpr;

      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);

      const cols = Math.ceil(width / DOT_SPACING);
      const rows = Math.ceil(height / DOT_SPACING);
      dotsRef.current = [];
      for (let row = 0; row <= rows; row++) {
        for (let col = 0; col <= cols; col++) {
          dotsRef.current.push({ 
            x: col * DOT_SPACING + DOT_SPACING / 2, 
            y: row * DOT_SPACING + DOT_SPACING / 2 
          });
        }
      }
    };

    const handleMouseMove = (e) => {
      const container = canvas.parentElement;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
        mouseRef.current = { x, y };
      } else {
        mouseRef.current = { x: -1000, y: -1000 };
      }
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

    const handleVisibilityChange = () => {
      isVisibleRef.current = document.visibilityState === 'visible';
      if (isVisibleRef.current) lastFrameTimeRef.current = 0;
    };

    const drawDots = (timestamp) => {
      if (!isMounted) return;

      if (!isVisibleRef.current) {
        animationFrameRef.current = requestAnimationFrame(drawDots);
        return;
      }

      const elapsed = timestamp - lastFrameTimeRef.current;
      if (elapsed < FRAME_TIME) {
        animationFrameRef.current = requestAnimationFrame(drawDots);
        return;
      }
      lastFrameTimeRef.current = timestamp - (elapsed % FRAME_TIME);

      const container = canvas.parentElement;
      const width = container?.offsetWidth || 0;
      const height = container?.offsetHeight || 0;
      
      if (width === 0 || height === 0) {
        animationFrameRef.current = requestAnimationFrame(drawDots);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      const mouse = mouseRef.current;
      const dots = dotsRef.current;
      const influenceRadiusSq = INFLUENCE_RADIUS * INFLUENCE_RADIUS;

      ctx.fillStyle = DOT_COLOR;

      for (let i = 0; i < dots.length; i++) {
        const dot = dots[i];
        const dx = dot.x - mouse.x;
        const dy = dot.y - mouse.y;
        const distSq = dx * dx + dy * dy;

        let dotSize = BASE_DOT_SIZE;
        if (distSq < influenceRadiusSq) {
          const distance = Math.sqrt(distSq);
          const influence = 1 - (distance / INFLUENCE_RADIUS);
          dotSize = BASE_DOT_SIZE + (MAX_DOT_SIZE - BASE_DOT_SIZE) * influence;
        }

        if (dotSize > 0.1) {
          ctx.beginPath();
          ctx.arc(dot.x, dot.y, dotSize, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animationFrameRef.current = requestAnimationFrame(drawDots);
    };

    resizeCanvas();

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('visibilitychange', handleVisibilityChange);

    let resizeObserver;
    if (typeof ResizeObserver !== 'undefined') {
      const container = canvas.parentElement;
      if (container) {
        resizeObserver = new ResizeObserver(() => resizeCanvas());
        resizeObserver.observe(container);
      }
    }

    animationFrameRef.current = requestAnimationFrame(drawDots);

    return () => {
      isMounted = false;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (resizeObserver) resizeObserver.disconnect();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, []);

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <canvas 
        ref={canvasRef} 
        className="absolute inset-0 w-full h-full pointer-events-none" 
        aria-hidden="true" 
      />
    </div>
  );
}
