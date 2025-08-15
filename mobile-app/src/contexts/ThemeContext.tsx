import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useColorScheme } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
  theme: 'light' | 'dark' | 'auto';
  setThemeMode: (mode: 'light' | 'dark' | 'auto') => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

const THEME_KEY = '@tonebridge_theme';

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [theme, setTheme] = useState<'light' | 'dark' | 'auto'>('auto');
  const [isDarkMode, setIsDarkMode] = useState(systemColorScheme === 'dark');

  useEffect(() => {
    loadThemePreference();
  }, []);

  useEffect(() => {
    if (theme === 'auto') {
      setIsDarkMode(systemColorScheme === 'dark');
    } else {
      setIsDarkMode(theme === 'dark');
    }
  }, [theme, systemColorScheme]);

  const loadThemePreference = async () => {
    try {
      const savedTheme = await AsyncStorage.getItem(THEME_KEY);
      if (savedTheme && ['light', 'dark', 'auto'].includes(savedTheme)) {
        setTheme(savedTheme as 'light' | 'dark' | 'auto');
      }
    } catch (error) {
      console.error('Failed to load theme preference:', error);
    }
  };

  const setThemeMode = async (mode: 'light' | 'dark' | 'auto') => {
    try {
      setTheme(mode);
      await AsyncStorage.setItem(THEME_KEY, mode);
    } catch (error) {
      console.error('Failed to save theme preference:', error);
    }
  };

  const toggleTheme = () => {
    if (theme === 'auto') {
      setThemeMode(isDarkMode ? 'light' : 'dark');
    } else {
      setThemeMode(theme === 'light' ? 'dark' : 'light');
    }
  };

  const value: ThemeContextType = {
    isDarkMode,
    toggleTheme,
    theme,
    setThemeMode,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
};