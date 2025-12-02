/**
 * Particle Animation Configuration
 * Constants and color palettes for particle system
 * OPTIMIZED FOR STATIC HOSTING - Reduced counts and simplified calculations
 */

// Particle count and behavior - REDUCED for performance
export const PARTICLE_COUNT = 60; // Reduced from 180 for better CPU performance
export const PARTICLE_COUNT_MOBILE = 25; // Even fewer on mobile
export const PARTICLE_MAX_SPEED = 18; // Slightly slower for smoother appearance
export const PARTICLE_CONNECTION_DISTANCE = 120; // Reduced connection range
export const MAX_CONNECTIONS_PER_PARTICLE = 3; // Fewer connections per particle

// Connection animation - Simplified
export const BEAM_SEGMENT_SPACING = 20; // Fewer segments = fewer draw calls
export const CONNECTION_FADE_IN_RATE = 3.0;
export const CONNECTION_FADE_OUT_RATE = 3.5;
export const CONNECTION_FADE_THRESHOLD = 0.8;

// Performance settings
export const TARGET_FPS = 30; // Target 30fps for better battery/CPU
export const FRAME_TIME = 1000 / TARGET_FPS;
export const VISIBILITY_CHECK_INTERVAL = 500; // Check visibility every 500ms

// Camera system - Simplified
export const CAMERA_ENABLED = false; // Disabled for performance - simple is better
export const CAMERA_ORBIT_SPEED = Math.PI / 90; // Slower orbit
export const CAMERA_ROLL_SPEED = 0.1;
export const CAMERA_ROLL_AMPLITUDE = 0.06; // Reduced amplitude
export const CAMERA_SCALE_AMPLITUDE = 0.01; // Reduced scale effect
export const CAMERA_CENTER_SMOOTHING = 0.04;
export const CAMERA_OFFSET_RATIO = 0.08;
export const CAMERA_OFFSET_MAX_RATIO = 0.15;
export const CAMERA_MIN_OFFSET = 24;
export const CAMERA_VERTICAL_OFFSET_FACTOR = 0.2;

// Light Mode: Darker, saturated particles for contrast against light background
export const PARTICLE_COLORS_LIGHT = [
  { fill: 'rgba(200, 90, 65, 0.85)' },   // burnt-peach (darker, more saturated)
  { fill: 'rgba(45, 48, 75, 0.75)' },    // twilight (darker, more saturated)
  { fill: 'rgba(95, 150, 125, 0.8)' },   // muted-teal (darker, more saturated)
  { fill: 'rgba(220, 170, 95, 0.75)' },  // apricot (darker, more saturated)
  { fill: 'rgba(190, 65, 45, 0.8)' },    // darker burnt-peach variant (more saturated)
];

// Dark Mode: Brighter, luminous particles for contrast against dark background
export const PARTICLE_COLORS_DARK = [
  { fill: 'rgba(255, 150, 130, 0.7)' },  // bright burnt-peach
  { fill: 'rgba(150, 220, 200, 0.65)' }, // bright muted-teal
  { fill: 'rgba(255, 230, 180, 0.6)' },  // bright apricot
  { fill: 'rgba(180, 200, 220, 0.6)' },  // light twilight (brightened)
  { fill: 'rgba(244, 241, 222, 0.55)' }, // eggshell (light neutral)
];
