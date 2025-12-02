'use client';

import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for responsive header visibility control.
 * 
 * Behavior:
 * - Header hides ONLY after scrolling down past a defined threshold
 * - Header shows IMMEDIATELY when ANY upward scroll is detected
 * - Prioritizes rapid navigational access regardless of vertical position
 * 
 * @param {Object} options - Configuration options
 * @param {number} options.hideThreshold - Pixels to scroll down before hiding (default: 100)
 * @param {number} options.showDelay - Delay before showing header on scroll up in ms (default: 0 for immediate)
 * @returns {Object} { isVisible, isAtTop }
 */
export function useHeaderVisibility({ 
  hideThreshold = 100,
  showDelay = 0 
} = {}) {
  const [isVisible, setIsVisible] = useState(true);
  const [isAtTop, setIsAtTop] = useState(true);
  
  const lastScrollY = useRef(0);
  const ticking = useRef(false);
  const showTimeoutRef = useRef(null);

  const updateVisibility = useCallback(() => {
    const currentScrollY = window.scrollY;
    const scrollDirection = currentScrollY > lastScrollY.current ? 'down' : 'up';
    const scrollDelta = Math.abs(currentScrollY - lastScrollY.current);
    
    // Update isAtTop state
    setIsAtTop(currentScrollY < 10);
    
    // Ignore tiny scroll movements (debounce jitter)
    if (scrollDelta < 5) {
      ticking.current = false;
      return;
    }

    // Clear any pending show timeout
    if (showTimeoutRef.current) {
      clearTimeout(showTimeoutRef.current);
      showTimeoutRef.current = null;
    }

    if (scrollDirection === 'up') {
      // IMMEDIATE restoration on upward scroll - prioritize navigational access
      if (showDelay === 0) {
        setIsVisible(true);
      } else {
        showTimeoutRef.current = setTimeout(() => {
          setIsVisible(true);
        }, showDelay);
      }
    } else if (scrollDirection === 'down' && currentScrollY > hideThreshold) {
      // Hide ONLY after passing the threshold while scrolling down
      setIsVisible(false);
    }
    
    lastScrollY.current = currentScrollY;
    ticking.current = false;
  }, [hideThreshold, showDelay]);

  const handleScroll = useCallback(() => {
    if (!ticking.current) {
      // Use requestAnimationFrame for smooth, performant updates
      requestAnimationFrame(updateVisibility);
      ticking.current = true;
    }
  }, [updateVisibility]);

  useEffect(() => {
    // Initialize scroll position
    lastScrollY.current = window.scrollY;
    setIsAtTop(window.scrollY < 10);
    
    // Add scroll listener with passive flag for performance
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (showTimeoutRef.current) {
        clearTimeout(showTimeoutRef.current);
      }
    };
  }, [handleScroll]);

  return { isVisible, isAtTop };
}

export default useHeaderVisibility;
