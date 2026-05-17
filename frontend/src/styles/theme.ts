export type ColorPalette = {
  background: string;
  surface: string;
  primary: string;
  primaryGlow: string;
  accent: string;
  text: string;
  textMuted: string;
  danger: string;
};

export const darkTheme: ColorPalette = {
  background: '#0F172A',
  surface: '#1E293B',
  primary: '#3B82F6',
  primaryGlow: '#60A5FA',
  accent: '#10B981',
  text: '#F8FAFC',
  textMuted: '#94A3B8',
  danger: '#EF4444',
};

export const pinkTheme: ColorPalette = {
  background: '#fdf4ff', // Fuchsia 50
  surface: '#fae8ff',    // Fuchsia 100
  primary: '#d946ef',    // Fuchsia 500
  primaryGlow: '#e879f9',// Fuchsia 400
  accent: '#a21caf',     // Fuchsia 700
  text: '#4a044e',       // Fuchsia 900
  textMuted: '#86198f',  // Fuchsia 800
  danger: '#e11d48',     // Rose 600
};

export const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 20,
  full: 9999,
};
