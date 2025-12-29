'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import { useTheme } from 'next-themes';
import { Briefcase, Mail, Github, Linkedin, ChevronDown, ChevronLeft, ChevronRight, ExternalLink, Sun, Moon, Code, FileText, Camera, Eye, Clock, Menu, X, Brain } from 'lucide-react';
import { useHeaderVisibility } from '@/hooks/use-header-visibility';
import { InfoDialog, InfoButton } from '@/components/fit-check/InfoDialog';
import { ProjectModal, ReadSummaryButton } from '@/components/ProjectModal';
import { Button } from '@/components/ui/button';
import ParticleBackground from '@/components/ParticleBackground';
import InteractiveGridDots from '@/components/InteractiveGridDots';
import CardGridDots from '@/components/CardGridDots';
import HeroGridDots from '@/components/HeroGridDots';
import FitCheckSection from '@/components/FitCheckSection';
import { 
  HERO_TEXT, 
  PRIMARY_SKILLS, 
  DEVOPS_SKILLS, 
  FEATURED_PROJECTS, 
  PRIMARY_EDUCATION,
  EMAIL,
  GITHUB_URL,
  GITHUB_USERNAME,
  REPO_URL,
  PORTRAIT_PATH,
  PORTRAIT_ALT,
  BIO_TLDR,
  BIO_FULL,
  EXPERIENCE 
} from '@/lib/profile-data';

// ============================================
// PERSONAL COLLAGE IMAGE PATHS
// Fallback array - actual images loaded dynamically from manifest
// ============================================
const FALLBACK_COLLAGE_IMAGES = [
  '/resources/personal_collage/0.jpg',
];

// ============================================
// IMAGE CAROUSEL COMPONENT
// Rotating carousel that cycles through images
// with smooth right-to-left slide transitions.
// Loads images dynamically from manifest.json (alphanumerically sorted)
// ============================================
const HERO_SLIDE_DURATION = 500; // Slide animation duration in ms

const ImageCarousel = ({ interval = 4000 }) => {
  const [images, setImages] = useState(FALLBACK_COLLAGE_IMAGES);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [previousIndex, setPreviousIndex] = useState(null);
  const [isSliding, setIsSliding] = useState(false);
  const [slideDirection, setSlideDirection] = useState('right'); // 'left' or 'right'
  const timerRef = useRef(null);

  /**
   * Fetch image list from manifest on mount.
   * Falls back to hardcoded list if fetch fails.
   */
  useEffect(() => {
    fetch('/resources/collage_manifest.json')
      .then(res => res.json())
      .then(data => {
        if (data.images && data.images.length > 0) {
          setImages(data.images);
        }
      })
      .catch(() => {
        // Use fallback images if manifest fails to load
        console.warn('Failed to load collage manifest, using fallback images');
      });
  }, []);

  /**
   * Start or restart the auto-advance timer.
   * Called on mount and after any user interaction to reset the countdown.
   * Auto-advance always goes forward (right direction).
   */
  const startTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    timerRef.current = setInterval(() => {
      setSlideDirection('right');
      setCurrentIndex(prev => {
        const next = (prev + 1) % images.length;
        setPreviousIndex(prev);
        setIsSliding(true);
        setTimeout(() => {
          setIsSliding(false);
          setPreviousIndex(null);
        }, HERO_SLIDE_DURATION);
        return next;
      });
    }, interval);
  }, [images.length, interval]);

  /**
   * Trigger slide transition to a specific index with direction awareness.
   * Resets the auto-advance timer to prevent immediate jump after interaction.
   * 
   * @param {number} newIndex - Target image index
   * @param {string} direction - Animation direction: 'left' or 'right'
   */
  const slideToIndex = useCallback((newIndex, direction = 'right') => {
    if (isSliding || newIndex === currentIndex) return;
    
    setSlideDirection(direction);
    setPreviousIndex(currentIndex);
    setCurrentIndex(newIndex);
    setIsSliding(true);
    
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, HERO_SLIDE_DURATION);
    
    // Reset timer after user interaction
    startTimer();
  }, [isSliding, currentIndex, startTimer]);

  /**
   * Navigate to previous image (slides from left).
   * Timer is reset via slideToIndex.
   */
  const goToPrevious = useCallback(() => {
    const prevIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
    slideToIndex(prevIndex, 'left');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Navigate to next image (slides from right).
   * Timer is reset via slideToIndex.
   */
  const goToNext = useCallback(() => {
    const nextIndex = (currentIndex + 1) % images.length;
    slideToIndex(nextIndex, 'right');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Initialize auto-advance timer on mount and when images change.
   * Cleanup on unmount.
   */
  useEffect(() => {
    if (images.length <= 1) return;
    
    startTimer();
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [images.length, startTimer]);

  return (
    <div className="relative w-full h-full overflow-hidden rounded-[5px] group">
      {/* Previous image - slides out based on direction */}
      {previousIndex !== null && (
        <img
          src={images[previousIndex]}
          alt={`Personal photo ${previousIndex + 1}`}
          className={`absolute inset-0 w-full h-full object-cover ${
            slideDirection === 'right' ? 'animate-slide-out-left' : 'animate-slide-out-right'
          }`}
          style={{
            animationDuration: `${HERO_SLIDE_DURATION}ms`,
          }}
        />
      )}
      {/* Current image - slides in based on direction */}
      <img
        src={images[currentIndex]}
        alt={`Personal photo ${currentIndex + 1}`}
        className={`absolute inset-0 w-full h-full object-cover ${
          isSliding && previousIndex !== null 
            ? (slideDirection === 'right' ? 'animate-slide-in-right' : 'animate-slide-in-left')
            : ''
        }`}
        style={{
          animationDuration: `${HERO_SLIDE_DURATION}ms`,
        }}
      />
      {/* Navigation arrows - only show if more than 1 image */}
      {images.length > 1 && (
        <>
          {/* Left arrow */}
          <button
            onClick={goToPrevious}
            className="absolute left-2 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 hover:bg-muted-teal hover:scale-110"
            aria-label="Previous image"
          >
            <ChevronLeft className="w-5 h-5 text-eggshell" />
          </button>
          {/* Right arrow */}
          <button
            onClick={goToNext}
            className="absolute right-2 top-1/2 -translate-y-1/2 z-10 w-8 h-8 rounded-full bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 hover:bg-muted-teal hover:scale-110"
            aria-label="Next image"
          >
            <ChevronRight className="w-5 h-5 text-eggshell" />
          </button>
        </>
      )}
      {/* Image indicator dots - only show if more than 1 image */}
      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {images.map((_, idx) => (
            <button
              key={idx}
              onClick={() => slideToIndex(idx, idx > currentIndex ? 'right' : 'left')}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-300 ${
                idx === currentIndex
                  ? 'bg-burnt-peach scale-125'
                  : 'bg-eggshell/60 hover:bg-eggshell/80'
              }`}
              aria-label={`Go to image ${idx + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================
// HEADER COMPONENT
// ============================================
const Header = () => {
  const [infoOpen, setInfoOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  
  // Responsive visibility controller with scroll detection
  const { isVisible, isAtTop } = useHeaderVisibility({ 
    hideThreshold: 100,  // Hide after 100px scroll down
    showDelay: 0         // Immediate show on scroll up
  });

  useEffect(() => {
    setMounted(true);
    // On mount, if theme is 'system', resolve it to the actual system preference
    if (theme === 'system') {
      const systemPreference = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      setTheme(systemPreference);
    }
  }, []);

  const navItems = [
    { name: 'About', href: '#about' },
    { name: 'Fit Check', href: '#fit-check' },
    { name: 'Projects', href: '#projects' },
    { name: 'Experience', href: '#experience' },
    { name: 'Contact', href: '#contact' },
  ];

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  return (
    <header 
      className={`fixed top-0 left-0 right-0 z-50 overflow-visible transition-all duration-300 ease-out
        ${isVisible || mobileMenuOpen
          ? 'translate-y-0 opacity-100' 
          : '-translate-y-full opacity-0 pointer-events-none'
        }
      `}
      style={{
        transform: (isVisible || mobileMenuOpen) ? 'translateY(0)' : 'translateY(-100%)',
        transition: (isVisible || mobileMenuOpen) 
          ? 'transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.2s ease-out' 
          : 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.25s ease-in',
      }}
    >
      <div className="mx-auto px-[10%] py-4">
        <div className={`relative rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden transition-all duration-300
          ${!isAtTop && isVisible 
            ? 'bg-background/80 backdrop-blur-md' 
            : 'bg-background/95 backdrop-blur-sm'
          }
        `}>
          <InteractiveGridDots />
          <div className="relative z-10 p-1">
            <div className="flex items-center justify-between">
          {/* Theme Toggle (replaces Home Icon) */}
          {mounted && (
            <button 
              onClick={toggleTheme}
              className="group p-2 rounded-sm hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-all duration-300 hover:scale-110"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? (
                <Moon className="w-6 h-6 text-muted-teal transition-transform duration-300 group-hover:rotate-12" />
              ) : (
                <Sun className="w-6 h-6 text-burnt-peach transition-transform duration-300 group-hover:rotate-12" />
              )}
            </button>
          )}
          {!mounted && (
            <div className="p-2 w-10 h-10" />
          )}

              {/* Navigation */}
              <nav className="hidden md:flex items-center gap-1">
                {navItems.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    className="relative z-20 px-4 py-2 text-sm font-medium text-twilight dark:text-eggshell hover:text-eggshell transition-all duration-300 rounded-sm hover:bg-burnt-peach"
                  >
                    {item.name}
                  </a>
                ))}
              </nav>

              {/* Mobile Menu Toggle */}
              <button 
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-sm hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-all duration-300"
                aria-label="Toggle menu"
              >
                {mobileMenuOpen ? (
                  <X className="w-6 h-6 text-twilight dark:text-eggshell" />
                ) : (
                  <Menu className="w-6 h-6 text-twilight dark:text-eggshell" />
                )}
              </button>

              {/* Info */}
              <div className="flex items-center gap-1">
                {/* Info Button */}
                <InfoDialog 
                  open={infoOpen} 
                  onOpenChange={setInfoOpen}
                  trigger={<InfoButton onClick={() => {}} />}
                />
              </div>
            </div>

            {/* Mobile Navigation Menu */}
            {mobileMenuOpen && (
              <nav className="md:hidden flex flex-col gap-1 mt-1 pb-2 border-t border-twilight/10 dark:border-eggshell/10 animate-in fade-in slide-in-from-top-2 duration-300">
                {navItems.map((item) => (
                  <a
                    key={item.name}
                    href={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className="px-4 py-3 text-sm font-medium text-twilight dark:text-eggshell hover:text-eggshell transition-all duration-300 rounded-sm hover:bg-burnt-peach"
                  >
                    {item.name}
                  </a>
                ))}
              </nav>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

// ============================================
// FOOTER COMPONENT
// ============================================
const Footer = () => {
  const footerLinks = [
    { name: 'About', href: '#about' },
    { name: 'Projects', href: '#projects' },
    { name: 'Experience', href: '#experience' },
    { name: 'Contact', href: '#contact' },
  ];

  const socialLinks = [
    { icon: Github, href: GITHUB_URL, label: 'GitHub' },
    { icon: Linkedin, href: 'https://www.linkedin.com/in/jaden-b-519500233/', label: 'LinkedIn' },
    { icon: Mail, href: `mailto:${EMAIL}`, label: 'Email' },
  ];

  return (
    <footer className="text-twilight dark:text-eggshell py-6 relative z-20">
      <div className="max-w-4xl mx-auto px-6">
        <div className="relative bg-background/30 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-6">
          <InteractiveGridDots />
          <div className="relative z-10 px-8">
            {/* Main footer content */}
            <div className="grid md:grid-cols-4 gap-8">
              {/* Brand */}
              <div className="md:col-span-3">
                <h3 className="text-lg font-semibold mb-3">Whats next?</h3>
                <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">
                  Feel free to reach out to chat, collaborate, inquire, or just to say hi! I'm always open to meeting new people who share similar interets and passions, as well as people who also don't but still want to get in touch to talk anyways!
                </p>
              </div>

              {/* Contact */}
              <div className="md:col-start-4 flex flex-col md:items-end text-left md:text-right">
                <div className="flex gap-4 mb-3">
                  {socialLinks.map((social) => (
                    <a
                      key={social.label}
                      href={social.href}
                      className="p-2 rounded-sm bg-twilight/10 dark:bg-eggshell/10 hover:bg-burnt-peach/30 transition-all duration-300 hover:scale-110 hover:-translate-y-1"
                      aria-label={social.label}
                    >
                      <social.icon className="w-5 h-5" />
                    </a>
                  ))}
                </div>
                <p className="text-twilight/70 dark:text-eggshell/70 text-sm">
                  {EMAIL}
                </p>
              </div>
            </div>

            {/* Copyright */}
            <div className="mt-8 pt-6 border-t border-twilight/20 dark:border-eggshell/20 text-center">
              <p className="text-twilight/50 dark:text-eggshell/50 text-sm">
                &copy; {new Date().getFullYear()} Portfolio. No rights reserved haha.
              </p>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

// ============================================
// ANIMATED BACKGROUND SHAPES
// ============================================
const AnimatedShapes = () => {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {/* Morphing blob 1 */}
      <div className="absolute top-20 left-10 w-72 h-72 bg-burnt-peach/20 dark:bg-burnt-peach/30 rounded-full blur-3xl animate-float animate-morph" />
      {/* Morphing blob 2 */}
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-muted-teal/20 dark:bg-muted-teal/30 rounded-full blur-3xl animate-float-delayed animate-morph" style={{ animationDelay: '2s' }} />
      {/* Center glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-apricot/10 dark:bg-apricot/20 rounded-full blur-3xl" />
      {/* Rotating ring */}
      <div className="absolute top-1/4 right-1/4 w-64 h-64 border-2 border-burnt-peach/10 dark:border-burnt-peach/20 rounded-full animate-rotate-slow" />
      {/* Small floating dots */}
      <div className="absolute top-1/3 left-1/4 w-4 h-4 bg-burnt-peach/40 rounded-full animate-bounce-soft" />
      <div className="absolute top-2/3 right-1/3 w-3 h-3 bg-muted-teal/40 rounded-full animate-bounce-soft" style={{ animationDelay: '0.5s' }} />
      <div className="absolute bottom-1/4 left-1/3 w-5 h-5 bg-apricot/40 rounded-full animate-bounce-soft" style={{ animationDelay: '1s' }} />
    </div>
  );
};

// ============================================
// ANIMATION STATE MACHINE CONSTANTS
// ============================================

/**
 * Animation states for the multi-phase typing effect.
 * Flow: LEFT_TYPING -> LEFT_PAUSED -> LEFT_DELETING -> TRANSLATING_RIGHT
 *       -> RIGHT_TYPING -> RIGHT_PAUSED -> RIGHT_DELETING -> TRANSLATING_LEFT -> (loop)
 */
const ANIMATION_STATES = {
  LEFT_TYPING: 'LEFT_TYPING',           // Typing "Software Engineer" on left
  LEFT_PAUSED: 'LEFT_PAUSED',           // Pause after completing left text
  LEFT_DELETING: 'LEFT_DELETING',       // Deleting left text
  TRANSLATING_RIGHT: 'TRANSLATING_RIGHT', // Cursor slides to right container
  RIGHT_TYPING: 'RIGHT_TYPING',         // Typing "Recent Graduate" on right
  RIGHT_PAUSED: 'RIGHT_PAUSED',         // Pause after completing right text
  RIGHT_DELETING: 'RIGHT_DELETING',     // Deleting right text
  TRANSLATING_LEFT: 'TRANSLATING_LEFT', // Cursor slides back to left container
};

/**
 * Text content for each animation position.
 * Loaded from SPOT (Single Point of Truth) profile data.
 */
const ANIMATION_TEXTS = {
  left: HERO_TEXT.left,
  right: HERO_TEXT.right,
};

/**
 * Timing configurations for animation phases (in milliseconds).
 * Carefully tuned for smooth, coherent visual flow.
 */
const ANIMATION_TIMING = {
  typeSpeed: 100,           // Delay between typing each character
  deleteSpeed: 80,          // Delay between deleting each character
  pauseAfterType: 3000,     // Hold time after text is fully typed
  pauseAfterDelete: 400,    // Brief pause after text is fully deleted
  translateDuration: 600,   // Duration of cursor translation animation
  cursorBlinkSpeed: 500,    // Cursor blink interval during pauses
};

// ============================================
// HERO + ABOUT SECTION (Combined)
// ============================================
const HeroAboutSection = () => {
  // Animation state machine
  const [animationState, setAnimationState] = useState(ANIMATION_STATES.LEFT_TYPING);
  const [typedText, setTypedText] = useState('');
  const [showCursor, setShowCursor] = useState(true);

  // Derived states for easier conditionals
  const isLeftPosition = [
    ANIMATION_STATES.LEFT_TYPING,
    ANIMATION_STATES.LEFT_PAUSED,
    ANIMATION_STATES.LEFT_DELETING,
  ].includes(animationState);
  
  const isTranslating = [
    ANIMATION_STATES.TRANSLATING_RIGHT,
    ANIMATION_STATES.TRANSLATING_LEFT,
  ].includes(animationState);
  
  const isPaused = [
    ANIMATION_STATES.LEFT_PAUSED,
    ANIMATION_STATES.RIGHT_PAUSED,
  ].includes(animationState);

  // Skills loaded from SPOT (Single Point of Truth) profile data
  const skills = PRIMARY_SKILLS;

  const devOps = DEVOPS_SKILLS;

  /**
   * Cursor blinking effect during pause and translation states.
   * Cursor remains solid during active typing/deleting.
   */
  useEffect(() => {
    let cursorInterval;
    
    if (isPaused || isTranslating) {
      setShowCursor(true);
      cursorInterval = setInterval(() => {
        setShowCursor(prev => !prev);
      }, ANIMATION_TIMING.cursorBlinkSpeed);
    } else {
      setShowCursor(true);
    }

    return () => {
      if (cursorInterval) clearInterval(cursorInterval);
    };
  }, [isPaused, isTranslating]);

  /**
   * Main animation state machine effect.
   * Handles all state transitions with precise timing.
   */
  useEffect(() => {
    let timer;
    let charIndex = 0;

    /**
     * Get the target text based on current animation state.
     */
    const getCurrentText = () => {
      if ([ANIMATION_STATES.LEFT_TYPING, ANIMATION_STATES.LEFT_PAUSED, ANIMATION_STATES.LEFT_DELETING].includes(animationState)) {
        return ANIMATION_TEXTS.left;
      }
      return ANIMATION_TEXTS.right;
    };

    /**
     * Handle typing animation for a given text.
     * Transitions to nextState immediately after typing completes.
     * @param {string} text - Text to type
     * @param {string} nextState - State to transition to after typing completes
     */
    const typeText = (text, nextState) => {
      if (charIndex <= text.length) {
        setTypedText(text.slice(0, charIndex));
        charIndex++;
        timer = setTimeout(() => typeText(text, nextState), ANIMATION_TIMING.typeSpeed);
      } else {
        // Typing complete, immediately transition to pause state
        setAnimationState(nextState);
      }
    };

    /**
     * Handle delete animation for current text.
     * Transitions to nextState immediately after deletion completes.
     * @param {string} text - Text being deleted
     * @param {string} nextState - State to transition to after deletion completes
     */
    const deleteText = (text, nextState) => {
      if (charIndex >= 0) {
        setTypedText(text.slice(0, charIndex));
        charIndex--;
        timer = setTimeout(() => deleteText(text, nextState), ANIMATION_TIMING.deleteSpeed);
      } else {
        // Deletion complete, transition after brief pause for visual clarity
        timer = setTimeout(() => {
          setAnimationState(nextState);
        }, ANIMATION_TIMING.pauseAfterDelete);
      }
    };

    // State machine logic - each state handles its own timing
    switch (animationState) {
      case ANIMATION_STATES.LEFT_TYPING:
        // Start typing "Software Engineer" from current position
        charIndex = typedText.length;
        typeText(ANIMATION_TEXTS.left, ANIMATION_STATES.LEFT_PAUSED);
        break;

      case ANIMATION_STATES.LEFT_PAUSED:
        // Pause with blinking cursor after text is fully typed
        // The pauseAfterType delay happens HERE so cursor blinks are visible
        timer = setTimeout(() => {
          setAnimationState(ANIMATION_STATES.LEFT_DELETING);
        }, ANIMATION_TIMING.pauseAfterType);
        break;

      case ANIMATION_STATES.LEFT_DELETING:
        // Delete "Software Engineer" character by character
        charIndex = typedText.length;
        deleteText(ANIMATION_TEXTS.left, ANIMATION_STATES.TRANSLATING_RIGHT);
        break;

      case ANIMATION_STATES.TRANSLATING_RIGHT:
        // Cursor slides to center of right container
        // Wait for CSS transition to complete before starting right typing
        timer = setTimeout(() => {
          setAnimationState(ANIMATION_STATES.RIGHT_TYPING);
        }, ANIMATION_TIMING.translateDuration);
        break;

      case ANIMATION_STATES.RIGHT_TYPING:
        // Start typing "Recent Graduate"
        charIndex = typedText.length;
        typeText(ANIMATION_TEXTS.right, ANIMATION_STATES.RIGHT_PAUSED);
        break;

      case ANIMATION_STATES.RIGHT_PAUSED:
        // Pause with blinking cursor after text is fully typed
        timer = setTimeout(() => {
          setAnimationState(ANIMATION_STATES.RIGHT_DELETING);
        }, ANIMATION_TIMING.pauseAfterType);
        break;

      case ANIMATION_STATES.RIGHT_DELETING:
        // Delete "Recent Graduate" character by character
        charIndex = typedText.length;
        deleteText(ANIMATION_TEXTS.right, ANIMATION_STATES.TRANSLATING_LEFT);
        break;

      case ANIMATION_STATES.TRANSLATING_LEFT:
        // Cursor slides back to left container
        // Wait for CSS transition to complete, then restart the full cycle
        timer = setTimeout(() => {
          setAnimationState(ANIMATION_STATES.LEFT_TYPING);
        }, ANIMATION_TIMING.translateDuration);
        break;

      default:
        break;
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [animationState]);

  /**
   * Calculate the transform style for cursor translation.
   * Left position: centered above left container (1/3 width element at x=0)
   * Right position: centered above right container (2/3 width)
   * 
   * CSS Grid Layout: [1/3 left] [gap-4] [2/3 right]
   * 
   * Math for right-center positioning:
   * - Element width: 1/3 of container (33.33%)
   * - Right container center: 33.33% + gap + 33.33% = 66.67% + gap/2
   * - To center element at 66.67%: left edge at 50%
   * - TranslateX: 50% / 33.33% = 150% of element width
   * - Plus half the gap (0.5rem) for precise centering
   * 
   * Note: Translation only applies on lg+ screens. On mobile/tablet, containers
   * stack vertically so animation stays centered for both states.
   */
  const getTransformStyle = () => {
    const isRightPosition = [
      ANIMATION_STATES.TRANSLATING_RIGHT,
      ANIMATION_STATES.RIGHT_TYPING,
      ANIMATION_STATES.RIGHT_PAUSED,
      ANIMATION_STATES.RIGHT_DELETING,
    ].includes(animationState);

    // Only apply transform via inline style on large screens
    // Use window.innerWidth check for responsive behavior
    if (typeof window !== 'undefined' && window.innerWidth < 1024) {
      // Mobile/tablet: no translation
      return {
        transform: 'translateX(0)',
        transition: `transform ${ANIMATION_TIMING.translateDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`,
      };
    }

    return {
      // Desktop: TranslateX(150%) centers the 1/3-width element above the 2/3-width right container
      // +0.5rem accounts for half the grid gap to achieve true center alignment
      transform: isRightPosition 
        ? 'translateX(calc(150% + 0.5rem))' // Center above right container on desktop only
        : 'translateX(0)',
      transition: `transform ${ANIMATION_TIMING.translateDuration}ms cubic-bezier(0.4, 0, 0.2, 1)`,
    };
  };

  return (
    <section id="about" className="flex items-center pt-20 pb-3">
      <div className="container mx-auto px-6">
        {/* 
          Typing animation with translation capability.
          Wrapper spans full grid width to allow smooth translation.
          Inner container constrains text and handles positioning.
          Uses overflow-x-hidden to clip horizontal overflow during translation
          while preserving vertical visibility for descenders and cursor.
        */}
        <div className="w-full mb-4 overflow-x-hidden pb-1">
          <div 
            className="lg:w-1/3"
            style={getTransformStyle()}
          >
            <h1 className="text-xl md:text-3xl font-bold text-twilight dark:text-eggshell opacity-0 animate-fade-in delay-100 text-center leading-relaxed">
              <span className="gradient-text">{typedText}</span>
              <span 
                className="inline-block w-0.5 h-5 md:h-8 bg-burnt-peach ml-1 transition-opacity duration-100"
                style={{ opacity: showCursor ? 1 : 0 }}
              />
            </h1>
          </div>
        </div>

        {/* Grid: 1/3 left container, 2/3 right container */}
        <div className="grid lg:grid-cols-3 gap-6 items-stretch">
          {/* Left: Hero Content with Grid Dots (1/3 width) */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden min-h-0 md:min-h-[300px] flex flex-col lg:col-span-1 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
            <HeroGridDots />
            <div className="relative z-10 px-3 py-2 md:px-8 md:py-5 text-center flex-1 flex flex-col justify-center">
              {/* Profile Picture (3:4 aspect ratio) */}
              <div className="flex justify-center mb-4 opacity-0 animate-fade-in delay-200 group">
                <div 
                  className="w-36 md:w-48 bg-twilight/10 dark:bg-eggshell/10 rounded-[5px] border-2 border-solid border-twilight/30 dark:border-eggshell/30 flex items-center justify-center transition-all duration-300 group-hover:scale-110 group-hover:border-muted-teal/50 group-hover:bg-twilight/5 dark:group-hover:bg-eggshell/5 cursor-pointer shadow-none group-hover:shadow-2xl overflow-hidden"
                  style={{ aspectRatio: '3/4' }}
                >
                  <img 
                    src={PORTRAIT_PATH} 
                    alt={PORTRAIT_ALT} 
                    className="w-full h-full object-cover transition-all duration-300 group-hover:scale-105"
                  />
                </div>
              </div>

              {/* GitHub Link */}
              <div className="flex justify-center mb-2 opacity-0 animate-fade-in delay-250">
                <a
                  href={GITHUB_URL}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 rounded-sm bg-twilight/10 dark:bg-eggshell/10 hover:bg-burnt-peach/30 transition-all duration-300 hover:scale-105 hover:-translate-y-1 text-twilight dark:text-eggshell font-medium text-sm border border-twilight/10 dark:border-eggshell/10"
                >
                  <Github className="w-4 h-4" />
                  <span>@{GITHUB_USERNAME}</span>
                </a>
              </div>

              {/* Skills & Technologies (moved from right container) */}
              <div className="mt-2 opacity-0 animate-fade-in delay-300">
                <h3 className="text-sm font-semibold text-twilight dark:text-eggshell mb-2">Skills &amp; Technologies</h3>
                <div className="flex flex-wrap justify-center gap-2">
                  {skills.map((skill, index) => (
                    <span
                      key={skill}
                      className="inline-flex items-center justify-center h-7 px-3 bg-muted-teal/10 dark:bg-muted-teal/18 text-twilight dark:text-eggshell rounded-full text-xs font-medium border border-muted-teal/20 dark:border-muted-teal/30 hover:bg-muted-teal hover:border-muted-teal hover:text-eggshell transition-all duration-300 cursor-default hover:scale-110 hover:-translate-y-1 whitespace-nowrap"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Dev Ops */}
              <div className="mt-4 opacity-0 animate-fade-in delay-400">
                <h3 className="text-sm font-semibold text-twilight dark:text-eggshell mb-2">Dev Ops</h3>
                <div className="flex flex-wrap justify-center gap-2">
                  {devOps.map((tool, index) => (
                    <span
                      key={tool}
                      className="inline-flex items-center justify-center h-7 px-3 bg-burnt-peach/10 dark:bg-burnt-peach/18 text-twilight dark:text-eggshell rounded-full text-xs font-medium border border-burnt-peach/20 dark:border-burnt-peach/30 hover:bg-burnt-peach hover:border-burnt-peach hover:text-eggshell transition-all duration-300 cursor-default hover:scale-110 hover:-translate-y-1 whitespace-nowrap"
                      style={{ animationDelay: `${(index + skills.length) * 50}ms` }}
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
              
              {/* Analyze Qualifications CTA Button */}
              <div className="mt-6 opacity-0 animate-fade-in delay-500">
                <Button
                  asChild
                  className="w-full max-w-xs mx-auto bg-emerald-600 hover:bg-emerald-500 text-eggshell px-6 py-3 text-sm rounded-sm hover:scale-[1.02] transition-all duration-200 flex items-center justify-center gap-2"
                >
                  <a href="#fit-check">
                    <Brain className="w-4 h-4" />
                    Analyze Qualifications
                  </a>
                </Button>
              </div>
            </div>
            {/* Scroll indicator - docked to bottom independently */}
            <div className="relative z-10 pb-2 md:pb-5 opacity-0 animate-fade-in delay-500">
              <a href="#fit-check" className="inline-flex flex-col items-center group w-full justify-center">
                <div className="hero-arrow-bounce">
                  <ChevronDown className="w-6 h-6 text-burnt-peach dark:text-muted-teal group-hover:translate-y-1 transition-transform" />
                </div>
              </a>
            </div>
          </div>

          {/* Right: About Content (2/3 width) */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden flex flex-col lg:col-span-2 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl">
            <InteractiveGridDots />
            <div className="relative z-10 p-6 md:p-8 flex-1 flex flex-col">
              {/* Profile mini - displays school logo and degree information */}
              <div className="flex items-center gap-4 mb-4 opacity-0 animate-fade-in-left delay-100">
                <div className="w-16 h-16 rounded-[5px] overflow-hidden shadow-lg flex-shrink-0 bg-eggshell dark:bg-twilight/50">
                  <img
                    src={PRIMARY_EDUCATION.logo_path}
                    alt={`${PRIMARY_EDUCATION.institution} Logo`}
                    className="w-full h-full object-contain p-1"
                  />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-muted-teal">
                    {PRIMARY_EDUCATION.degree}
                  </h3>
                  <p className="text-twilight/60 dark:text-eggshell/60 text-sm">{PRIMARY_EDUCATION.institution} • {PRIMARY_EDUCATION.graduation}</p>
                </div>
              </div>

              {/* Bio */}
              <div className="opacity-0 animate-fade-in-right delay-200">
                <p className="text-twilight/80 dark:text-eggshell/80 leading-relaxed mb-4 text-sm">
                  <span className="font-bold text-muted-teal">{BIO_TLDR}</span> <br></br> {BIO_FULL} <br></br>
                </p>
              </div>

              {/* Showcase Containers - Personal Collage and Transcript (compact layout, 3:2 ratio) */}
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-4 opacity-0 animate-fade-in delay-250 w-full max-w-2xl mx-auto">
                {/* Get to Know Me - Personal Collage Container (3 columns, landscape aspect) */}
                <div className="col-span-1 md:col-span-3 relative bg-twilight/5 dark:bg-eggshell/5 rounded-[5px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden group hover:border-muted-teal/50 transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
                  <div className="p-3">
                    <div className="flex items-center gap-2 mb-3">
                      <Camera className="w-4 h-4 text-muted-teal" />
                      <h4 className="text-sm font-semibold text-twilight dark:text-eggshell">Get to know me!</h4>
                    </div>
                    {/* Image Carousel - wider landscape aspect ratio */}
                    <div className="relative aspect-[11/9] rounded-[3px] overflow-hidden border border-twilight/10 dark:border-eggshell/10">
                      <ImageCarousel interval={4000} />
                    </div>
                  </div>
                </div>

                {/* Official Transcript Container (2 columns) */}
                <a
                  href="/resources/resume.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="col-span-1 md:col-span-2 relative bg-twilight/5 dark:bg-eggshell/5 rounded-[5px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden group hover:border-burnt-peach/50 transition-all duration-300 hover:shadow-lg hover:-translate-y-1"
                >
                  <div className="p-3">
                    <div className="flex items-center gap-2 mb-3">
                      <FileText className="w-4 h-4 text-burnt-peach" />
                      <h4 className="text-sm font-semibold text-twilight dark:text-eggshell">PDF Resume</h4>
                    </div>
                    {/* PDF Thumbnail Preview */}
                    <div className="relative aspect-[4/5] bg-white dark:bg-twilight/30 rounded-[3px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden">
                      <img
                        src="/resources/resume_thumb.jpg"
                        alt="Transcript Preview"
                        className="w-full h-full object-cover object-top"
                      />
                      {/* Hover overlay */}
                      <div className="absolute inset-0 bg-burnt-peach/0 group-hover:bg-burnt-peach/20 transition-colors duration-300 flex items-center justify-center">
                        <ExternalLink className="w-5 h-5 text-burnt-peach opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                      </div>
                    </div>
                  </div>
                </a>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-wrap justify-center gap-2 md:gap-3 mt-auto opacity-0 animate-fade-in delay-300">
                <Button
                  asChild
                  className="bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell px-4 py-3 md:px-6 md:py-5 text-xs md:text-sm rounded-sm animate-pulse-glow hover:scale-105 transition-transform"
                >
                  <a href="#experience">View Experience</a>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-twilight dark:border-eggshell text-twilight dark:text-eggshell hover:bg-twilight hover:text-eggshell dark:hover:bg-eggshell dark:hover:text-twilight px-4 py-3 md:px-6 md:py-5 text-xs md:text-sm rounded-sm hover:scale-105 transition-transform"
                >
                  <a href="#contact">Get in Touch</a>
                </Button>
              </div>
            </div>
            {/* Scroll indicator - docked to bottom independently */}
            <div className="relative z-10 pb-2 md:pb-5 opacity-0 animate-fade-in delay-500">
              <a href="#projects" className="inline-flex flex-col items-center group w-full justify-center">
                <div className="hero-arrow-bounce">
                  <ChevronDown className="w-6 h-6 text-burnt-peach dark:text-muted-teal group-hover:translate-y-1 transition-transform" />
                </div>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// ============================================
// PROJECTS SECTION
// Features interactive project cards with modal pop-ups
// for detailed project information and image galleries
// ============================================

/**
 * Project data with extended properties for modal display.
 * Loaded from SPOT (Single Point of Truth) profile data.
 * Each project includes:
 * - id: Unique identifier matching the image folder name
 * - title: Display name
 * - description: Brief card description
 * - about: Extended description for modal
 * - learningOutcomes: Array of key takeaways (renamed from learning_outcomes)
 * - tags: Technology stack
 * - color: Gradient class for visual theming
 * - link: Optional external project URL
 */
const PROJECTS_DATA = FEATURED_PROJECTS.map(project => ({
  ...project,
  learningOutcomes: project.learning_outcomes, // Map to camelCase for consistency
}));

/**
 * ProjectCardThumbnail Component
 * 
 * Displays the first project image from the manifest as a thumbnail on project cards.
 * Falls back to a gradient placeholder with Code icon if no images are available.
 * 
 * @param {Object} props
 * @param {string} props.imagesFolder - Folder name in /resources/project_images/ (e.g., "project-churchlink")
 * @param {string} props.color - Gradient color classes for fallback display
 * @param {string} props.projectTitle - Project title for accessibility
 */
const ProjectCardThumbnail = ({ imagesFolder, color, projectTitle }) => {
  const [thumbnailSrc, setThumbnailSrc] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  /**
   * Fetch the first image from the project manifest on mount.
   */
  useEffect(() => {
    if (!imagesFolder) {
      setIsLoading(false);
      return;
    }

    const loadThumbnail = async () => {
      try {
        const response = await fetch(`/resources/project_images/${imagesFolder}/manifest.json`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        if (data.images && data.images.length > 0) {
          setThumbnailSrc(data.images[0]); // Use first image as thumbnail
        }
      } catch (error) {
        console.warn(`Failed to load thumbnail for ${imagesFolder}:`, error.message);
      } finally {
        setIsLoading(false);
      }
    };

    loadThumbnail();
  }, [imagesFolder]);

  // Loading state - show gradient placeholder
  if (isLoading) {
    return (
      <div className={`h-48 bg-gradient-to-br ${color} flex items-center justify-center relative overflow-hidden`}>
        <div className="animate-pulse">
          <Code className="w-16 h-16 text-eggshell/60" />
        </div>
      </div>
    );
  }

  // Show thumbnail image if available
  if (thumbnailSrc && !hasError) {
    return (
      <div className={`h-48 relative overflow-hidden bg-gradient-to-br ${color}`}>
        {/* Background pattern for letterboxing areas */}
        <div className="absolute inset-0 bg-twilight/10 dark:bg-eggshell/5" />
        <img
          src={thumbnailSrc}
          alt={`${projectTitle} thumbnail`}
          className="absolute inset-0 w-full h-full object-contain group-hover:scale-105 transition-transform duration-500"
          onError={() => setHasError(true)}
        />
        {/* Shimmer overlay on hover */}
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 shimmer" />
      </div>
    );
  }

  // Fallback to gradient placeholder with Code icon
  return (
    <div className={`h-48 bg-gradient-to-br ${color} flex items-center justify-center relative overflow-hidden`}>
      <Code className="w-16 h-16 text-eggshell/80 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500" />
      {/* Shimmer overlay on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 shimmer" />
    </div>
  );
};

const ProjectsSection = () => {
  // Track which project modal is open (null = none open)
  const [openProjectId, setOpenProjectId] = useState(null);

  return (
    <section id="projects" className="py-6">
      <div className="container mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-twilight dark:text-eggshell mb-3 text-center">
          Featured <span className="text-muted-teal">Projects</span>
        </h2>
        <p className="text-twilight/60 dark:text-eggshell/60 text-center mb-8 max-w-2xl mx-auto">
          My top-3 favorite projects showcasing my diverse skills, hard work, and passion for building
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {PROJECTS_DATA.map((project, index) => (
            <ProjectModal
              key={project.id}
              project={project}
              open={openProjectId === project.id}
              onOpenChange={(isOpen) => setOpenProjectId(isOpen ? project.id : null)}
            >
              <div
                className="group relative bg-white dark:bg-twilight/50 rounded-sm overflow-hidden shadow-lg hover:shadow-2xl hover:shadow-muted-teal/20 dark:hover:shadow-muted-teal/10 transition-all duration-300 hover:-translate-y-1 translate-y-0 opacity-0 animate-scale-in-no-transform glass flex flex-col cursor-pointer border-2 border-transparent hover:border-muted-teal/40"
                style={{ animationDelay: `${index * 150}ms` }}
                role="button"
                tabIndex={0}
                aria-label={`View details for ${project.title}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    setOpenProjectId(project.id);
                  }
                }}
              >
                {/* Project thumbnail image from manifest or gradient fallback */}
                <div className="relative">
                  <ProjectCardThumbnail 
                    imagesFolder={project.images_folder}
                    color={project.color}
                    projectTitle={project.title}
                  />
                  {/* Click to Explore Button - positioned on image */}
                  <div className="absolute top-3 right-3 z-10">
                    <ReadSummaryButton />
                  </div>
                </div>

                {/* Content */}
                <div className="relative flex-1 flex flex-col">
                  <CardGridDots />
                  <div className="p-6 relative z-10 flex-1 flex flex-col">
                    {/* Header with title */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <h3 className="text-xl font-semibold text-twilight dark:text-eggshell group-hover:text-muted-teal transition-colors duration-300">
                        {project.title}
                      </h3>
                    </div>
                    <p className="text-twilight/70 dark:text-eggshell/70 text-sm mb-4 leading-relaxed flex-1">
                      {project.description}
                    </p>
                    
                    {/* Tags */}
                    <div className="flex flex-wrap gap-2 mt-auto">
                      {project.tags.map((tag) => (
                        <span 
                          key={tag} 
                          className="px-3 py-1 bg-muted-teal/10 dark:bg-muted-teal/20 text-muted-teal text-xs rounded-full transition-all duration-300 hover:bg-muted-teal hover:text-eggshell"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </ProjectModal>
          ))}
        </div>
      </div>
    </section>
  );
};

// ============================================
// TIMELINE SHOWCASE IMAGE CAROUSEL COMPONENT
// Rotating carousel for timeline showcase cards
// Uses staggered offsets for graceful cascade/waterfall effect
// Smooth right-to-left sliding animation
// ============================================
const TOTAL_SHOWCASE_CARDS = 7;
const CAROUSEL_INTERVAL = 5250; // Base interval in ms (50% longer for smoother viewing)
const SLIDE_DURATION = 500; // Slide animation duration in ms
const STAGGER_OFFSET_MS = 750; // Offset between each card's rotation start (waterfall effect)

const TimelineShowcaseCarousel = ({ showcaseId, interval = CAROUSEL_INTERVAL, color = 'burnt-peach' }) => {
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [previousIndex, setPreviousIndex] = useState(null);
  const [isSliding, setIsSliding] = useState(false);
  const [slideDirection, setSlideDirection] = useState('right'); // 'left' or 'right'
  const [hasImages, setHasImages] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);
  const timerRef = useRef(null);

  /**
   * Fetch showcase images from manifest on mount.
   * Falls back to placeholder if no images available.
   */
  useEffect(() => {
    fetch(`/resources/timeline_images/showcase${showcaseId}/manifest.json`)
      .then(res => res.json())
      .then(data => {
        if (data.images && data.images.length > 0) {
          setImages(data.images);
        } else {
          setHasImages(false);
        }
      })
      .catch(() => {
        setHasImages(false);
      });
  }, [showcaseId]);

  /**
   * Start or restart the auto-advance timer.
   * Called after initialization and after any user interaction.
   * Auto-advance always goes forward (right direction).
   */
  const startTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }
    
    timerRef.current = setInterval(() => {
      setSlideDirection('right');
      setCurrentIndex(prev => {
        const next = (prev + 1) % images.length;
        setPreviousIndex(prev);
        setIsSliding(true);
        setTimeout(() => {
          setIsSliding(false);
          setPreviousIndex(null);
        }, SLIDE_DURATION);
        return next;
      });
    }, interval);
  }, [images.length, interval]);

  /**
   * Trigger slide transition to next image with direction awareness.
   * Resets the auto-advance timer to prevent immediate jump after interaction.
   * 
   * @param {number} newIndex - Target image index
   * @param {string} direction - Animation direction: 'left' or 'right'
   */
  const slideToIndex = useCallback((newIndex, direction = 'right') => {
    if (isSliding || newIndex === currentIndex) return;
    
    setSlideDirection(direction);
    setPreviousIndex(currentIndex);
    setCurrentIndex(newIndex);
    setIsSliding(true);
    
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, SLIDE_DURATION);
    
    // Reset timer after user interaction
    if (isInitialized) {
      startTimer();
    }
  }, [isSliding, currentIndex, isInitialized, startTimer]);

  /**
   * Navigate to previous image (slides from left).
   * Timer is reset via slideToIndex.
   */
  const goToPrevious = useCallback(() => {
    const prevIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
    slideToIndex(prevIndex, 'left');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Navigate to next image (slides from right).
   * Timer is reset via slideToIndex.
   */
  const goToNext = useCallback(() => {
    const nextIndex = (currentIndex + 1) % images.length;
    slideToIndex(nextIndex, 'right');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Auto-advance carousel with slide transition.
   * Each card has a staggered start offset to create a graceful waterfall effect.
   * Cards are offset by STAGGER_OFFSET_MS each: card 1 at 0ms, card 2 at 750ms, etc.
   * This creates a beautiful wave where image changes ripple across all cards.
   */
  useEffect(() => {
    if (images.length <= 1) return;
    
    // Calculate staggered offset: each card starts STAGGER_OFFSET_MS after the previous
    const staggerOffset = (showcaseId - 1) * STAGGER_OFFSET_MS;
    
    // Initial delay before starting the interval (creates the waterfall effect)
    const initialDelay = setTimeout(() => {
      setIsInitialized(true);
    }, staggerOffset);
    
    return () => clearTimeout(initialDelay);
  }, [images.length, interval, showcaseId]);

  // Main carousel interval (only starts after initial stagger delay)
  useEffect(() => {
    if (images.length <= 1 || !isInitialized) return;
    
    // Trigger first transition immediately when initialized
    const nextIndex = (currentIndex + 1) % images.length;
    setPreviousIndex(currentIndex);
    setCurrentIndex(nextIndex);
    setIsSliding(true);
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, SLIDE_DURATION);
    
    // Start the auto-advance timer
    startTimer();

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [images.length, isInitialized, startTimer]);

  // Placeholder when no images are available
  if (!hasImages || images.length === 0) {
    return (
      <div className="relative w-full h-full overflow-hidden rounded-[5px] bg-twilight/10 dark:bg-eggshell/10 flex items-center justify-center border-2 border-dashed border-twilight/20 dark:border-eggshell/20">
        <div className="text-center p-4">
          <Camera className={`w-8 h-8 mx-auto mb-2 text-${color}/30`} />
          <p className="text-xs text-twilight/40 dark:text-eggshell/40">Showcase {showcaseId}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full overflow-hidden rounded-[5px] group">
      {/* Previous image - slides out to the left */}
      {previousIndex !== null && (
        <img
          src={images[previousIndex]}
          alt={`Showcase ${showcaseId} - ${previousIndex + 1}`}
          className={`absolute inset-0 w-full h-full object-cover ${
            slideDirection === 'right' ? 'animate-slide-out-left' : 'animate-slide-out-right'
          }`}
          style={{
            animationDuration: `${SLIDE_DURATION}ms`,
          }}
        />
      )}
      {/* Current image - slides in based on direction */}
      <img
        src={images[currentIndex]}
        alt={`Showcase ${showcaseId} - ${currentIndex + 1}`}
        className={`absolute inset-0 w-full h-full object-cover ${
          isSliding && previousIndex !== null 
            ? (slideDirection === 'right' ? 'animate-slide-in-right' : 'animate-slide-in-left')
            : ''
        }`}
        style={{
          animationDuration: `${SLIDE_DURATION}ms`,
        }}
      />
      {/* Navigation arrows - only show if more than 1 image */}
      {images.length > 1 && (
        <>
          {/* Left arrow */}
          <button
            onClick={goToPrevious}
            className="absolute left-1 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 hover:bg-muted-teal hover:scale-110"
            aria-label="Previous image"
          >
            <ChevronLeft className="w-4 h-4 text-eggshell" />
          </button>
          {/* Right arrow */}
          <button
            onClick={goToNext}
            className="absolute right-1 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 hover:bg-muted-teal hover:scale-110"
            aria-label="Next image"
          >
            <ChevronRight className="w-4 h-4 text-eggshell" />
          </button>
        </>
      )}
      {/* Image indicator dots */}
      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {images.map((_, idx) => (
            <button
              key={idx}
              onClick={() => slideToIndex(idx, idx > currentIndex ? 'right' : 'left')}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-200 ${
                idx === currentIndex
                  ? `bg-${color} scale-125`
                  : 'bg-eggshell/60 hover:bg-eggshell/80'
              }`}
              aria-label={`Go to image ${idx + 1}`}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// ============================================
// EXPERIENCE SECTION - CENTERED TIMELINE
// Elegant alternating left/right timeline layout
// with showcase cards and connecting lines
// ============================================
const ExperienceSection = () => {
  /**
   * Timeline experience data loaded from SPOT (Single Point of Truth).
   * Each entry alternates between left and right positioning.
   */
  const experiences = EXPERIENCE.timeline;

  return (
    <section id="experience" className="py-6 relative">
      <div className="container mx-auto px-6">
        <div className="relative bg-background/30 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-8">
          <InteractiveGridDots />
          <div className="relative z-10">
            {/* Centered Timeline Container */}
            <div className="relative max-w-5xl mx-auto px-4">
              {/* Central Timeline Line */}
              <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-muted-teal via-apricot to-burnt-peach transform -translate-x-1/2 rounded-full hidden md:block" />
              
              {/* Desktop Timeline Caps */}
              <div className="absolute left-1/2 top-0 w-3 h-3 bg-muted-teal rounded-full transform -translate-x-1/2 -translate-y-1/2 z-10 hidden md:block shadow-[0_0_10px_rgba(129,178,154,0.5)]" />
              <div className="absolute left-1/2 bottom-0 w-3 h-3 bg-burnt-peach rounded-full transform -translate-x-1/2 translate-y-1/2 z-10 hidden md:block shadow-[0_0_10px_rgba(224,122,95,0.5)]" />

              {/* Mobile Timeline Line (left-aligned) */}
              <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-muted-teal via-apricot to-burnt-peach transform -translate-x-1/2 rounded-full md:hidden" />
              
              {/* Mobile Timeline Caps */}
              <div className="absolute left-8 top-0 w-3 h-3 bg-muted-teal rounded-full transform -translate-x-1/2 -translate-y-1/2 z-10 md:hidden shadow-[0_0_10px_rgba(129,178,154,0.5)]" />
              <div className="absolute left-8 bottom-0 w-3 h-3 bg-burnt-peach rounded-full transform -translate-x-1/2 translate-y-1/2 z-10 md:hidden shadow-[0_0_10px_rgba(224,122,95,0.5)]" />

              {/* Timeline Entries */}
              {experiences.map((exp, index) => {
                const isLeft = index % 2 === 0;
                
                // Calculate dynamic color based on position in the gradient
                // Top (0) -> muted-teal, Center (0.5) -> apricot, Bottom (1) -> burnt-peach
                const total = experiences.length;
                const ratio = index / (total - 1);
                let nodeColor = 'muted-teal';
                let glowRgb = '129, 178, 154'; // muted-teal
                
                if (ratio > 0.33 && ratio <= 0.66) {
                  nodeColor = 'apricot';
                  glowRgb = '242, 204, 143'; // apricot
                } else if (ratio > 0.66) {
                  nodeColor = 'burnt-peach';
                  glowRgb = '224, 122, 95'; // burnt-peach
                }
                
                return (
                  <div
                    key={exp.id}
                    className={`relative md:-mb-36 mb-12 last:mb-0 opacity-0 animate-slide-up pointer-events-none`}
                    style={{ 
                      animationDelay: `${index * 150}ms`,
                      zIndex: experiences.length - index
                    }}
                  >
                    {/* Desktop Layout - Alternating */}
                    <div className="hidden md:grid md:grid-cols-[1fr_60px_1fr] gap-0 items-center">
                      {/* Left Side Content */}
                      <div className={`${isLeft ? 'pr-4' : ''}`}>
                        {isLeft ? (
                          /* Showcase Card - Left */
                          <div className="flex justify-end">
                            <div className="relative w-full max-w-sm bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg hover:shadow-xl transition-transform transition-shadow duration-300 hover:-translate-y-1 translate-y-0 overflow-hidden group glass pointer-events-auto">
                              {/* Showcase Image Container */}
                              <div className="aspect-[16/9] relative">
                                <TimelineShowcaseCarousel showcaseId={exp.id} color={nodeColor} />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                              </div>
                              {/* Card Content */}
                              <div className="p-3.5">
                                <div className="flex items-center justify-between gap-2 mb-0.5">
                                  <h3 className="text-lg font-bold text-twilight dark:text-eggshell transition-colors">
                                    {exp.title}
                                  </h3>
                                  <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-twilight/5 dark:bg-eggshell/15 border border-twilight/15 dark:border-eggshell/20 transition-all duration-300`}>
                                    <Clock className={`w-4 h-4 text-${nodeColor} transition-transform duration-300`} />
                                    <span className={`text-xs font-bold text-twilight/60 dark:text-eggshell/80 transition-colors whitespace-nowrap`}>
                                      {exp.period}
                                    </span>
                                  </div>
                                </div>
                                <p className={`text-${nodeColor} font-medium text-xs mb-2`}>{exp.company}</p>
                                
                                {/* Description Row */}
                                <div className={`mt-1.5 mb-2 p-2.5 rounded-[5px] border border-${nodeColor}/20 bg-twilight/5 dark:bg-eggshell/5`}>
                                  <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">
                                    {exp.description}
                                  </p>
                                </div>

                                {/* Tags */}
                                <div className="flex flex-wrap gap-1">
                                  {exp.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className={`px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full hover:bg-${nodeColor} hover:text-eggshell transition-all duration-200`}
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          /* Empty space where Description Card used to be */
                          <div className="w-full max-w-sm" />
                        )}
                      </div>

                      {/* Center - Timeline Node with Connecting Line */}
                      <div className="relative flex items-center justify-center">
                        {/* Connecting Line to Card */}
                        <div className={`absolute h-0.5 bg-gradient-to-r ${
                          isLeft 
                            ? `from-${nodeColor}/60 to-${nodeColor} right-1/2 w-[30px]`
                            : `from-${nodeColor} to-${nodeColor}/60 left-1/2 w-[30px]`
                        }`} />
                        {/* Timeline Node */}
                        <div 
                          className={`relative z-10 w-10 h-10 rounded-full bg-${nodeColor} flex items-center justify-center shadow-lg animate-pulse-glow pointer-events-auto`}
                          style={{ '--glow-color': `rgba(${glowRgb}, 0.3)` }}
                        >
                          <Briefcase className="w-5 h-5 text-eggshell" />
                        </div>
                      </div>

                      {/* Right Side Content */}
                      <div className={`${!isLeft ? 'pl-4' : ''}`}>
                        {!isLeft ? (
                          /* Showcase Card - Right */
                          <div className="flex justify-start">
                            <div className="relative w-full max-w-sm bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg hover:shadow-xl transition-transform transition-shadow duration-300 hover:-translate-y-1 translate-y-0 overflow-hidden group glass pointer-events-auto">
                              {/* Showcase Image Container */}
                              <div className="aspect-[16/9] relative">
                                <TimelineShowcaseCarousel showcaseId={exp.id} color={nodeColor} />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                              </div>
                              {/* Card Content */}
                              <div className="p-3.5">
                                <div className="flex items-center justify-between gap-2 mb-0.5">
                                  <h3 className="text-lg font-bold text-twilight dark:text-eggshell transition-colors">
                                    {exp.title}
                                  </h3>
                                  <div className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-twilight/5 dark:bg-eggshell/15 border border-twilight/15 dark:border-eggshell/20 transition-all duration-300`}>
                                    <Clock className={`w-4 h-4 text-${nodeColor} transition-transform duration-300`} />
                                    <span className={`text-xs font-bold text-twilight/60 dark:text-eggshell/80 transition-colors whitespace-nowrap`}>
                                      {exp.period}
                                    </span>
                                  </div>
                                </div>
                                <p className={`text-${nodeColor} font-medium text-xs mb-2`}>{exp.company}</p>
                                
                                {/* Description Row */}
                                <div className={`mt-1.5 mb-2 p-2.5 rounded-[5px] border border-${nodeColor}/20 bg-twilight/5 dark:bg-eggshell/5`}>
                                  <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">
                                    {exp.description}
                                  </p>
                                </div>

                                {/* Tags */}
                                <div className="flex flex-wrap gap-1">
                                  {exp.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className={`px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full hover:bg-${nodeColor} hover:text-eggshell transition-all duration-200`}
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          /* Empty space where Description Card used to be */
                          <div className="w-full max-w-sm" />
                        )}
                      </div>
                    </div>

                    {/* Mobile Layout - Single Column */}
                    <div className="md:hidden relative pl-12">
                      {/* Connecting Line to Timeline */}
                      <div className={`absolute left-4 top-8 w-8 h-0.5 bg-${nodeColor}`} />
                      
                      {/* Timeline Node */}
                      <div 
                        className={`absolute left-4 top-4 w-8 h-8 rounded-full bg-${nodeColor} flex items-center justify-center shadow-md z-10 transform -translate-x-1/2`}
                        style={{ '--glow-color': `rgba(${glowRgb}, 0.3)` }}
                      >
                        <Briefcase className="w-4 h-4 text-eggshell" />
                      </div>

                      {/* Combined Card for Mobile */}
                      <div className="bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg hover:shadow-xl transition-transform transition-shadow duration-300 hover:-translate-y-1 translate-y-0 overflow-hidden glass pointer-events-auto">
                        {/* Showcase Image */}
                        <div className="aspect-[16/9] relative">
                          <TimelineShowcaseCarousel showcaseId={exp.id} color={nodeColor} />
                          <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                        </div>
                        {/* Content */}
                        <div className="p-3.5">
                          <div className="flex items-center justify-between gap-2 mb-0.5">
                            <h3 className="text-base font-bold text-twilight dark:text-eggshell">
                              {exp.title}
                            </h3>
                            <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-twilight/5 dark:bg-eggshell/15 border border-twilight/15 dark:border-eggshell/20 transition-all duration-300`}>
                              <Clock className={`w-3.5 h-3.5 text-${nodeColor}`} />
                              <span className={`text-[10px] font-bold text-twilight/60 dark:text-eggshell/80 whitespace-nowrap`}>
                                {exp.period}
                              </span>
                            </div>
                          </div>
                          <p className={`text-${nodeColor} font-medium text-xs mb-2`}>{exp.company}</p>
                          
                          {/* Description Row */}
                          <div className={`mt-1.5 mb-2 p-2.5 rounded-[5px] border border-${nodeColor}/20 bg-twilight/5 dark:bg-eggshell/5`}>
                            <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">
                              {exp.description}
                            </p>
                          </div>

                          <div className="flex flex-wrap gap-1">
                            {exp.tags.map((tag) => (
                              <span
                                key={tag}
                                className={`px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full hover:bg-${nodeColor} hover:text-eggshell transition-all duration-200`}
                              >
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

// ============================================
// CONTACT SECTION
// ============================================
const ContactSection = () => {
  return (
    <section id="contact" className="py-6 relative z-30">
      <div className="container mx-auto px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-twilight dark:text-eggshell mb-3">
            Get in <span className="text-burnt-peach">Touch</span>
          </h2>

          <Button
            asChild
            className="bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell px-7 py-5 text-base rounded-sm animate-pulse-glow hover:scale-105 transition-transform relative z-10"
          >
            <a href={`mailto:${EMAIL}`} className="flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Say Hello
            </a>
          </Button>
        </div>
      </div>
    </section>
  );
};

// ============================================
// MAIN PAGE COMPONENT
// ============================================
export default function App() {
  return (
    <>
      <ParticleBackground />
      <Header />
      <main>
        <HeroAboutSection />
        <FitCheckSection />
        <ProjectsSection />
        <ExperienceSection />
        <ContactSection />
      </main>
      <Footer />
    </>
  );
}
