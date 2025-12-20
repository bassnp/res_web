'use client';

import { useState, useCallback } from 'react';
import { API_BASE_URL } from '@/lib/profile-data';

/**
 * API URL for backend requests.
 * Falls back to SPOT configuration for development.
 */
const API_URL = process.env.NEXT_PUBLIC_API_URL || API_BASE_URL;

/**
 * Custom hook for generating example job queries.
 * 
 * Provides functionality to generate good or bad example queries
 * that can be used to demonstrate the fit check feature.
 * 
 * @returns {Object} State and control functions
 * @property {boolean} isLoading - Whether a generation is in progress
 * @property {string|null} generatedExample - The most recently generated example
 * @property {string|null} error - Error message if generation failed
 * @property {Function} generateGoodExample - Generate a well-matched example
 * @property {Function} generateBadExample - Generate a poorly-matched example
 * @property {Function} clearExample - Clear the current example
 */
export function useExampleGenerator() {
  const [state, setState] = useState({
    isLoading: false,
    generatedExample: null,
    exampleType: null,
    quality: null,
    error: null,
  });

  /**
   * Generate an example of the specified quality.
   * 
   * @param {'good' | 'bad'} quality - Quality of example to generate
   */
  const generateExample = useCallback(async (quality) => {
    setState(prev => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await fetch(`${API_URL}/api/examples/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ quality }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success && data.example) {
        setState({
          isLoading: false,
          generatedExample: data.example,
          exampleType: data.example_type,
          quality: data.quality,
          error: null,
        });
        return data.example;
      } else {
        throw new Error(data.error || 'Failed to generate example');
      }
    } catch (error) {
      console.error('Example generation error:', error);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error.message || 'Failed to generate example',
      }));
      return null;
    }
  }, []);

  /**
   * Generate a well-matched (good) example.
   * Returns the generated example text.
   */
  const generateGoodExample = useCallback(() => {
    return generateExample('good');
  }, [generateExample]);

  /**
   * Generate a poorly-matched (bad) example.
   * Returns the generated example text.
   */
  const generateBadExample = useCallback(() => {
    return generateExample('bad');
  }, [generateExample]);

  /**
   * Clear the current example and error state.
   */
  const clearExample = useCallback(() => {
    setState({
      isLoading: false,
      generatedExample: null,
      exampleType: null,
      quality: null,
      error: null,
    });
  }, []);

  return {
    isLoading: state.isLoading,
    generatedExample: state.generatedExample,
    exampleType: state.exampleType,
    quality: state.quality,
    error: state.error,
    generateGoodExample,
    generateBadExample,
    clearExample,
  };
}

export default useExampleGenerator;
