import React from 'react';
import { TouchableOpacity, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { borderRadius, spacing } from '../styles/theme';
import { useTheme } from '../styles/ThemeContext';

interface ButtonProps {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  type?: 'primary' | 'secondary';
  style?: any;
}

export function Button({ title, onPress, loading, disabled, type = 'primary', style }: ButtonProps) {
  const { colors } = useTheme();

  return (
    <TouchableOpacity
      style={[
        styles.button,
        { backgroundColor: colors.primary, shadowColor: colors.primaryGlow },
        type === 'secondary' && { ...styles.secondaryButton, borderColor: colors.primary },
        (disabled || loading) && styles.disabled,
        style
      ]}
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.8}
    >
      {loading ? (
        <ActivityIndicator color={colors.text} />
      ) : (
        <Text 
          numberOfLines={2}
          adjustsFontSizeToFit={true}
          style={[styles.text, { color: colors.text }, type === 'secondary' && { color: colors.primary }]}
        >
          {title}
        </Text>
      )}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  button: {
    paddingVertical: spacing.md,
    paddingHorizontal: spacing.xl,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
    justifyContent: 'center',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  secondaryButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    shadowOpacity: 0,
    elevation: 0,
  },
  disabled: {
    opacity: 0.6,
  },
  text: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  }
});
