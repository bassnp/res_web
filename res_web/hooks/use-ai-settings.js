'use client';

import { createContext, useContext, useState, useCallback } from 'react';

/**
 * AI Model Configuration
 * 
 * Model options with their specific configuration requirements:
 * - gemini-3-pro-preview: Uses high reasoning syntax (thinking_config)
 * - gemini-flash-latest: Uses temperature and topK for accuracy
 */

export const AI_MODELS = {
  'gemini-3-pro-preview': {
    id: 'gemini-3-pro-preview',
    label: 'Gemini 3 Pro (Preview)',
    description: 'Advanced reasoning with deep analysis',
    configType: 'reasoning', // Uses thinking_config for high reasoning
    badge: 'Recommended',
  },
  'gemini-flash-latest': {
    id: 'gemini-flash-latest',
    label: 'Gemini Flash (Latest)',
    description: 'Fast responses with balanced accuracy',
    configType: 'standard', // Uses temperature and topK
    badge: 'Fast',
  },
};

export const DEFAULT_MODEL = 'gemini-flash-latest';

/**
 * AI Settings Context
 * Provides global AI model configuration for the application.
 */
const AISettingsContext = createContext(null);

/**
 * AISettingsProvider Component
 * Wraps the application to provide AI model settings context.
 */
export function AISettingsProvider({ children }) {
  const [selectedModel, setSelectedModel] = useState(DEFAULT_MODEL);

  const updateModel = useCallback((modelId) => {
    if (AI_MODELS[modelId]) {
      setSelectedModel(modelId);
    }
  }, []);

  const getModelConfig = useCallback(() => {
    const model = AI_MODELS[selectedModel];
    return {
      model_id: model.id,
      config_type: model.configType,
    };
  }, [selectedModel]);

  const value = {
    selectedModel,
    modelInfo: AI_MODELS[selectedModel],
    models: AI_MODELS,
    updateModel,
    getModelConfig,
  };

  return (
    <AISettingsContext.Provider value={value}>
      {children}
    </AISettingsContext.Provider>
  );
}

/**
 * useAISettings Hook
 * Access AI model settings from any component.
 */
export function useAISettings() {
  const context = useContext(AISettingsContext);
  if (!context) {
    throw new Error('useAISettings must be used within an AISettingsProvider');
  }
  return context;
}

export default AISettingsContext;
