'use client';

import { useState, useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';

export default function InteractiveGridDots() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });
  const hoveredCardsRef = useRef([]);
  const animationFrameRef = useRef(null);
  const twinkleStatesRef = useRef(new Map());
  const lastTwinkleCheckRef = useRef(Date.now());
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let isMounted = true;

    // Configuration
    const DOT_SPACING = 25;
    const BASE_DOT_SIZE = 0;
    const MAX_DOT_SIZE = 6;
    const INFLUENCE_RADIUS = 100;
    
    // Twinkle configuration
    const TWINKLE_PROBABILITY = 0.008; // 0.8% of dots can twinkle (more frequent)
    const TWINKLE_DURATION = 4000; // 4 seconds per twinkle cycle (slower)
    const MAX_TWINKLE_SIZE = 8; // Maximum size during twinkle

    // Colors based on theme and position
    const getDotColor = (x, y) => {
      const sectionRect = canvas.parentElement?.parentElement?.getBoundingClientRect();
      if (!sectionRect) {
        return theme === 'dark' ? 'rgba(129, 178, 154, 0.4)' : 'rgba(224, 122, 95, 0.35)';
      }

      // Check if dot is behind any hovered card
      let isBehindCard = false;
      for (const cardRect of hoveredCardsRef.current) {
        const dotAbsoluteX = x + sectionRect.left;
        const dotAbsoluteY = y + sectionRect.top;
        
        if (
          dotAbsoluteX >= cardRect.left &&
          dotAbsoluteX <= cardRect.right &&
          dotAbsoluteY >= cardRect.top &&
          dotAbsoluteY <= cardRect.bottom
        ) {
          isBehindCard = true;
          break;
        }
      }

      // Both modes: Greenish default, Orangish behind card (using dark mode colors)
      if (theme === 'dark') {
        return isBehindCard 
          ? 'rgba(224, 122, 95, 0.6)' // Orangish when behind card
          : 'rgba(129, 178, 154, 0.4)'; // Greenish default
      } else {
        return isBehindCard
          ? 'rgba(224, 122, 95, 0.6)' // Orangish when behind card
          : 'rgba(129, 178, 154, 0.4)'; // Greenish default
      }
    };

    const resizeCanvas = () => {
      const wrapper = canvas.parentElement;
      if (!wrapper) return;

      const parent = wrapper.parentElement;
      if (!parent) return;

      const rect = parent.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;

      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;

      // Reset transform before scaling
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
    };

    const handleMouseMove = (e) => {
      const wrapper = canvas.parentElement;
      const section = wrapper?.parentElement;
      if (!section) return;

      const rect = section.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Check if mouse is within section bounds
      if (x >= 0 && x <= rect.width && y >= 0 && y <= rect.height) {
        mouseRef.current = { x, y };
      } else {
        mouseRef.current = { x: -1000, y: -1000 };
      }
    };

    const handleMouseLeave = () => {
      mouseRef.current = { x: -1000, y: -1000 };
    };

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

    // Get or create twinkle state for a dot
    const getTwinkleState = (dotKey, currentTime) => {
      const twinkleStates = twinkleStatesRef.current;
      
      if (!twinkleStates.has(dotKey)) {
        // Randomly decide if this dot should ever twinkle
        if (Math.random() < TWINKLE_PROBABILITY) {
          // Create a unique random seed based on the dot key for consistent randomness
          const seed = dotKey.split('-').reduce((acc, val) => acc + parseInt(val) * 7919, 0);
          const seededRandom = (seed * 9301 + 49297) % 233280 / 233280;
          
          // Assign a widely distributed random start time (spread across multiple cycles)
          const phaseOffset = seededRandom * TWINKLE_DURATION * 3; // Spread across 3 full cycles
          
          // Randomly select twinkle color from the theme's color palette
          const useAlternateColor = (seed % 2) === 0;
          
          twinkleStates.set(dotKey, {
            canTwinkle: true,
            startTime: currentTime - phaseOffset, // Start in the past for immediate variety
            phaseOffset,
            useAlternateColor
          });
        } else {
          twinkleStates.set(dotKey, { canTwinkle: false });
        }
      }
      
      return twinkleStates.get(dotKey);
    };
    
    // Get twinkle color based on theme and random selection
    const getTwinkleColor = (twinkleState) => {
      if (!twinkleState.canTwinkle) return null;
      
      // Both modes use same colors: default greenish, alternate orangish
      return twinkleState.useAlternateColor
        ? 'rgba(224, 122, 95, 0.8)' // Orangish
        : 'rgba(129, 178, 154, 0.6)'; // Greenish
    };

    // Calculate twinkle intensity (0 to 1) based on sine wave
    const getTwinkleIntensity = (twinkleState, currentTime) => {
      if (!twinkleState.canTwinkle) return 0;
      
      const elapsed = currentTime - twinkleState.startTime;
      const phase = (elapsed % TWINKLE_DURATION) / TWINKLE_DURATION;
      
      // Use sine wave for smooth twinkle: peaks at 0.5, valleys at 0 and 1
      const intensity = Math.sin(phase * Math.PI * 2) * 0.5 + 0.5;
      
      // Add occasional "skip" - randomly pause twinkling
      const skipChance = Math.sin(elapsed / 5000) * 0.5 + 0.5;
      return intensity * skipChance;
    };

    const drawDots = () => {
      if (!isMounted) return;

      const rect = canvas.getBoundingClientRect();
      const width = rect.width;
      const height = rect.height;

      if (width === 0 || height === 0) {
        animationFrameRef.current = requestAnimationFrame(drawDots);
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Update hovered cards before drawing
      updateHoveredCards();

      const cols = Math.ceil(width / DOT_SPACING);
      const rows = Math.ceil(height / DOT_SPACING);

      const mouse = mouseRef.current;
      const currentTime = Date.now();

      for (let row = 0; row <= rows; row++) {
        for (let col = 0; col <= cols; col++) {
          const x = col * DOT_SPACING + 2;
          const y = row * DOT_SPACING + 2;

          // Create unique key for this dot position
          const dotKey = `${col}-${row}`;

          // Calculate distance from mouse
          const dx = x - mouse.x;
          const dy = y - mouse.y;
          const distance = Math.sqrt(dx * dx + dy * dy);

          // Calculate size based on distance
          let dotSize = BASE_DOT_SIZE;
          if (distance < INFLUENCE_RADIUS) {
            const influence = 1 - (distance / INFLUENCE_RADIUS);
            dotSize = BASE_DOT_SIZE + (MAX_DOT_SIZE - BASE_DOT_SIZE) * influence;
          }

          // Get twinkle state and apply twinkle effect
          const twinkleState = getTwinkleState(dotKey, currentTime);
          const twinkleIntensity = getTwinkleIntensity(twinkleState, currentTime);
          
          // Apply twinkle: increase size and brightness
          if (twinkleIntensity > 0) {
            dotSize = Math.max(dotSize, BASE_DOT_SIZE + twinkleIntensity * MAX_TWINKLE_SIZE);
          }

          // Only draw if dot has size
          if (dotSize > 0) {
            // Get color based on position (checks if behind card)
            let dotColor = getDotColor(x, y);
            
            // Use twinkle color if actively twinkling
            if (twinkleIntensity > 0.3) {
              const twinkleColor = getTwinkleColor(twinkleState);
              if (twinkleColor) {
                // Blend between normal color and twinkle color based on intensity
                dotColor = twinkleColor;
              }
            }

            ctx.beginPath();
            ctx.fillStyle = dotColor;
            ctx.filter = 'blur(4px)';
            ctx.arc(x, y, dotSize, 0, Math.PI * 2);
            ctx.fill();
            ctx.filter = 'none';
          }
        }
      }

      animationFrameRef.current = requestAnimationFrame(drawDots);
    };

    resizeCanvas();
    
    // Use document-level mouse tracking to detect mouse even over higher z-index elements
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);

    let resizeObserver;
    if (typeof ResizeObserver !== 'undefined') {
      const wrapper = canvas.parentElement;
      const section = wrapper?.parentElement;
      if (section) {
        resizeObserver = new ResizeObserver(resizeCanvas);
        resizeObserver.observe(section);
      }
    } else {
      window.addEventListener('resize', resizeCanvas);
    }

    animationFrameRef.current = requestAnimationFrame(drawDots);

    return () => {
      isMounted = false;
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);

      if (resizeObserver) {
        resizeObserver.disconnect();
      } else {
        window.removeEventListener('resize', resizeCanvas);
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      ctx.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [mounted, theme]);

  if (!mounted) return null;

  return (
    <div className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
      <canvas
        ref={canvasRef}
        className="w-full h-full pointer-events-none"
        aria-hidden="true"
      />
    </div>
  );
}
