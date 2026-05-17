import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { borderRadius, spacing } from '../styles/theme';
import { useTheme } from '../styles/ThemeContext';

interface TagProps {
  label: string;
  selected: boolean;
  onPress: () => void;
}

export function Tag({ label, selected, onPress }: TagProps) {
  const { colors } = useTheme();

  return (
    <TouchableOpacity
      style={[
        styles.tag, 
        { backgroundColor: colors.surface, borderColor: colors.textMuted + '50' }, // 50 opacity hex
        selected && { backgroundColor: colors.primary + '30', borderColor: colors.primary }
      ]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={[
        styles.text, 
        { color: colors.textMuted },
        selected && { color: colors.primaryGlow, fontWeight: 'bold' }
      ]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  tag: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: borderRadius.full,
    borderWidth: 1,
    margin: 4,
  },
  text: {
    fontSize: 14,
    fontWeight: '500',
  }
});
