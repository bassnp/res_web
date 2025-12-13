'use client';

import * as React from 'react';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

/**
 * Select Component
 * A styled dropdown select for model selection.
 */
const Select = React.forwardRef(({ 
  className, 
  value, 
  onChange, 
  options = [],
  placeholder = 'Select an option',
  disabled = false,
  ...props 
}, ref) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const selectRef = React.useRef(null);
  
  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event) => {
      if (selectRef.current && !selectRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  // Find selected option
  const selectedOption = options.find(opt => opt.id === value);
  
  const handleSelect = (optionId) => {
    onChange?.(optionId);
    setIsOpen(false);
  };

  return (
    <div 
      ref={selectRef}
      className={cn("relative", className)}
      {...props}
    >
      {/* Trigger Button */}
      <button
        ref={ref}
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={cn(
          "flex w-full items-center justify-between gap-2",
          "rounded-sm border border-twilight/20 dark:border-eggshell/20",
          "bg-white/80 dark:bg-twilight/40",
          "px-4 py-3 text-left text-sm",
          "transition-all duration-200",
          "hover:border-burnt-peach/50 focus:outline-none focus:ring-2 focus:ring-burnt-peach/30",
          disabled && "opacity-50 cursor-not-allowed",
          isOpen && "border-burnt-peach ring-2 ring-burnt-peach/20"
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex-1 min-w-0">
          {selectedOption ? (
            <div className="flex items-center gap-2">
              <span className="font-medium text-twilight dark:text-eggshell truncate">
                {selectedOption.label}
              </span>
              {selectedOption.badge && (
                <span className={cn(
                  "px-2 py-0.5 text-xs font-medium rounded-full",
                  selectedOption.badge === 'Recommended' 
                    ? "bg-muted-teal/20 text-muted-teal" 
                    : "bg-burnt-peach/20 text-burnt-peach"
                )}>
                  {selectedOption.badge}
                </span>
              )}
            </div>
          ) : (
            <span className="text-twilight/50 dark:text-eggshell/50">
              {placeholder}
            </span>
          )}
        </div>
        <ChevronDown 
          className={cn(
            "w-4 h-4 text-twilight/60 dark:text-eggshell/60 transition-transform duration-200",
            isOpen && "rotate-180"
          )} 
        />
      </button>
      
      {/* Dropdown Menu */}
      {isOpen && (
        <div 
          className={cn(
            "absolute z-50 w-full mt-2",
            "bg-white dark:bg-twilight",
            "border border-twilight/20 dark:border-eggshell/20",
            "rounded-sm shadow-lg",
            "animate-in fade-in-0 zoom-in-95 duration-150",
            "overflow-hidden"
          )}
          role="listbox"
        >
          {options.map((option) => (
            <button
              key={option.id}
              type="button"
              onClick={() => handleSelect(option.id)}
              className={cn(
                "flex w-full items-center gap-3 px-4 py-3",
                "text-left transition-colors duration-150",
                "hover:bg-twilight/5 dark:hover:bg-eggshell/5",
                value === option.id && "bg-burnt-peach/10"
              )}
              role="option"
              aria-selected={value === option.id}
            >
              {/* Check Icon */}
              <div className={cn(
                "w-4 h-4 flex-shrink-0",
                value === option.id ? "opacity-100" : "opacity-0"
              )}>
                <Check className="w-4 h-4 text-burnt-peach" />
              </div>
              
              {/* Option Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={cn(
                    "font-medium",
                    value === option.id 
                      ? "text-burnt-peach" 
                      : "text-twilight dark:text-eggshell"
                  )}>
                    {option.label}
                  </span>
                  {option.badge && (
                    <span className={cn(
                      "px-2 py-0.5 text-xs font-medium rounded-full",
                      option.badge === 'Recommended' 
                        ? "bg-muted-teal/20 text-muted-teal" 
                        : "bg-burnt-peach/20 text-burnt-peach"
                    )}>
                      {option.badge}
                    </span>
                  )}
                </div>
                {option.description && (
                  <p className="text-xs text-twilight/60 dark:text-eggshell/60 mt-0.5">
                    {option.description}
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
});

Select.displayName = 'Select';

export { Select };
