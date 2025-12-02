'use client';

import { useState, useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';

const TARGET_FPS = 30;
const FRAME_TIME = 1000 / TARGET_FPS;

export default function InteractiveGridDots() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const hoveredCardsRef = useRef([]);
  const animationFrameRef = useRef(null);
  const lastFrameTimeRef = useRef(0);
  const isVisibleRef = useRef(true);
  const dotsRef = useRef([]);
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    const handleVisibilityChange = () => {
      isVisibleRef.current = document.visibilityState === 'visible';
      if (isVisibleRef.current) lastFrameTimeRef.current = 0;
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [mounted]);

  useEffect(() => {
    if (!mounted) return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d', { alpha: true });
    if (!ctx) return;
    let isMounted = true;
    const DOT_SPACING = 30;
    const BASE_DOT_SIZE = 0;
    const MAX_DOT_SIZE = 5;
    const INFLUENCE_RADIUS = 80;

    // Colors
    const DEFAULT_COLOR = 'rgba(224, 122, 95, 0.4)'; // Orangish
    const CARD_HOVER_COLOR = 'rgba(129, 178, 154, 0.6)'; // Greenish

    // Get dot color - check if behind a hovered card
    const getDotColor = (dotX, dotY) => {
      const sectionRect = canvas.parentElement?.parentElement?.getBoundingClientRect();
      if (!sectionRect) return DEFAULT_COLOR;

      for (const cardRect of hoveredCardsRef.current) {
        const dotAbsoluteX = dotX + sectionRect.left;
        const dotAbsoluteY = dotY + sectionRect.top;
        
        if (
          dotAbsoluteX >= cardRect.left &&
          dotAbsoluteX <= cardRect.right &&
          dotAbsoluteY >= cardRect.top &&
          dotAbsoluteY <= cardRect.bottom
        ) {
          return CARD_HOVER_COLOR;
        }
      }
      return DEFAULT_COLOR;
    };

    // Update hovered cards list
    const updateHoveredCards = () => {
      const section = canvas.parentElement?.parentElement;
      if (!section) return;
      const cards = section.querySelectorAll('[data-work-experience-card]');
      const hoveredCards = [];
      cards.forEach((card) => {
        if (card.matches(':hover')) {
          hoveredCards.push(card.getBoundingClientRect());
        }
      });
      hoveredCardsRef.current = hoveredCards;
    };

    const resizeCanvas = () => {
      const wrapper = canvas.parentElement;
      const parent = wrapper?.parentElement;
      if (!parent) return;
      const rect = parent.getBoundingClientRect();
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = rect.width + 'px';
      canvas.style.height = rect.height + 'px';
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      const cols = Math.ceil(rect.width / DOT_SPACING);
      const rows = Math.ceil(rect.height / DOT_SPACING);
      dotsRef.current = [];
      for (let row = 0; row <= rows; row++) {
        for (let col = 0; col <= cols; col++) {
          dotsRef.current.push({ x: col * DOT_SPACING + 2, y: row * DOT_SPACING + 2 });
        }
      }
    };

    const handleMouseMove = (e) => {
      const wrapper = canvas.parentElement;
      const section = wrapper?.parentElement;
      if (!section) return;
      const rect = section.getBoundingClientRect();
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
      const rect = canvas.getBoundingClientRect();
      if (rect.width === 0 || rect.height === 0) {
        animationFrameRef.current = requestAnimationFrame(drawDots);
        return;
      }
      ctx.clearRect(0, 0, rect.width, rect.height);

      // Update hovered cards before drawing
      updateHoveredCards();

      const mouse = mouseRef.current;
      const dots = dotsRef.current;
      const influenceRadiusSq = INFLUENCE_RADIUS * INFLUENCE_RADIUS;
      const hasHoveredCards = hoveredCardsRef.current.length > 0;

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
          // Only calculate color per-dot if cards are hovered (optimization)
          ctx.fillStyle = hasHoveredCards ? getDotColor(dot.x, dot.y) : DEFAULT_COLOR;
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
    let resizeObserver;
    if (typeof ResizeObserver !== 'undefined') {
      const wrapper = canvas.parentElement;
      const section = wrapper?.parentElement;
      if (section) {
        resizeObserver = new ResizeObserver(() => resizeCanvas());
        resizeObserver.observe(section);
      }
    }
    animationFrameRef.current = requestAnimationFrame(drawDots);

    return () => {
      isMounted = false;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      if (resizeObserver) resizeObserver.disconnect();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [mounted, theme]);

  if (!mounted) return null;

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 0 }}>
      <canvas ref={canvasRef} className="w-full h-full pointer-events-none" aria-hidden="true" />
    </div>
  );
}
