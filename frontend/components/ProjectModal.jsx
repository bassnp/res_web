'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, ChevronLeft, ChevronRight, Eye, Code, Lightbulb, BookOpen, ExternalLink } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

// ============================================
// CONSTANTS
// ============================================
const CAROUSEL_SLIDE_DURATION = 400; // ms for slide animation

/**
 * ProjectImageCarousel Component
 * 
 * A large, interactive image carousel for project showcase modals.
 * Features smooth slide transitions and navigation controls.
 * 
 * @param {Object} props
 * @param {string} props.imagesFolder - Folder name in /resources/project_images/ containing project images
 * @param {string[]} props.fallbackImages - Fallback images if manifest fails to load
 */
const ProjectImageCarousel = ({ imagesFolder, fallbackImages = [] }) => {
  const [images, setImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [previousIndex, setPreviousIndex] = useState(null);
  const [slideDirection, setSlideDirection] = useState('right'); // 'left' or 'right'
  const [isSliding, setIsSliding] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  /**
   * Fetch project images from manifest on mount.
   * Falls back to provided fallbackImages if manifest unavailable.
   */
  useEffect(() => {
    const loadImages = async () => {
      // Skip fetch if no folder specified
      if (!imagesFolder) {
        if (fallbackImages.length > 0) {
          setImages(fallbackImages);
        }
        setIsLoading(false);
        return;
      }

      try {
        const response = await fetch(`/resources/project_images/${imagesFolder}/manifest.json`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data = await response.json();
        if (data.images && data.images.length > 0) {
          setImages(data.images);
        } else if (fallbackImages.length > 0) {
          setImages(fallbackImages);
        }
      } catch (error) {
        console.warn(`Failed to load manifest for ${imagesFolder}:`, error.message);
        if (fallbackImages.length > 0) {
          setImages(fallbackImages);
        }
      } finally {
        setIsLoading(false);
      }
    };

    loadImages();
  }, [imagesFolder, fallbackImages]);

  /**
   * Navigate to a specific slide with direction-aware animation.
   */
  const slideToIndex = useCallback((newIndex, direction = 'right') => {
    if (isSliding || newIndex === currentIndex || images.length === 0) return;
    
    setSlideDirection(direction);
    setPreviousIndex(currentIndex);
    setCurrentIndex(newIndex);
    setIsSliding(true);
    
    setTimeout(() => {
      setIsSliding(false);
      setPreviousIndex(null);
    }, CAROUSEL_SLIDE_DURATION);
  }, [isSliding, currentIndex, images.length]);

  /**
   * Navigate to previous slide.
   */
  const goToPrevious = useCallback(() => {
    const prevIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
    slideToIndex(prevIndex, 'left');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Navigate to next slide.
   */
  const goToNext = useCallback(() => {
    const nextIndex = (currentIndex + 1) % images.length;
    slideToIndex(nextIndex, 'right');
  }, [currentIndex, images.length, slideToIndex]);

  /**
   * Keyboard navigation support.
   */
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'ArrowLeft') goToPrevious();
      if (e.key === 'ArrowRight') goToNext();
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [goToPrevious, goToNext]);

  // Loading state
  if (isLoading) {
    return (
      <div className="relative w-full aspect-[16/9] bg-twilight/10 dark:bg-eggshell/10 rounded-sm overflow-hidden flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center gap-2">
          <Code className="w-12 h-12 text-twilight/30 dark:text-eggshell/30" />
          <span className="text-sm text-twilight/40 dark:text-eggshell/40">Loading images...</span>
        </div>
      </div>
    );
  }

  // Empty state - show placeholder
  if (images.length === 0) {
    return (
      <div className="relative w-full aspect-[16/9] bg-twilight/10 dark:bg-eggshell/10 rounded-sm overflow-hidden flex items-center justify-center border-2 border-dashed border-twilight/20 dark:border-eggshell/20">
        <div className="text-center p-4">
          <Code className="w-12 h-12 mx-auto mb-2 text-twilight/30 dark:text-eggshell/30" />
          <p className="text-sm text-twilight/50 dark:text-eggshell/50">Project images coming soon</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full aspect-[16/9] bg-twilight/10 dark:bg-eggshell/10 rounded-sm overflow-hidden group">
      {/* Previous image - slides out */}
      {previousIndex !== null && (
        <img
          src={images[previousIndex]}
          alt={`Project image ${previousIndex + 1}`}
          className={cn(
            "absolute inset-0 w-full h-full object-contain",
            slideDirection === 'right' ? 'animate-carousel-slide-out-left' : 'animate-carousel-slide-out-right'
          )}
          style={{ animationDuration: `${CAROUSEL_SLIDE_DURATION}ms` }}
        />
      )}
      
      {/* Current image - slides in or static */}
      <img
        src={images[currentIndex]}
        alt={`Project image ${currentIndex + 1}`}
        className={cn(
          "absolute inset-0 w-full h-full object-contain",
          isSliding && previousIndex !== null && (
            slideDirection === 'right' ? 'animate-carousel-slide-in-right' : 'animate-carousel-slide-in-left'
          )
        )}
        style={{ animationDuration: `${CAROUSEL_SLIDE_DURATION}ms` }}
      />

      {/* Navigation arrows - only show if multiple images */}
      {images.length > 1 && (
        <>
          {/* Left arrow */}
          <button
            onClick={goToPrevious}
            className={cn(
              "absolute left-2 top-1/2 -translate-y-1/2 z-10",
              "w-10 h-10 rounded-full",
              "bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm",
              "flex items-center justify-center",
              "opacity-0 group-hover:opacity-100 transition-opacity duration-300",
              "hover:bg-muted-teal hover:scale-110 transition-all",
              "focus:outline-none focus:ring-2 focus:ring-muted-teal"
            )}
            aria-label="Previous image"
          >
            <ChevronLeft className="w-6 h-6 text-eggshell" />
          </button>

          {/* Right arrow */}
          <button
            onClick={goToNext}
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2 z-10",
              "w-10 h-10 rounded-full",
              "bg-muted-teal/90 dark:bg-muted-teal/80 backdrop-blur-sm",
              "flex items-center justify-center",
              "opacity-0 group-hover:opacity-100 transition-opacity duration-300",
              "hover:bg-muted-teal hover:scale-110 transition-all",
              "focus:outline-none focus:ring-2 focus:ring-muted-teal"
            )}
            aria-label="Next image"
          >
            <ChevronRight className="w-6 h-6 text-eggshell" />
          </button>
        </>
      )}

      {/* Image indicator dots */}
      {images.length > 1 && (
        <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2 z-10">
          {images.map((_, idx) => (
            <button
              key={idx}
              onClick={() => slideToIndex(idx, idx > currentIndex ? 'right' : 'left')}
              className={cn(
                "w-2.5 h-2.5 rounded-full transition-all duration-300",
                idx === currentIndex
                  ? "bg-burnt-peach scale-125 shadow-[0_0_8px_rgba(224,122,95,0.5)]"
                  : "bg-eggshell/60 hover:bg-eggshell/80"
              )}
              aria-label={`Go to image ${idx + 1}`}
            />
          ))}
        </div>
      )}

      {/* Image counter badge */}
      <div className="absolute top-3 right-3 px-2.5 py-1 rounded-full bg-twilight/60 dark:bg-eggshell/20 backdrop-blur-sm">
        <span className="text-xs font-medium text-eggshell">
          {currentIndex + 1} / {images.length}
        </span>
      </div>
    </div>
  );
};

/**
 * ProjectModal Component
 * 
 * Full-featured project details modal with:
 * - Large image carousel with dynamic image loading
 * - Two-column layout: About the Project & Learning Outcomes
 * - Elegant animations and glassmorphism effects
 * 
 * @param {Object} props
 * @param {Object} props.project - Project data object
 * @param {string} props.project.id - Unique identifier for image manifest lookup
 * @param {string} props.project.title - Project title
 * @param {string} props.project.description - Brief description
 * @param {string} props.project.about - Detailed project description
 * @param {string[]} props.project.learningOutcomes - Array of learning outcomes
 * @param {string[]} props.project.tags - Technology tags
 * @param {string} props.project.color - Gradient color class
 * @param {string} props.project.link - Optional external project link
 * @param {boolean} props.open - Controlled open state
 * @param {Function} props.onOpenChange - Open state change handler
 * @param {React.ReactNode} props.children - Trigger element
 */
export function ProjectModal({ 
  project, 
  open, 
  onOpenChange,
  children 
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        {children}
      </DialogTrigger>
      <DialogContent 
        className={cn(
          "bg-eggshell dark:bg-twilight",
          "border-twilight/20 dark:border-eggshell/20",
          "max-w-4xl w-[95vw] max-h-[90vh]",
          "overflow-y-auto overflow-x-hidden",
          "p-0"
        )}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        {/* Hidden accessible description for screen readers */}
        <DialogDescription className="sr-only">
          Detailed view of {project.title} project including images, description, and learning outcomes.
        </DialogDescription>
        
        {/* Header with gradient accent */}
        <div className={cn(
          "relative overflow-hidden",
          "p-6 pb-4",
          "border-b border-twilight/10 dark:border-eggshell/10"
        )}>
          {/* Subtle gradient background */}
          <div 
            className={cn(
              "absolute inset-0 opacity-10",
              `bg-gradient-to-br ${project.color}`
            )} 
          />
          
          <DialogHeader className="relative z-10">
            <DialogTitle className="text-2xl font-bold text-twilight dark:text-eggshell flex items-center gap-3">
              <div className={cn(
                "w-10 h-10 rounded-sm flex items-center justify-center",
                `bg-gradient-to-br ${project.color}`
              )}>
                <Code className="w-5 h-5 text-eggshell" />
              </div>
              {project.title}
              {project.link && (
                <a 
                  href={project.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-auto p-2 rounded-sm hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-colors"
                  aria-label="View project"
                >
                  <ExternalLink className="w-5 h-5 text-muted-teal" />
                </a>
              )}
            </DialogTitle>
          </DialogHeader>

          {/* Tags */}
          <div className="flex flex-wrap gap-2 mt-3 relative z-10">
            {project.tags.map((tag) => (
              <span 
                key={tag} 
                className={cn(
                  "px-3 py-1 rounded-full text-xs font-medium",
                  "bg-muted-teal/15 dark:bg-muted-teal/25",
                  "text-muted-teal dark:text-muted-teal",
                  "border border-muted-teal/20"
                )}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        {/* Image Carousel Section */}
        <div className="px-6 pt-6">
          <ProjectImageCarousel 
            imagesFolder={project.images_folder || project.imagesFolder} 
            fallbackImages={project.images || []}
          />
        </div>

        {/* Two-Column Content Section */}
        <div className="p-6 grid md:grid-cols-2 gap-6">
          {/* Column 1: About the Project */}
          <div className={cn(
            "p-5 rounded-sm",
            "bg-twilight/5 dark:bg-eggshell/5",
            "border border-twilight/10 dark:border-eggshell/10",
            "hover:border-muted-teal/30 transition-colors duration-300"
          )}>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-sm bg-muted-teal/15">
                <BookOpen className="w-4 h-4 text-muted-teal" />
              </div>
              <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">
                About the Project
              </h3>
            </div>
            <p className="text-sm text-twilight/80 dark:text-eggshell/80 leading-relaxed">
              {project.about || project.description}
            </p>
          </div>

          {/* Column 2: Learning Outcomes */}
          <div className={cn(
            "p-5 rounded-sm",
            "bg-twilight/5 dark:bg-eggshell/5",
            "border border-twilight/10 dark:border-eggshell/10",
            "hover:border-muted-teal/30 transition-colors duration-300"
          )}>
            <div className="flex items-center gap-2 mb-4">
              <div className="p-2 rounded-sm bg-muted-teal/15">
                <Lightbulb className="w-4 h-4 text-muted-teal" />
              </div>
              <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">
                Learning Outcomes
              </h3>
            </div>
            {project.learningOutcomes && project.learningOutcomes.length > 0 ? (
              <ul className="space-y-2">
                {project.learningOutcomes.map((outcome, idx) => (
                  <li 
                    key={idx}
                    className="flex items-start gap-2 text-sm text-twilight/80 dark:text-eggshell/80"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-teal mt-2 flex-shrink-0" />
                    <span className="leading-relaxed">{outcome}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-twilight/60 dark:text-eggshell/60 italic">
                Learning outcomes to be documented.
              </p>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * ReadSummaryButton Component
 * 
 * Eye icon button with "Read summary" label in a rounded container.
 * Used as the call-to-action on project cards.
 */
export function ReadSummaryButton({ className }) {
  return (
    <div 
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1",
        "rounded-full",
        "bg-twilight/5 dark:bg-eggshell/15",
        "border border-twilight/15 dark:border-eggshell/20",
        "group-hover:bg-muted-teal/20 group-hover:border-muted-teal/40",
        "transition-all duration-300",
        className
      )}
    >
      <Eye className="w-3.5 h-3.5 text-muted-teal transition-transform duration-300 group-hover:scale-110" />
      <span className="text-xs font-medium text-twilight/60 dark:text-eggshell/80 group-hover:text-muted-teal transition-colors">
        Read more...
      </span>
    </div>
  );
}

export default ProjectModal;
