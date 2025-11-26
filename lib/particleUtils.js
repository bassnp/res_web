/**
 * Particle Animation Utility Functions
 * Helper functions for color parsing, conversion, and interpolation
 */

/**
 * Parse an rgba() or rgb() string into a color object
 * @param {string} value - CSS rgba/rgb color string
 * @returns {Object} Color object with r, g, b, a properties
 */
export const parseRgba = (value) => {
  if (typeof value !== 'string') {
    return { r: 255, g: 255, b: 255, a: 1 };
  }

  const matches = value.match(/rgba?\(([^)]+)\)/i);
  if (!matches) {
    return { r: 255, g: 255, b: 255, a: 1 };
  }

  const parts = matches[1]
    .split(',')
    .map((part) => parseFloat(part.trim()))
    .filter((part) => Number.isFinite(part));

  const [r = 255, g = 255, b = 255, a = 1] = parts;
  return { r, g, b, a };
};

/**
 * Convert a color object to an rgba() CSS string
 * @param {Object} color - Color object with r, g, b, a properties
 * @returns {string} CSS rgba() color string
 */
export const rgbaToString = ({ r, g, b, a }) =>
  `rgba(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)}, ${Math.min(Math.max(a, 0), 1)})`;

/**
 * Interpolate between two colors
 * @param {Object} start - Starting color object
 * @param {Object} end - Ending color object
 * @param {number} t - Interpolation factor (0 to 1)
 * @returns {Object} Interpolated color object
 */
export const interpolateColor = (start, end, t) => ({
  r: start.r + (end.r - start.r) * t,
  g: start.g + (end.g - start.g) * t,
  b: start.b + (end.b - start.b) * t,
  a: start.a + (end.a - start.a) * t,
});
