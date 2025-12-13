'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Briefcase, User, Mail, Github, ChevronDown, ExternalLink, Sun, Moon, Code, FileText, Camera } from 'lucide-react';
import { useHeaderVisibility } from '@/hooks/use-header-visibility';
import { InfoDialog, InfoButton } from '@/components/fit-check/InfoDialog';
import { Button } from '@/components/ui/button';
import ParticleBackground from '@/components/ParticleBackground';
import InteractiveGridDots from '@/components/InteractiveGridDots';
import CardGridDots from '@/components/CardGridDots';
import HeroGridDots from '@/components/HeroGridDots';
import FitCheckSection from '@/components/FitCheckSection';

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
   * Trigger slide transition to a specific index.
   * New image slides in from right, current slides out to left.
   */
  const slideToIndex = (newIndex) => {
    if (isSliding || newIndex === currentIndex) return;
    
    setPreviousIndex(currentIndex);
    setCurrentIndex(newIndex);
    setIsSliding(true);
    
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, HERO_SLIDE_DURATION);
  };

  /**
   * Auto-advance to next image with slide transition.
   */
  useEffect(() => {
    if (images.length <= 1) return;
    
    const timer = setInterval(() => {
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

    return () => clearInterval(timer);
  }, [images.length, interval]);

  return (
    <div className="relative w-full h-full overflow-hidden rounded-[5px]">
      {/* Previous image - slides out to the left */}
      {previousIndex !== null && (
        <img
          src={images[previousIndex]}
          alt={`Personal photo ${previousIndex + 1}`}
          className="absolute inset-0 w-full h-full object-cover animate-slide-out-left"
          style={{
            animationDuration: `${HERO_SLIDE_DURATION}ms`,
          }}
        />
      )}
      {/* Current image - slides in from the right (or static if not sliding) */}
      <img
        src={images[currentIndex]}
        alt={`Personal photo ${currentIndex + 1}`}
        className={`absolute inset-0 w-full h-full object-cover ${
          isSliding && previousIndex !== null ? 'animate-slide-in-right' : ''
        }`}
        style={{
          animationDuration: `${HERO_SLIDE_DURATION}ms`,
        }}
      />
      {/* Image indicator dots - only show if more than 1 image */}
      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {images.map((_, idx) => (
            <button
              key={idx}
              onClick={() => slideToIndex(idx)}
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
        ${isVisible 
          ? 'translate-y-0 opacity-100' 
          : '-translate-y-full opacity-0 pointer-events-none'
        }
      `}
      style={{
        transform: isVisible ? 'translateY(0)' : 'translateY(-100%)',
        transition: isVisible 
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
    { icon: Github, href: '#', label: 'GitHub' },
    { icon: Mail, href: '#', label: 'Email' },
  ];

  return (
    <footer className="text-twilight dark:text-eggshell py-6 relative z-20">
      <div className="container mx-auto px-6">
        <div className="relative bg-background/95 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-6">
          <InteractiveGridDots />
          <div className="relative z-10 px-8">
            {/* Main footer content */}
            <div className="grid md:grid-cols-3 gap-8">
              {/* Brand */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Portfolio</h3>
                <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">
                  Hobbyist software engineer &amp; recent graduate passionate about building elegant solutions.
                </p>
              </div>

              {/* Navigation */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Navigation</h3>
                <ul className="space-y-2">
                  {footerLinks.map((link) => (
                    <li key={link.name}>
                      <a href={link.href} className="text-twilight/70 dark:text-eggshell/70 hover:text-burnt-peach transition-colors text-sm animated-underline">
                        {link.name}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Contact */}
              <div>
                <h3 className="text-lg font-semibold mb-3">Connect</h3>
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
                  hello@example.com
                </p>
              </div>
            </div>

            {/* Copyright */}
            <div className="mt-8 pt-6 border-t border-twilight/20 dark:border-eggshell/20 text-center">
              <p className="text-twilight/50 dark:text-eggshell/50 text-sm">
                &copy; {new Date().getFullYear()} Portfolio. All rights reserved.
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
 */
const ANIMATION_TEXTS = {
  left: 'I\'m Jaden Bruha',
  right: 'A Technical Engineer',
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

  const skills = [
    'JavaScript', 'React', 'Next.js', 'Python', 'Node.js', 'TypeScript',
    'PostgreSQL', 'Git', 'AWS', 'Docker', 'TailwindCSS'
  ];

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
    <section id="about" className="flex items-center pt-20 pb-4">
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
        <div className="grid lg:grid-cols-3 gap-4 items-stretch">
          {/* Left: Hero Content with Grid Dots (1/3 width) */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden min-h-0 md:min-h-[300px] flex flex-col lg:col-span-1">
            <HeroGridDots />
            <div className="relative z-10 px-3 py-2 md:px-8 md:py-5 text-center flex-1 flex flex-col justify-center">
              {/* Profile Picture Placeholder (3:4 aspect ratio) */}
              <div className="flex justify-center mb-4 opacity-0 animate-fade-in delay-200">
                <div 
                  className="w-36 md:w-48 bg-twilight/10 dark:bg-eggshell/10 rounded-[5px] border-2 border-dashed border-twilight/30 dark:border-eggshell/30 flex items-center justify-center"
                  style={{ aspectRatio: '3/4' }}
                >
                  {/* Placeholder icon for future profile picture */}
                  <User className="w-12 h-12 md:w-16 md:h-16 text-twilight/40 dark:text-eggshell/40" />
                </div>
              </div>

              {/* Skills & Technologies (moved from right container) */}
              <div className="mt-4 opacity-0 animate-fade-in delay-300">
                <h3 className="text-sm font-semibold text-twilight dark:text-eggshell mb-2">Skills &amp; Technologies</h3>
                <div className="flex flex-wrap justify-center gap-2">
                  {skills.map((skill, index) => (
                    <span
                      key={skill}
                      className="px-3 py-1.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell rounded-full text-xs font-medium hover:bg-muted-teal dark:hover:bg-muted-teal hover:text-eggshell dark:hover:text-eggshell transition-all duration-300 cursor-default hover:scale-110 hover:-translate-y-1"
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
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
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden flex flex-col lg:col-span-2">
            <InteractiveGridDots />
            <div className="relative z-10 p-6 md:p-8 flex-1 flex flex-col">
              {/* Profile mini - displays school logo and degree information */}
              <div className="flex items-center gap-4 mb-4 opacity-0 animate-fade-in-left delay-100">
                <div className="w-16 h-16 rounded-[5px] overflow-hidden shadow-lg flex-shrink-0 bg-eggshell dark:bg-twilight/50">
                  <img
                    src="/resources/school_logo.png"
                    alt="California State University, Sacramento Logo"
                    className="w-full h-full object-contain p-1"
                  />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">Bachelor of Science Degree in Computer Science</h3>
                  <p className="text-twilight/60 dark:text-eggshell/60 text-sm">California State University, Sacramento • 2025 Winter Graduate</p>
                </div>
              </div>

              {/* Bio */}
              <div className="opacity-0 animate-fade-in-right delay-200">
                <p className="text-twilight/80 dark:text-eggshell/80 leading-relaxed mb-4 text-sm">
                  <span className="font-bold text-muted-teal">TLDR; I am Jaden Bruha, and I'm a very nerdy engineer.</span> <br></br> I have a passion for building  anything and everything from software, computers to serve my software, AI agents, and motorcycles. My journey started at a young age as a hobbyist, and I've grown into a full stack developer striving for elegant solutions.
                </p>
              </div>

              {/* Showcase Containers - Personal Collage and Transcript (compact layout, 3:2 ratio) */}
              <div className="grid grid-cols-5 gap-3 mb-4 opacity-0 animate-fade-in delay-250 max-w-lg mx-auto">
                {/* Get to Know Me - Personal Collage Container (3 columns, landscape aspect) */}
                <div className="col-span-3 relative bg-twilight/5 dark:bg-eggshell/5 rounded-[5px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden group hover:border-muted-teal/50 transition-all duration-300">
                  <div className="p-2">
                    <div className="flex items-center gap-1.5 mb-2">
                      <Camera className="w-3.5 h-3.5 text-muted-teal" />
                      <h4 className="text-xs font-semibold text-twilight dark:text-eggshell">Get to know me!</h4>
                    </div>
                    {/* Image Carousel - wider landscape aspect ratio */}
                    <div className="relative aspect-[11/9] rounded-[3px] overflow-hidden border border-twilight/10 dark:border-eggshell/10">
                      <ImageCarousel interval={4000} />
                    </div>
                  </div>
                </div>

                {/* Official Transcript Container (2 columns) */}
                <a
                  href="/resources/SSR_TSRPT.pdf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="col-span-2 relative bg-twilight/5 dark:bg-eggshell/5 rounded-[5px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden group hover:border-burnt-peach/50 transition-all duration-300 hover:shadow-md"
                >
                  <div className="p-2">
                    <div className="flex items-center gap-1.5 mb-2">
                      <FileText className="w-3.5 h-3.5 text-burnt-peach" />
                      <h4 className="text-xs font-semibold text-twilight dark:text-eggshell">My Transcript</h4>
                    </div>
                    {/* PDF Thumbnail Preview */}
                    <div className="relative aspect-[4/5] bg-white dark:bg-twilight/30 rounded-[3px] border border-twilight/10 dark:border-eggshell/10 overflow-hidden">
                      <img
                        src="/resources/SSR_TSRPT_thumb.jpg"
                        alt="Transcript Preview"
                        className="w-full h-full object-cover object-top"
                      />
                      {/* Hover overlay */}
                      <div className="absolute inset-0 bg-burnt-peach/0 group-hover:bg-burnt-peach/20 transition-colors duration-300 flex items-center justify-center">
                        <ExternalLink className="w-4 h-4 text-burnt-peach opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
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
// ============================================
const ProjectsSection = () => {
  const projects = [
    {
      title: 'Project Alpha',
      description: 'A full-stack web application built with React and Node.js, featuring real-time updates and modern UI.',
      tags: ['React', 'Node.js', 'PostgreSQL'],
      color: 'from-burnt-peach to-apricot',
    },
    {
      title: 'Project Beta',
      description: 'Mobile-first progressive web app with offline capabilities and push notifications.',
      tags: ['Next.js', 'PWA', 'TypeScript'],
      color: 'from-muted-teal to-twilight',
    },
    {
      title: 'Project Gamma',
      description: 'Data visualization dashboard with interactive charts and real-time analytics.',
      tags: ['Python', 'D3.js', 'PostgreSQL'],
      color: 'from-apricot to-muted-teal',
    },
  ];

  return (
    <section id="projects" className="py-6">
      <div className="container mx-auto px-6">
        <h2 className="text-3xl md:text-4xl font-bold text-twilight dark:text-eggshell mb-3 text-center">
          Featured <span className="text-burnt-peach">Projects</span>
        </h2>
        <p className="text-twilight/60 dark:text-eggshell/60 text-center mb-8 max-w-2xl mx-auto">
          My top-3 favorite projects to showcase my diverse skills and passion for building.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {projects.map((project, index) => (
            <div
              key={project.title}
              className="group bg-white dark:bg-twilight/50 rounded-sm overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 opacity-0 animate-scale-in-no-transform glass flex flex-col"
              style={{ animationDelay: `${index * 150}ms` }}
            >
              {/* Project image placeholder */}
              <div className={`h-48 bg-gradient-to-br ${project.color} flex items-center justify-center relative overflow-hidden`}>
                <Code className="w-16 h-16 text-eggshell/80 group-hover:scale-125 group-hover:rotate-12 transition-all duration-500" />
                {/* Shimmer overlay on hover */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 shimmer" />
              </div>

              {/* Content */}
              <div className="relative flex-1 flex flex-col">
                <CardGridDots />
                <div className="p-6 relative z-10 flex-1 flex flex-col">
                  <h3 className="text-xl font-semibold text-twilight dark:text-eggshell mb-3 flex items-center justify-between">
                    {project.title}
                    <ExternalLink className="w-5 h-5 text-twilight/40 dark:text-eggshell/40 group-hover:text-burnt-peach group-hover:translate-x-1 group-hover:-translate-y-1 transition-all duration-300" />
                  </h3>
                  <p className="text-twilight/70 dark:text-eggshell/70 text-sm mb-4 leading-relaxed flex-1">
                    {project.description}
                  </p>
                  <div className="flex flex-wrap gap-2 mt-auto">
                    {project.tags.map((tag) => (
                      <span key={tag} className="px-3 py-1 bg-muted-teal/10 dark:bg-muted-teal/20 text-muted-teal text-xs rounded-full transition-all duration-300 hover:bg-muted-teal hover:text-eggshell">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

// ============================================
// TIMELINE SHOWCASE IMAGE CAROUSEL COMPONENT
// Rotating carousel for timeline showcase cards
// Uses staggered offsets for graceful cascade effect
// Smooth right-to-left sliding animation
// ============================================
const TOTAL_SHOWCASE_CARDS = 7;
const CAROUSEL_INTERVAL = 3500; // Base interval in ms
const SLIDE_DURATION = 500; // Slide animation duration in ms

const TimelineShowcaseCarousel = ({ showcaseId, interval = CAROUSEL_INTERVAL }) => {
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [previousIndex, setPreviousIndex] = useState(null);
  const [isSliding, setIsSliding] = useState(false);
  const [hasImages, setHasImages] = useState(true);
  const [isInitialized, setIsInitialized] = useState(false);

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
   * Trigger slide transition to next image.
   * New image slides in from right, current slides out to left.
   */
  const slideToIndex = (newIndex) => {
    if (isSliding || newIndex === currentIndex) return;
    
    setPreviousIndex(currentIndex);
    setCurrentIndex(newIndex);
    setIsSliding(true);
    
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, SLIDE_DURATION);
  };

  /**
   * Auto-advance carousel with slide transition.
   * Each card has a staggered start offset to create a graceful cascade effect.
   * Cards are evenly distributed: card 1 starts at 0ms, card 2 at interval/7, etc.
   * This creates a beautiful wave where image changes ripple across all 7 cards.
   */
  useEffect(() => {
    if (images.length <= 1) return;
    
    // Calculate staggered offset: evenly distribute across the interval
    const staggerOffset = ((showcaseId - 1) / TOTAL_SHOWCASE_CARDS) * interval;
    
    // Initial delay before starting the interval (creates the cascade effect)
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
    slideToIndex(nextIndex);
    
    const timer = setInterval(() => {
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

    return () => clearInterval(timer);
  }, [images.length, interval, isInitialized]);

  // Placeholder when no images are available
  if (!hasImages || images.length === 0) {
    return (
      <div className="relative w-full h-full overflow-hidden rounded-[5px] bg-twilight/10 dark:bg-eggshell/10 flex items-center justify-center border-2 border-dashed border-twilight/20 dark:border-eggshell/20">
        <div className="text-center p-4">
          <Camera className="w-8 h-8 mx-auto mb-2 text-twilight/30 dark:text-eggshell/30" />
          <p className="text-xs text-twilight/40 dark:text-eggshell/40">Showcase {showcaseId}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full overflow-hidden rounded-[5px]">
      {/* Previous image - slides out to the left */}
      {previousIndex !== null && (
        <img
          src={images[previousIndex]}
          alt={`Showcase ${showcaseId} - ${previousIndex + 1}`}
          className="absolute inset-0 w-full h-full object-cover animate-slide-out-left"
          style={{
            animationDuration: `${SLIDE_DURATION}ms`,
          }}
        />
      )}
      {/* Current image - slides in from the right (or static if not sliding) */}
      <img
        src={images[currentIndex]}
        alt={`Showcase ${showcaseId} - ${currentIndex + 1}`}
        className={`absolute inset-0 w-full h-full object-cover ${
          isSliding && previousIndex !== null ? 'animate-slide-in-right' : ''
        }`}
        style={{
          animationDuration: `${SLIDE_DURATION}ms`,
        }}
      />
      {/* Image indicator dots */}
      {images.length > 1 && (
        <div className="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {images.map((_, idx) => (
            <button
              key={idx}
              onClick={() => slideToIndex(idx)}
              className={`w-2.5 h-2.5 rounded-full transition-all duration-200 ${
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
// EXPERIENCE SECTION - CENTERED TIMELINE
// Elegant alternating left/right timeline layout
// with showcase cards and connecting lines
// ============================================
const ExperienceSection = () => {
  /**
   * Timeline experience data - 7 entries from Dec 2025 to 2016
   * Each entry alternates between left and right positioning
   */
  const experiences = [
    {
      id: 1,
      title: 'Software Engineer',
      company: 'Tech Innovation Corp',
      period: 'December 2025',
      description: 'Leading full-stack development initiatives, architecting scalable solutions with React, Node.js, and cloud services. Implementing CI/CD pipelines and mentoring junior developers.',
      tags: ['React', 'Node.js', 'AWS', 'TypeScript'],
      color: 'burnt-peach',
    },
    {
      id: 2,
      title: 'Full Stack Developer',
      company: 'Digital Solutions Inc',
      period: '2024',
      description: 'Built and deployed production-ready web applications serving thousands of users. Optimized database queries resulting in 40% performance improvement.',
      tags: ['Next.js', 'PostgreSQL', 'Docker'],
      color: 'muted-teal',
    },
    {
      id: 3,
      title: 'Software Development Intern',
      company: 'StartupXYZ',
      period: '2023',
      description: 'Developed RESTful APIs and integrated third-party services. Contributed to agile sprints and participated in code reviews with senior engineers.',
      tags: ['Python', 'FastAPI', 'Git'],
      color: 'apricot',
    },
    {
      id: 4,
      title: 'Freelance Web Developer',
      company: 'Self-Employed',
      period: '2022',
      description: 'Delivered custom websites and e-commerce solutions for small businesses. Managed client relationships and project timelines independently.',
      tags: ['JavaScript', 'WordPress', 'CSS'],
      color: 'burnt-peach',
    },
    {
      id: 5,
      title: 'Research Assistant',
      company: 'University CS Department',
      period: '2020',
      description: 'Assisted in machine learning research projects. Processed datasets, implemented algorithms, and co-authored a conference paper on NLP techniques.',
      tags: ['Python', 'TensorFlow', 'NLP'],
      color: 'muted-teal',
    },
    {
      id: 6,
      title: 'IT Support Technician',
      company: 'Campus Tech Services',
      period: '2018',
      description: 'Provided technical support for faculty and students. Troubleshot hardware/software issues and maintained computer lab equipment.',
      tags: ['Troubleshooting', 'Windows', 'Linux'],
      color: 'apricot',
    },
    {
      id: 7,
      title: 'Programming Hobbyist',
      company: 'Self-Taught Journey',
      period: '2016',
      description: 'Discovered passion for programming through game development and automation scripts. Built first website and learned fundamentals of coding logic.',
      tags: ['Java', 'HTML', 'CSS'],
      color: 'burnt-peach',
    },
  ];

  return (
    <section id="experience" className="py-6 relative">
      <div className="container mx-auto px-6">
        <div className="relative bg-background/30 backdrop-blur-sm rounded-[5px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-8">
          <InteractiveGridDots />
          <div className="relative z-10">
            {/* Section Header */}
            <h2 className="text-3xl md:text-4xl font-bold text-twilight dark:text-eggshell mb-8 text-center">
              <span className="text-burnt-peach">My Experience</span>
            </h2>

            {/* Centered Timeline Container */}
            <div className="relative max-w-5xl mx-auto px-4">
              {/* Central Timeline Line */}
              <div className="absolute left-1/2 top-0 bottom-0 w-1 bg-gradient-to-b from-burnt-peach via-muted-teal to-apricot transform -translate-x-1/2 rounded-full hidden md:block" />
              
              {/* Mobile Timeline Line (left-aligned) */}
              <div className="absolute left-4 top-0 bottom-0 w-1 bg-gradient-to-b from-burnt-peach via-muted-teal to-apricot rounded-full md:hidden" />

              {/* Timeline Entries */}
              {experiences.map((exp, index) => {
                const isLeft = index % 2 === 0;
                
                return (
                  <div
                    key={exp.id}
                    className={`relative -mb-4 last:mb-0 opacity-0 animate-slide-up`}
                    style={{ animationDelay: `${index * 150}ms` }}
                  >
                    {/* Desktop Layout - Alternating */}
                    <div className="hidden md:grid md:grid-cols-[1fr_60px_1fr] gap-0 items-center">
                      {/* Left Side Content */}
                      <div className={`${isLeft ? 'pr-4' : ''}`}>
                        {isLeft ? (
                          /* Showcase Card - Left */
                          <div className="flex justify-end">
                            <div className="relative w-full max-w-sm bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 overflow-hidden group glass">
                              {/* Showcase Image Container */}
                              <div className="aspect-[16/10] relative">
                                <TimelineShowcaseCarousel showcaseId={exp.id} />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                                {/* Period Badge */}
                                <div className={`absolute top-3 right-3 px-3 py-1 bg-${exp.color}/90 text-eggshell text-xs font-semibold rounded-full shadow-md pointer-events-none`}>
                                  {exp.period}
                                </div>
                              </div>
                              {/* Card Content */}
                              <div className="p-4">
                                <h3 className="text-lg font-bold text-twilight dark:text-eggshell mb-1 group-hover:text-burnt-peach transition-colors">
                                  {exp.title}
                                </h3>
                                <p className="text-muted-teal font-medium text-sm mb-2">{exp.company}</p>
                                {/* Tags */}
                                <div className="flex flex-wrap gap-1.5">
                                  {exp.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full hover:bg-muted-teal hover:text-eggshell transition-all duration-200"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          /* Description Card - Left */
                          <div className="flex justify-end">
                            <div className="w-full max-w-sm text-right">
                              <div className="bg-white/50 dark:bg-twilight/30 backdrop-blur-sm rounded-[5px] p-5 border border-twilight/10 dark:border-eggshell/10 hover:border-muted-teal/50 transition-all duration-300">
                                <p className="text-twilight/80 dark:text-eggshell/80 text-sm leading-relaxed">
                                  {exp.description}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Center - Timeline Node with Connecting Lines */}
                      <div className="relative flex items-center justify-center">
                        {/* Connecting Line - Left */}
                        <div className={`absolute h-0.5 bg-gradient-to-r ${
                          isLeft 
                            ? `from-${exp.color}/60 to-${exp.color} right-1/2 w-[30px]`
                            : `from-${exp.color} to-${exp.color}/60 left-1/2 w-[30px]`
                        }`} />
                        {/* Connecting Line - Right */}
                        <div className={`absolute h-0.5 bg-gradient-to-r ${
                          isLeft 
                            ? `from-${exp.color} to-${exp.color}/60 left-1/2 w-[30px]`
                            : `from-${exp.color}/60 to-${exp.color} right-1/2 w-[30px]`
                        }`} />
                        {/* Timeline Node */}
                        <div className={`relative z-10 w-10 h-10 rounded-full bg-${exp.color} flex items-center justify-center shadow-lg animate-pulse-glow`}>
                          <Briefcase className="w-5 h-5 text-eggshell" />
                        </div>
                      </div>

                      {/* Right Side Content */}
                      <div className={`${!isLeft ? 'pl-4' : ''}`}>
                        {!isLeft ? (
                          /* Showcase Card - Right */
                          <div className="flex justify-start">
                            <div className="relative w-full max-w-sm bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1 overflow-hidden group glass">
                              {/* Showcase Image Container */}
                              <div className="aspect-[16/10] relative">
                                <TimelineShowcaseCarousel showcaseId={exp.id} />
                                {/* Gradient Overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                                {/* Period Badge */}
                                <div className={`absolute top-3 left-3 px-3 py-1 bg-${exp.color}/90 text-eggshell text-xs font-semibold rounded-full shadow-md pointer-events-none`}>
                                  {exp.period}
                                </div>
                              </div>
                              {/* Card Content */}
                              <div className="p-4">
                                <h3 className="text-lg font-bold text-twilight dark:text-eggshell mb-1 group-hover:text-burnt-peach transition-colors">
                                  {exp.title}
                                </h3>
                                <p className="text-muted-teal font-medium text-sm mb-2">{exp.company}</p>
                                {/* Tags */}
                                <div className="flex flex-wrap gap-1.5">
                                  {exp.tags.map((tag) => (
                                    <span
                                      key={tag}
                                      className="px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full hover:bg-muted-teal hover:text-eggshell transition-all duration-200"
                                    >
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </div>
                        ) : (
                          /* Description Card - Right */
                          <div className="flex justify-start">
                            <div className="w-full max-w-sm text-left">
                              <div className="bg-white/50 dark:bg-twilight/30 backdrop-blur-sm rounded-[5px] p-5 border border-twilight/10 dark:border-eggshell/10 hover:border-muted-teal/50 transition-all duration-300">
                                <p className="text-twilight/80 dark:text-eggshell/80 text-sm leading-relaxed">
                                  {exp.description}
                                </p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Mobile Layout - Single Column */}
                    <div className="md:hidden relative pl-12">
                      {/* Connecting Line to Timeline */}
                      <div className={`absolute left-4 top-6 w-6 h-0.5 bg-${exp.color}`} />
                      
                      {/* Timeline Node */}
                      <div className={`absolute left-1 top-3 w-7 h-7 rounded-full bg-${exp.color} flex items-center justify-center shadow-md z-10`}>
                        <Briefcase className="w-3.5 h-3.5 text-eggshell" />
                      </div>

                      {/* Combined Card for Mobile */}
                      <div className="bg-white dark:bg-twilight/50 rounded-[5px] shadow-lg overflow-hidden glass">
                        {/* Showcase Image */}
                        <div className="aspect-[16/9] relative">
                          <TimelineShowcaseCarousel showcaseId={exp.id} />
                          <div className="absolute inset-0 bg-gradient-to-t from-twilight/60 via-transparent to-transparent pointer-events-none" />
                          <div className={`absolute top-2 right-2 px-2 py-0.5 bg-${exp.color}/90 text-eggshell text-xs font-semibold rounded-full pointer-events-none`}>
                            {exp.period}
                          </div>
                        </div>
                        {/* Content */}
                        <div className="p-4">
                          <h3 className="text-base font-bold text-twilight dark:text-eggshell mb-1">
                            {exp.title}
                          </h3>
                          <p className="text-muted-teal font-medium text-sm mb-2">{exp.company}</p>
                          <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed mb-3">
                            {exp.description}
                          </p>
                          <div className="flex flex-wrap gap-1.5">
                            {exp.tags.map((tag) => (
                              <span
                                key={tag}
                                className="px-2 py-0.5 bg-twilight/5 dark:bg-eggshell/10 text-twilight dark:text-eggshell text-xs rounded-full"
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

              {/* Timeline End Cap */}
              <div className="hidden md:flex justify-center mt-4">
                <div className="w-4 h-4 rounded-full bg-gradient-to-br from-apricot to-burnt-peach shadow-lg" />
              </div>
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
            <a href="mailto:hello@example.com" className="flex items-center gap-2">
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
