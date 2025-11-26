'use client';

import { useState, useEffect, useRef } from 'react';
import { useTheme } from 'next-themes';
import {
  PARTICLE_COUNT,
  PARTICLE_MAX_SPEED,
  PARTICLE_CONNECTION_DISTANCE,
  MAX_CONNECTIONS_PER_PARTICLE,
  PARTICLE_COLORS_LIGHT,
  PARTICLE_COLORS_DARK,
  BEAM_SEGMENT_SPACING,
  CONNECTION_FADE_IN_RATE,
  CONNECTION_FADE_OUT_RATE,
  CONNECTION_FADE_THRESHOLD,
  CAMERA_ORBIT_SPEED,
  CAMERA_ROLL_SPEED,
  CAMERA_ROLL_AMPLITUDE,
  CAMERA_SCALE_AMPLITUDE,
  CAMERA_CENTER_SMOOTHING,
  CAMERA_OFFSET_RATIO,
  CAMERA_OFFSET_MAX_RATIO,
  CAMERA_MIN_OFFSET,
  CAMERA_VERTICAL_OFFSET_FACTOR,
} from '@/lib/particleConfig';
import { parseRgba, rgbaToString, interpolateColor } from '@/lib/particleUtils';

export default function ParticleBackground() {
  const containerRef = useRef(null);
  const canvasRef = useRef(null);
  const animationFrameRef = useRef(null);
  const lastFrameTimestampRef = useRef(null);
  const particlesRef = useRef([]);
  const connectionStatesRef = useRef(new Map());
  const boundsRef = useRef({ width: 0, height: 0 });
  const cameraRef = useRef({
    angle: Math.random() * Math.PI * 2,
    rollPhase: Math.random() * Math.PI * 2,
    centerX: null,
    centerY: null,
    offsetX: 0,
    offsetY: 0,
    roll: 0,
    enabled: true,
  });

  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Ensure component only renders on client (Next.js SSR safety)
  useEffect(() => {
    setMounted(true);
  }, []);

  // Main animation effect
  useEffect(() => {
    if (!mounted) return;

    const container = containerRef.current;
    const canvas = canvasRef.current;

    if (!container || !canvas) {
      return undefined;
    }

    const context = canvas.getContext('2d');
    if (!context) {
      return undefined;
    }

    let isMounted = true;
    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Select color palette based on theme
    const PARTICLE_COLORS = theme === 'dark' 
      ? PARTICLE_COLORS_DARK 
      : PARTICLE_COLORS_LIGHT;

    // Check if mobile device (reduce particle count)
    const isMobile = typeof window !== 'undefined' && window.innerWidth < 768;
    const targetParticleCount = prefersReducedMotion ? 0 : (isMobile ? 100 : PARTICLE_COUNT);
    
    cameraRef.current.enabled = targetParticleCount > 0;
    if (!cameraRef.current.enabled) {
      cameraRef.current.centerX = null;
      cameraRef.current.centerY = null;
      cameraRef.current.offsetX = 0;
      cameraRef.current.offsetY = 0;
      cameraRef.current.angle = 0;
      cameraRef.current.rollPhase = 0;
      cameraRef.current.roll = 0;
    }

    const createParticle = (width, height) => {
      const palette = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
      const baseColor = parseRgba(palette.fill);
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * PARTICLE_MAX_SPEED,
        vy: (Math.random() - 0.5) * PARTICLE_MAX_SPEED,
        radius: Math.random() * 1.2 + 0.8,
        color: baseColor,
        colorString: rgbaToString(baseColor),
      };
    };

    const resizeCanvas = () => {
      // Get the actual viewport dimensions (not container dimensions)
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;
      const devicePixelRatio = window.devicePixelRatio || 1;

      // Set canvas dimensions to match viewport with pixel ratio for sharp rendering
      canvas.width = viewportWidth * devicePixelRatio;
      canvas.height = viewportHeight * devicePixelRatio;
      
      // Set CSS dimensions to viewport size
      canvas.style.width = `${viewportWidth}px`;
      canvas.style.height = `${viewportHeight}px`;

      // Apply device pixel ratio transformation
      context.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);

      // Store previous dimensions for particle scaling
      const previousWidth = boundsRef.current.width || viewportWidth;
      const previousHeight = boundsRef.current.height || viewportHeight;
      
      // Update bounds to current viewport dimensions
      boundsRef.current = { width: viewportWidth, height: viewportHeight };

      // Scale existing particles proportionally when viewport changes
      if (previousWidth && previousHeight) {
        const scaleX = viewportWidth / previousWidth;
        const scaleY = viewportHeight / previousHeight;
        particlesRef.current.forEach((particle) => {
          particle.x *= scaleX;
          particle.y *= scaleY;
        });
      }
    };

    resizeCanvas();

    particlesRef.current = [];
    for (let i = 0; i < targetParticleCount; i += 1) {
      particlesRef.current.push(
        createParticle(boundsRef.current.width, boundsRef.current.height)
      );
    }

    // Dynamic buffer based on viewport size for smooth edge wrapping
    const getBuffer = () => {
      const minDimension = Math.min(boundsRef.current.width, boundsRef.current.height);
      return Math.max(20, Math.min(50, minDimension * 0.03));
    };

    const step = (timestamp) => {
      if (!isMounted) {
        return;
      }

      const { width, height } = boundsRef.current;
      if (!width || !height) {
        animationFrameRef.current = requestAnimationFrame(step);
        return;
      }

      const lastTimestamp = lastFrameTimestampRef.current ?? timestamp;
      const delta = Math.min((timestamp - lastTimestamp) / 1000, 0.05);
      lastFrameTimestampRef.current = timestamp;

      context.clearRect(0, 0, width, height);

      const particles = particlesRef.current;
      const buffer = getBuffer();
      let sumX = 0;
      let sumY = 0;

      for (let i = 0; i < particles.length; i += 1) {
        const particle = particles[i];
        particle.x += particle.vx * delta;
        particle.y += particle.vy * delta;

        // Wrap particles around viewport edges with dynamic buffer
        if (particle.x < -buffer) {
          particle.x = width + buffer;
        } else if (particle.x > width + buffer) {
          particle.x = -buffer;
        }

        if (particle.y < -buffer) {
          particle.y = height + buffer;
        } else if (particle.y > height + buffer) {
          particle.y = -buffer;
        }

        sumX += particle.x;
        sumY += particle.y;
      }

      const hasParticles = particles.length > 0;
      const targetCenterX = hasParticles ? sumX / particles.length : width / 2;
      const targetCenterY = hasParticles ? sumY / particles.length : height / 2;

      const camera = cameraRef.current;
      if (!camera.enabled) {
        camera.centerX = targetCenterX;
        camera.centerY = targetCenterY;
        camera.offsetX = 0;
        camera.offsetY = 0;
        camera.angle = 0;
        camera.rollPhase = camera.rollPhase ?? 0;
        camera.roll = 0;
      } else {
        if (camera.centerX == null || camera.centerY == null) {
          camera.centerX = targetCenterX;
          camera.centerY = targetCenterY;
        } else {
          camera.centerX += (targetCenterX - camera.centerX) * CAMERA_CENTER_SMOOTHING;
          camera.centerY += (targetCenterY - camera.centerY) * CAMERA_CENTER_SMOOTHING;
        }

        // Calculate camera orbit offset dynamically based on viewport size
        const minDimension = Math.min(width, height);
        const maxDimension = Math.max(width, height);
        const aspectRatio = width / height;
        
        // Adjust offset calculation for different aspect ratios
        const baseOffset = minDimension * CAMERA_OFFSET_RATIO * (aspectRatio > 1 ? 1.1 : 0.9);
        const maxOffset = minDimension * CAMERA_OFFSET_MAX_RATIO;
        const orbitOffset = Math.max(CAMERA_MIN_OFFSET, Math.min(maxOffset, baseOffset));

        camera.angle = (camera.angle + CAMERA_ORBIT_SPEED * delta) % (Math.PI * 2);
        camera.rollPhase = (camera.rollPhase ?? Math.random() * Math.PI * 2) + CAMERA_ROLL_SPEED * delta;

        const desiredOffsetX = orbitOffset * Math.cos(camera.angle);
        const desiredOffsetY = orbitOffset * CAMERA_VERTICAL_OFFSET_FACTOR * Math.sin(camera.angle);

        camera.offsetX = (camera.offsetX ?? 0) + (desiredOffsetX - (camera.offsetX ?? 0)) * 0.12;
        camera.offsetY = (camera.offsetY ?? 0) + (desiredOffsetY - (camera.offsetY ?? 0)) * 0.12;
        camera.roll = Math.sin(camera.rollPhase) * CAMERA_ROLL_AMPLITUDE;
      }

      const cameraCenterX = camera.centerX ?? targetCenterX;
      const cameraCenterY = camera.centerY ?? targetCenterY;

      context.save();

      if (camera.enabled) {
        context.translate(cameraCenterX, cameraCenterY);
        context.rotate(camera.roll || 0);
        const scaleX = 1 + Math.sin(camera.angle * 1.4) * CAMERA_SCALE_AMPLITUDE;
        const scaleY = 1 - Math.sin(camera.angle * 1.4) * CAMERA_SCALE_AMPLITUDE * 0.65;
        context.scale(scaleX, scaleY);
        context.translate(-cameraCenterX, -cameraCenterY);
        context.translate(-(camera.offsetX ?? 0), -(camera.offsetY ?? 0));
      }

      // Theme-aware fog gradient
      const breathPhase = Math.sin(timestamp * 0.0008) * 0.5 + 0.5;
      const fogDepth = 0.045 + breathPhase * 0.015;
      const gradientRadius = Math.hypot(width, height) * 0.6;
      const gradient = context.createRadialGradient(
        cameraCenterX,
        cameraCenterY,
        gradientRadius * 0.15,
        cameraCenterX,
        cameraCenterY,
        gradientRadius
      );

      // Fog color adapts to theme
      if (theme === 'dark') {
        // Dark mode: Light subtle fog (muted-teal tint)
        gradient.addColorStop(0, `rgba(129, 178, 154, ${fogDepth * 0.25})`);
        gradient.addColorStop(0.5, `rgba(129, 178, 154, ${fogDepth * 0.15})`);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      } else {
        // Light mode: Dark subtle fog (twilight tint)
        gradient.addColorStop(0, `rgba(61, 64, 91, ${fogDepth * 0.15})`);
        gradient.addColorStop(0.5, `rgba(61, 64, 91, ${fogDepth * 0.08})`);
        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
      }

      context.save();
      context.globalCompositeOperation = 'source-over';
      context.fillStyle = gradient;
      context.fillRect(0, 0, width, height);
      context.restore();

      for (let i = 0; i < particles.length; i += 1) {
        const particle = particles[i];
        context.beginPath();
        context.fillStyle = particle.colorString;
        context.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
        context.fill();
      }

      const connectionStates = connectionStatesRef.current;
      connectionStates.forEach((state) => {
        state.active = false;
      });

      const potentialConnections = [];

      for (let i = 0; i < particles.length; i += 1) {
        const a = particles[i];
        for (let j = i + 1; j < particles.length; j += 1) {
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const distanceSq = dx * dx + dy * dy;
          if (distanceSq > PARTICLE_CONNECTION_DISTANCE * PARTICLE_CONNECTION_DISTANCE) {
            continue;
          }

          const distance = Math.sqrt(distanceSq);
          const connectionStrength = 1 - distance / PARTICLE_CONNECTION_DISTANCE;
          if (connectionStrength <= 0) {
            continue;
          }

          potentialConnections.push({
            key: `${i}-${j}`,
            i,
            j,
            distance,
            connectionStrength,
          });
        }
      }

      if (potentialConnections.length > 0) {
        potentialConnections.sort((left, right) => right.distance - left.distance);
        const connectionCounts = new Uint8Array(particles.length);

        for (let index = 0; index < potentialConnections.length; index += 1) {
          const candidate = potentialConnections[index];
          const { i, j, key, connectionStrength } = candidate;

          if (
            connectionCounts[i] >= MAX_CONNECTIONS_PER_PARTICLE ||
            connectionCounts[j] >= MAX_CONNECTIONS_PER_PARTICLE
          ) {
            continue;
          }

          connectionCounts[i] += 1;
          connectionCounts[j] += 1;

          let state = connectionStates.get(key);
          if (!state) {
            state = {
              progress: 0,
              source: i,
              target: j,
              connectionStrength,
            };
            connectionStates.set(key, state);
          }

          state.source = i;
          state.target = j;
          state.connectionStrength = connectionStrength;
          state.active = true;
        }
      }

      const connectionsToRender = [];

      connectionStates.forEach((state, key) => {
        const a = particles[state.source];
        const b = particles[state.target];

        if (!a || !b) {
          connectionStates.delete(key);
          return;
        }

        const dx = a.x - b.x;
        const dy = a.y - b.y;
        const distanceSq = dx * dx + dy * dy;
        const distance = Math.sqrt(distanceSq);

        if (!Number.isFinite(distance) || distance <= 0) {
          if (!state.active) {
            connectionStates.delete(key);
          }
          return;
        }

        const normalizedDistance = Math.min(distance, PARTICLE_CONNECTION_DISTANCE);
        let baseStrength = Math.max(0, 1 - normalizedDistance / PARTICLE_CONNECTION_DISTANCE);
        
        // Apply gradual distance-based fade when approaching max distance
        const fadeThreshold = PARTICLE_CONNECTION_DISTANCE * CONNECTION_FADE_THRESHOLD;
        if (distance > fadeThreshold) {
          const fadeZone = PARTICLE_CONNECTION_DISTANCE - fadeThreshold;
          const fadeAmount = (distance - fadeThreshold) / fadeZone;
          baseStrength *= (1 - fadeAmount * 0.5); // Reduce strength by up to 50% in fade zone
        }

        // Update progress based on active state - fade in when active, fade out when inactive
        if (state.active) {
          state.progress = Math.min(1, (state.progress ?? 0) + CONNECTION_FADE_IN_RATE * delta);
        } else {
          // Always fade out when inactive, regardless of distance
          state.progress = Math.max(0, (state.progress ?? 0) - CONNECTION_FADE_OUT_RATE * delta);
        }

        // Delete connection only after it has completely faded out
        if (state.progress <= 0.001) {
          connectionStates.delete(key);
          return;
        }

        state.connectionStrength = baseStrength;
        state.distance = distance;

        // Render connection if it has any visible progress
        // Even if baseStrength is 0, we render during fade-out with previous strength
        if (state.progress > 0.001) {
          connectionsToRender.push({ state, a, b });
        }
      });

      if (connectionsToRender.length > 0) {
        for (let idx = 0; idx < connectionsToRender.length; idx += 1) {
          const { state, a, b } = connectionsToRender[idx];
          const fade = state.progress;
          
          if (fade <= 0.001) {
            continue;
          }

          // Use current strength, or maintain last strength during fade-out for smooth transition
          let strength = state.connectionStrength;
          
          // Store the peak strength when connection becomes inactive for smooth fade-out
          if (!state.active && !state.lastActiveStrength) {
            state.lastActiveStrength = strength;
          }
          
          // During fade-out, use the stored strength for consistent visual appearance
          if (!state.active && state.lastActiveStrength) {
            strength = Math.max(strength, state.lastActiveStrength * 0.8);
          }
          
          // Clear stored strength when connection becomes active again
          if (state.active) {
            state.lastActiveStrength = null;
          }

          const segments = Math.max(2, Math.ceil(state.distance / BEAM_SEGMENT_SPACING));
          const beamRadius = ((a.radius + b.radius) / 2) * (0.5 + strength * 0.7) * (0.55 + fade * 0.45);
          
          // Theme-aware connection alpha with smooth fade-out
          const alphaBase = theme === 'dark' ? 0.4 : 0.35;
          const alphaBoost = (alphaBase + strength * 0.45) * fade;

          for (let s = 1; s < segments; s += 1) {
            const t = s / segments;
            const x = a.x + (b.x - a.x) * t;
            const y = a.y + (b.y - a.y) * t;
            const blended = interpolateColor(a.color, b.color, t);
            blended.a = Math.min(1, ((a.color.a + b.color.a) / 2) * alphaBoost);

            context.beginPath();
            context.fillStyle = rgbaToString(blended);
            context.arc(x, y, beamRadius, 0, Math.PI * 2);
            context.fill();
          }
        }
      }

      context.restore();

      animationFrameRef.current = requestAnimationFrame(step);
    };

    // Handle viewport resize with multiple listeners for comprehensive coverage
    const handleResize = () => {
      resizeCanvas();
    };

    const handleOrientationChange = () => {
      // Delay to allow browser to update viewport dimensions
      setTimeout(resizeCanvas, 100);
    };

    let resizeObserver;
    
    // Use ResizeObserver for container size changes
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(handleResize);
      resizeObserver.observe(container);
    }
    
    // Also listen to window events for comprehensive coverage
    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // Handle mobile viewport height changes (address bar show/hide)
    if ('visualViewport' in window) {
      window.visualViewport.addEventListener('resize', handleResize);
    }

    animationFrameRef.current = requestAnimationFrame(step);

    return () => {
      isMounted = false;

      if (resizeObserver) {
        resizeObserver.disconnect();
      }
      
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
      
      if ('visualViewport' in window && window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      }

      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }

      particlesRef.current = [];

      context.setTransform(1, 0, 0, 1, 0, 0);
      context.clearRect(0, 0, canvas.width, canvas.height);
    };
  }, [mounted, theme]);

  // Update particle colors when theme changes (smooth transition)
  useEffect(() => {
    if (!mounted || particlesRef.current.length === 0) return;

    const newColors = theme === 'dark' 
      ? PARTICLE_COLORS_DARK 
      : PARTICLE_COLORS_LIGHT;

    particlesRef.current.forEach((particle, index) => {
      const palette = newColors[index % newColors.length];
      particle.color = parseRgba(palette.fill);
      particle.colorString = rgbaToString(particle.color);
    });
  }, [theme, mounted]);

  if (!mounted) return null; // Prevent SSR mismatch

  return (
    <div ref={containerRef} className="particle-container" aria-hidden="true">
      <canvas ref={canvasRef} className="particle-lines-canvas" />
    </div>
  );
}
