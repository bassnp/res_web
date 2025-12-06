'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { Settings, Briefcase, User, Mail, Github, ChevronDown, ExternalLink, Sun, Moon, Code, Cpu } from 'lucide-react';
import { useHeaderVisibility } from '@/hooks/use-header-visibility';
import { useAISettings, AI_MODELS } from '@/hooks/use-ai-settings';
import { InfoDialog, InfoButton } from '@/components/fit-check/InfoDialog';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from '@/components/ui/dialog';
import ParticleBackground from '@/components/ParticleBackground';
import InteractiveGridDots from '@/components/InteractiveGridDots';
import CardGridDots from '@/components/CardGridDots';
import HeroGridDots from '@/components/HeroGridDots';
import FitCheckSection from '@/components/FitCheckSection';

// ============================================
// HEADER COMPONENT
// ============================================
const Header = () => {
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [infoOpen, setInfoOpen] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const { selectedModel, updateModel, modelInfo } = useAISettings();
  
  // Convert AI_MODELS object to array for Select component
  const modelOptions = Object.values(AI_MODELS);
  
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
        <div className={`relative rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden transition-all duration-300
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
              className="group p-2 rounded-lg hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-all duration-300 hover:scale-110"
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
                    className="relative z-20 px-4 py-2 text-sm font-medium text-twilight dark:text-eggshell hover:text-eggshell transition-all duration-300 rounded-lg hover:bg-burnt-peach"
                  >
                    {item.name}
                  </a>
                ))}
              </nav>

              {/* Info & Settings */}
              <div className="flex items-center gap-1">
                {/* Info Button */}
                <InfoDialog 
                  open={infoOpen} 
                  onOpenChange={setInfoOpen}
                  trigger={<InfoButton onClick={() => {}} />}
                />

                {/* Settings Icon */}
              <Dialog open={settingsOpen} onOpenChange={setSettingsOpen}>
                <DialogTrigger asChild>
                  <button className="group p-2 rounded-lg hover:bg-twilight/10 dark:hover:bg-eggshell/10 transition-all duration-300">
                    <Settings className="w-6 h-6 text-twilight dark:text-eggshell transition-transform duration-300 group-hover:rotate-90" />
                  </button>
                </DialogTrigger>
                <DialogContent className="bg-eggshell dark:bg-twilight border-twilight/20 dark:border-eggshell/20">
                  <DialogHeader>
                    <DialogTitle className="text-twilight dark:text-eggshell flex items-center gap-2">
                      <Settings className="w-5 h-5 text-burnt-peach" />
                      Settings
                    </DialogTitle>
                    <DialogDescription className="text-twilight/60 dark:text-eggshell/60">
                      Configure your AI model preferences
                    </DialogDescription>
                  </DialogHeader>
                  <div className="py-4 space-y-4">
                    {/* AI Model Selection */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <Cpu className="w-4 h-4 text-burnt-peach" />
                        <label className="text-sm font-medium text-twilight dark:text-eggshell">
                          AI Model
                        </label>
                      </div>
                      
                      {/* Model Selection Buttons */}
                      <div className="grid gap-2">
                        {modelOptions.map((model) => (
                          <button
                            key={model.id}
                            onClick={() => updateModel(model.id)}
                            className={`relative w-full p-3 rounded-lg border text-left transition-all duration-200 
                              ${selectedModel === model.id 
                                ? 'border-burnt-peach bg-burnt-peach/10 dark:bg-burnt-peach/15' 
                                : 'border-twilight/15 dark:border-eggshell/15 hover:border-burnt-peach/50 hover:bg-twilight/5 dark:hover:bg-eggshell/5'
                              }`}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <div className={`w-3 h-3 rounded-full border-2 flex items-center justify-center transition-colors
                                  ${selectedModel === model.id 
                                    ? 'border-burnt-peach' 
                                    : 'border-twilight/30 dark:border-eggshell/30'
                                  }`}
                                >
                                  {selectedModel === model.id && (
                                    <div className="w-1.5 h-1.5 rounded-full bg-burnt-peach" />
                                  )}
                                </div>
                                <span className="text-sm font-medium text-twilight dark:text-eggshell">
                                  {model.label}
                                </span>
                              </div>
                              {model.badge && (
                                <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded-full
                                  ${model.badge === 'Recommended' 
                                    ? 'bg-burnt-peach/20 text-burnt-peach' 
                                    : 'bg-muted-teal/20 text-muted-teal'
                                  }`}
                                >
                                  {model.badge}
                                </span>
                              )}
                            </div>
                            <p className="mt-1 ml-5 text-xs text-twilight/60 dark:text-eggshell/60">
                              {model.description}
                            </p>
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
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
        <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-6">
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
                      className="p-2 rounded-lg bg-twilight/10 dark:bg-eggshell/10 hover:bg-burnt-peach/30 transition-all duration-300 hover:scale-110 hover:-translate-y-1"
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
// HERO + ABOUT SECTION (Combined)
// ============================================
const HeroAboutSection = () => {
  const [typedText, setTypedText] = useState('');
  const [showCursor, setShowCursor] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const fullText = 'Software Engineer';

  const skills = [
    'JavaScript', 'React', 'Next.js', 'Python', 'Node.js', 'TypeScript',
    'PostgreSQL', 'Git', 'AWS', 'Docker', 'TailwindCSS'
  ];

  // Cursor flashing effect during pause states
  useEffect(() => {
    let cursorInterval;
    
    if (isPaused) {
      setShowCursor(true);
      cursorInterval = setInterval(() => {
        setShowCursor(prev => !prev);
      }, 500);
    } else {
      setShowCursor(true);
    }

    return () => {
      if (cursorInterval) clearInterval(cursorInterval);
    };
  }, [isPaused]);

  useEffect(() => {
    let index = 0;
    let isDeleting = false;
    let isPausedLocal = false;
    let timer;

    const typewriterCycle = () => {
      if (!isDeleting && !isPausedLocal && index <= fullText.length) {
        setTypedText(fullText.slice(0, index));
        index++;
        timer = setTimeout(typewriterCycle, 100);
        
        if (index > fullText.length) {
          isPausedLocal = true;
          setIsPaused(true);
          timer = setTimeout(() => {
            isPausedLocal = false;
            setIsPaused(false);
            isDeleting = true;
            typewriterCycle();
          }, 3000);
        }
      }
      else if (isDeleting && !isPausedLocal && index >= 0) {
        setTypedText(fullText.slice(0, index));
        index--;
        timer = setTimeout(typewriterCycle, 80);
        
        if (index < 0) {
          isDeleting = false;
          isPausedLocal = true;
          setIsPaused(true);
          timer = setTimeout(() => {
            isPausedLocal = false;
            setIsPaused(false);
            index = 0;
            typewriterCycle();
          }, 1000);
        }
      }
    };

    typewriterCycle();

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, []);

  return (
    <section id="about" className="flex items-center pt-20 pb-4">
      <div className="container mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-4 items-stretch">
          {/* Left: Hero Content with Grid Dots */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden min-h-0 md:min-h-[300px] flex flex-col justify-center">
            <HeroGridDots />
            <div className="relative z-10 px-3 py-2 md:px-8 md:py-5 text-center">
              {/* Greeting */}
              <p className="text-burnt-peach font-medium mb-1 md:mb-2 opacity-0 animate-fade-in text-sm">
                Hello, I&apos;m
              </p>

              {/* Name with typing effect */}
              <h1 className="text-2xl md:text-5xl font-bold text-twilight dark:text-eggshell mb-2 md:mb-3 opacity-0 animate-fade-in delay-100">
                <span className="gradient-text">{typedText}</span>
                <span 
                  className="inline-block w-0.5 h-6 md:h-12 bg-burnt-peach ml-1 transition-opacity duration-100"
                  style={{ opacity: showCursor ? 1 : 0 }}
                />
              </h1>

              {/* Tagline */}
              <p className="text-sm md:text-lg text-twilight/70 dark:text-eggshell/70 mb-3 md:mb-4 opacity-0 animate-fade-in delay-200">
                Recent graduate &amp; hobbyist developer crafting elegant digital experiences
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-wrap justify-center gap-2 md:gap-3 opacity-0 animate-fade-in delay-300">
                <Button
                  asChild
                  className="bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell px-4 py-3 md:px-6 md:py-5 text-xs md:text-sm rounded-xl animate-pulse-glow hover:scale-105 transition-transform"
                >
                  <a href="#experience">View Work Experience</a>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-twilight dark:border-eggshell text-twilight dark:text-eggshell hover:bg-twilight hover:text-eggshell dark:hover:bg-eggshell dark:hover:text-twilight px-4 py-3 md:px-6 md:py-5 text-xs md:text-sm rounded-xl hover:scale-105 transition-transform"
                >
                  <a href="#contact">Get in Touch</a>
                </Button>
              </div>

              {/* Scroll indicator */}
              <div className="mt-3 md:mt-5 opacity-0 animate-fade-in delay-500">
                <a href="#projects" className="inline-flex flex-col items-center group">
                  <ChevronDown className="w-6 h-6 text-burnt-peach dark:text-muted-teal animate-bounce group-hover:animate-none group-hover:translate-y-1 transition-all" />
                </a>
              </div>
            </div>
          </div>

          {/* Right: About Content */}
          <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden flex flex-col">
            <InteractiveGridDots />
            <div className="relative z-10 p-6 md:p-8 flex-1 flex flex-col">
              <h2 className="text-2xl md:text-3xl font-bold text-twilight dark:text-eggshell mb-4 opacity-0 animate-fade-in">
                About <span className="text-burnt-peach">Me</span>
              </h2>

              {/* Profile mini */}
              <div className="flex items-center gap-4 mb-4 opacity-0 animate-fade-in-left delay-100">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-burnt-peach to-muted-teal flex items-center justify-center animate-morph-fast shadow-lg flex-shrink-0">
                  <User className="w-8 h-8 text-eggshell" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">Software Engineer</h3>
                  <p className="text-twilight/60 dark:text-eggshell/60 text-sm">Recent Graduate • Hobbyist Developer</p>
                </div>
              </div>

              {/* Bio */}
              <div className="opacity-0 animate-fade-in-right delay-200 flex-1">
                <p className="text-twilight/80 dark:text-eggshell/80 leading-relaxed mb-4 text-sm">
                  As a recent graduate with a passion for software development, I love building 
                  projects that solve real problems. My journey started as a hobbyist, and I&apos;ve 
                  grown into a developer who values clean code and elegant solutions.
                </p>
                <p className="text-twilight/80 dark:text-eggshell/80 leading-relaxed text-sm">
                  When I&apos;m not coding, you&apos;ll find me exploring new technologies, contributing 
                  to open-source projects, or learning about the latest trends in software engineering.
                </p>
              </div>

              {/* Skills */}
              <div className="mt-4 opacity-0 animate-fade-in delay-300">
                <h3 className="text-sm font-semibold text-twilight dark:text-eggshell mb-2">Skills &amp; Technologies</h3>
                <div className="flex flex-wrap gap-2">
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
          A selection of projects that showcase my skills and passion for building great software.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {projects.map((project, index) => (
            <div
              key={project.title}
              className="group bg-white dark:bg-twilight/50 rounded-2xl overflow-hidden shadow-lg hover:shadow-2xl transition-all duration-500 hover:-translate-y-1 opacity-0 animate-scale-in-no-transform glass flex flex-col"
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
// EXPERIENCE SECTION
// ============================================
const ExperienceSection = () => {
  const experiences = [
    {
      title: 'Software Engineer Intern',
      company: 'Tech Company',
      period: '2024 - Present',
      description: 'Developed and maintained web applications using modern JavaScript frameworks. Collaborated with cross-functional teams to deliver high-quality software solutions.',
    },
    {
      title: 'Freelance Developer',
      company: 'Self-Employed',
      period: '2023 - 2024',
      description: 'Built custom websites and applications for various clients. Managed full project lifecycle from requirements gathering to deployment.',
    },
    {
      title: 'Computer Science Graduate',
      company: 'University',
      period: '2020 - 2024',
      description: 'Bachelor of Science in Computer Science. Coursework included algorithms, data structures, software engineering, and database systems.',
    },
  ];

  return (
    <section id="experience" className="py-6 relative">
      <div className="container mx-auto px-6">
        <div className="relative bg-background/95 backdrop-blur-sm rounded-[10px] shadow-[0_2px_8px_rgba(61,64,91,0.08)] dark:shadow-[0_2px_12px_rgba(0,0,0,0.3)] border border-twilight/8 dark:border-eggshell/8 overflow-hidden py-6">
          <InteractiveGridDots />
          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-bold text-twilight dark:text-eggshell mb-3 text-center">
              Work <span className="text-burnt-peach">Experience</span>
            </h2>
            <p className="text-twilight/60 dark:text-eggshell/60 text-center mb-8 max-w-2xl mx-auto">
              My professional journey and educational background.
            </p>

            <div className="max-w-3xl mx-auto">
          {experiences.map((exp, index) => (
            <div
              key={exp.title}
              className="relative pl-8 pb-12 last:pb-0 opacity-0 animate-slide-up"
              style={{ animationDelay: `${index * 200}ms` }}
            >
              {/* Timeline line */}
              {index !== experiences.length - 1 && (
                <div className="absolute left-[11px] top-8 bottom-0 w-0.5 bg-gradient-to-b from-burnt-peach to-muted-teal" />
              )}

              {/* Timeline dot */}
              <div className="absolute left-0 top-1 w-6 h-6 rounded-full bg-burnt-peach flex items-center justify-center animate-pulse-glow">
                <Briefcase className="w-3 h-3 text-eggshell" />
              </div>

              {/* Content */}
              <div 
                data-work-experience-card
                className="bg-white dark:bg-twilight/50 rounded-xl p-6 shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 glass"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <h3 className="text-lg font-semibold text-twilight dark:text-eggshell">{exp.title}</h3>
                  <span className="text-sm text-burnt-peach font-medium">{exp.period}</span>
                </div>
                <p className="text-muted-teal font-medium text-sm mb-3">{exp.company}</p>
                  <p className="text-twilight/70 dark:text-eggshell/70 text-sm leading-relaxed">{exp.description}</p>
                </div>
              </div>
            ))}
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
            className="bg-burnt-peach hover:bg-burnt-peach/90 text-eggshell px-7 py-5 text-base rounded-xl animate-pulse-glow hover:scale-105 transition-transform relative z-10"
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
