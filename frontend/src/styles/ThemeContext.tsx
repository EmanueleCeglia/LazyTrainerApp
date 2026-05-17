import React, { createContext, useContext, useState } from 'react';
import { ColorPalette, darkTheme, pinkTheme } from './theme';

type ThemeType = 'dark' | 'pink';

interface ThemeContextData {
  themeName: ThemeType;
  colors: ColorPalette;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextData | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [themeName, setThemeName] = useState<ThemeType>('dark');

  const toggleTheme = () => {
    setThemeName(prev => (prev === 'dark' ? 'pink' : 'dark'));
  };

  const colors = themeName === 'dark' ? darkTheme : pinkTheme;

  return (
    <ThemeContext.Provider value={{ themeName, colors, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
