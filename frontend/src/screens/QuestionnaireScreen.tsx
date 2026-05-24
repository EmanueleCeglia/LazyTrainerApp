import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TextInput, KeyboardAvoidingView, Platform, Alert, Modal, TouchableOpacity } from 'react-native';
import { spacing, borderRadius } from '../styles/theme';
import { useTheme } from '../styles/ThemeContext';
import { Button } from '../components/Button';
import { Tag } from '../components/Tag';

const GENDERS = ["Male", "Female", "Other"];
const EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"];
const LOCATIONS = ["Gym", "Home", "Park"];
const GOALS = ["Muscle Growth", "Pure Strength", "Muscle Endurance"];
const EXTRA_EQUIPMENT = [
  "Dumbbells", "Barbell", "Kettlebell", "Bench",
  "Squat Rack", "Smith Machine", "Pull-up Bar",
  "Parallel Bars", "Low Bar", "Rings", "Resistance Bands"
];

interface QuestionnaireScreenProps {
  onComplete: (payload: any) => void;
  isLoading: boolean;
}

export function QuestionnaireScreen({ onComplete, isLoading }: QuestionnaireScreenProps) {
  const { colors } = useTheme();
  
  const [age, setAge] = useState('25');
  const [weight, setWeight] = useState('75');
  const [height, setHeight] = useState('175');
  const [gender, setGender] = useState('Male');
  const [experience, setExperience] = useState('Beginner');
  const [days, setDays] = useState('4');
  const [duration, setDuration] = useState('60');
  const [location, setLocation] = useState('Gym');
  const [equipment, setEquipment] = useState<string[]>([]);
  const [goals, setGoals] = useState<string[]>(['Muscle Growth']);
  const [equipmentModalVisible, setEquipmentModalVisible] = useState(false);

  const showEquipmentOption = location === 'Home' || location === 'Park';

  const toggleSelection = (item: string, list: string[], setList: (l: string[]) => void) => {
    if (list.includes(item)) {
      setList(list.filter(i => i !== item));
    } else {
      setList([...list, item]);
    }
  };

  // Reset equipment when switching to Gym
  const handleLocationChange = (loc: string) => {
    setLocation(loc);
    if (loc === 'Gym') {
      setEquipment([]);
    }
  };

  const handleSubmit = () => {
    if (!age || !weight || !height || !days || !duration || goals.length === 0) {
      Alert.alert("Missing Fields", "Please fill out all fields and select at least one goal.");
      return;
    }

    const payload = {
      user_id: "user_" + Math.floor(Math.random() * 10000),
      age: parseInt(age),
      weight: parseFloat(weight),
      height: parseFloat(height),
      gender: gender as any,
      experience_level: experience as any,
      days_per_week: parseInt(days),
      session_duration_minutes: parseInt(duration),
      location: location as any,
      equipment: equipment,
      goals: goals
    };

    onComplete(payload);
  };

  return (
    <KeyboardAvoidingView 
      style={[styles.container, { backgroundColor: colors.background }]}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={[styles.header, { color: colors.text }]}>Build Your Plan</Text>
        <Text style={[styles.subHeader, { color: colors.textMuted }]}>Let the AI tailor the perfect strategy for you.</Text>

        <View style={styles.section}>
          <Text style={[styles.label, { color: colors.text }]}>Biometrics</Text>
          <View style={styles.row}>
            <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} value={age} onChangeText={setAge} placeholder="Age" keyboardType="numeric" placeholderTextColor={colors.textMuted} />
            <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} value={weight} onChangeText={setWeight} placeholder="Weight (kg)" keyboardType="numeric" placeholderTextColor={colors.textMuted} />
            <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} value={height} onChangeText={setHeight} placeholder="Height (cm)" keyboardType="numeric" placeholderTextColor={colors.textMuted} />
          </View>
          <View style={styles.tagContainer}>
            {GENDERS.map(g => (
              <Tag key={g} label={g} selected={gender === g} onPress={() => setGender(g)} />
            ))}
          </View>
          <Text style={[styles.subLabel, { color: colors.textMuted }]}>Experience Level:</Text>
          <View style={styles.tagContainer}>
            {EXPERIENCE_LEVELS.map(lvl => (
              <Tag key={lvl} label={lvl} selected={experience === lvl} onPress={() => setExperience(lvl)} />
            ))}
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.label, { color: colors.text }]}>Logistics</Text>
          <View style={styles.row}>
            <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} value={days} onChangeText={setDays} placeholder="Days/Week" keyboardType="numeric" placeholderTextColor={colors.textMuted} />
            <TextInput style={[styles.input, { backgroundColor: colors.surface, color: colors.text, borderColor: colors.textMuted + '50' }]} value={duration} onChangeText={setDuration} placeholder="Duration (min)" keyboardType="numeric" placeholderTextColor={colors.textMuted} />
          </View>
        </View>

        <View style={styles.section}>
          <Text style={[styles.label, { color: colors.text }]}>Environment</Text>
          <View style={styles.tagContainer}>
            {LOCATIONS.map(loc => (
              <Tag key={loc} label={loc} selected={location === loc} onPress={() => handleLocationChange(loc)} />
            ))}
          </View>

          {/* Dynamic equipment button — only for Park/Home */}
          {showEquipmentOption && (
            <TouchableOpacity
              style={[styles.equipmentBtn, { borderColor: colors.primary, backgroundColor: colors.surface }]}
              onPress={() => setEquipmentModalVisible(true)}
            >
              <Text style={[styles.equipmentBtnText, { color: colors.primary }]}>
                🏗️ Extra Equipment {equipment.length > 0 ? `(${equipment.length} selected)` : ''}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        <View style={styles.section}>
          <Text style={[styles.label, { color: colors.text }]}>Goals</Text>
          <View style={styles.tagContainer}>
            {GOALS.map(goal => (
              <Tag key={goal} label={goal} selected={goals.includes(goal)} onPress={() => toggleSelection(goal, goals, setGoals)} />
            ))}
          </View>
        </View>

        <View style={styles.footer}>
          <Button 
            title="Generate AI Program" 
            onPress={handleSubmit} 
            loading={isLoading} 
          />
        </View>
      </ScrollView>

      {/* Equipment Selection Modal */}
      <Modal visible={equipmentModalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.surface }]}>
            <Text style={[styles.modalTitle, { color: colors.text }]}>Select Extra Equipment</Text>
            <Text style={[styles.modalSub, { color: colors.textMuted }]}>
              What additional equipment do you have at {location.toLowerCase()}?
            </Text>

            <ScrollView style={styles.equipmentList}>
              {EXTRA_EQUIPMENT.map(eq => (
                <TouchableOpacity
                  key={eq}
                  style={[
                    styles.equipmentItem,
                    { borderColor: colors.textMuted + '30' },
                    equipment.includes(eq) && { borderColor: colors.primary, backgroundColor: colors.primary + '15' }
                  ]}
                  onPress={() => toggleSelection(eq, equipment, setEquipment)}
                >
                  <Text style={[
                    styles.equipmentItemText,
                    { color: colors.text },
                    equipment.includes(eq) && { color: colors.primary, fontWeight: 'bold' }
                  ]}>
                    {equipment.includes(eq) ? '✓ ' : ''}{eq}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <TouchableOpacity
              style={[styles.modalDoneBtn, { backgroundColor: colors.primary }]}
              onPress={() => setEquipmentModalVisible(false)}
            >
              <Text style={styles.modalDoneBtnText}>Done</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scroll: {
    padding: spacing.lg,
    paddingTop: spacing.xxl,
  },
  header: {
    fontSize: 32,
    fontWeight: 'bold',
    marginBottom: spacing.xs,
  },
  subHeader: {
    fontSize: 16,
    marginBottom: spacing.xl,
  },
  section: {
    marginBottom: spacing.xl,
  },
  label: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: spacing.sm,
  },
  subLabel: {
    fontSize: 14,
    marginTop: spacing.sm,
    marginBottom: spacing.xs,
  },
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  input: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
  },
  tagContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  footer: {
    marginTop: spacing.xl,
    paddingBottom: spacing.xxl,
  },
  equipmentBtn: {
    marginTop: spacing.md,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    alignItems: 'center',
  },
  equipmentBtnText: {
    fontSize: 15,
    fontWeight: '600',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    padding: spacing.xl,
    borderTopLeftRadius: borderRadius.xl,
    borderTopRightRadius: borderRadius.xl,
    maxHeight: '70%',
  },
  modalTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: spacing.xs,
  },
  modalSub: {
    fontSize: 14,
    marginBottom: spacing.lg,
  },
  equipmentList: {
    marginBottom: spacing.md,
  },
  equipmentItem: {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    marginBottom: spacing.sm,
  },
  equipmentItemText: {
    fontSize: 16,
  },
  modalDoneBtn: {
    padding: spacing.md,
    borderRadius: borderRadius.lg,
    alignItems: 'center',
  },
  modalDoneBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
