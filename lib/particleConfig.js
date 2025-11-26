/**
 * Particle Animation Configuration
 * Constants and color palettes for particle system
 */

// Particle count and behavior
export const PARTICLE_COUNT = 180;
export const PARTICLE_MAX_SPEED = 24;
export const PARTICLE_CONNECTION_DISTANCE = 180;
export const MAX_CONNECTIONS_PER_PARTICLE = 5;

// Connection animation
export const BEAM_SEGMENT_SPACING = 12;
export const CONNECTION_FADE_IN_RATE = 4.2;
export const CONNECTION_FADE_OUT_RATE = 4.5; // Faster fade-out for cleaner disconnections
export const CONNECTION_FADE_THRESHOLD = 0.85; // Start fading earlier (at 85% of max distance)

// Camera system
export const CAMERA_ORBIT_SPEED = Math.PI / 60;
export const CAMERA_ROLL_SPEED = 0.18;
export const CAMERA_ROLL_AMPLITUDE = 0.12;
export const CAMERA_SCALE_AMPLITUDE = 0.022;
export const CAMERA_CENTER_SMOOTHING = 0.06;
export const CAMERA_OFFSET_RATIO = 0.12;
export const CAMERA_OFFSET_MAX_RATIO = 0.2;
export const CAMERA_MIN_OFFSET = 36;
export const CAMERA_VERTICAL_OFFSET_FACTOR = 0.28;

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
