import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal, ActivityIndicator, Alert } from 'react-native';
import { spacing, borderRadius } from '../styles/theme';
import { useTheme } from '../styles/ThemeContext';
import { Button } from '../components/Button';
import { restructureWorkout, bulkSwapExercises } from '../api/client';

interface WorkoutScreenProps {
  planData: any;
  planId: string;
  userId: string;
  onPlanUpdated: (newData: any) => void;
  onReset: () => void;
}

export function WorkoutScreen({ planData, planId, userId, onPlanUpdated, onReset }: WorkoutScreenProps) {
  const { colors } = useTheme();
  const [activeDay, setActiveDay] = useState<string | null>(null);
  
  // Modal State (Change Split)
  const [isModalVisible, setModalVisible] = useState(false);
  const [isRestructuring, setIsRestructuring] = useState(false);
  const splits = ["Full Body", "Push, Pull, Legs", "Upper / Lower", "Body Part Split"];

  // Edit Mode State (Modify Exercises)
  const [isEditMode, setIsEditMode] = useState(false);
  const [selectedExercises, setSelectedExercises] = useState<Record<string, string[]>>({}); // { "Day 1": ["Bench Press", "Squat"] }
  const [isSwapping, setIsSwapping] = useState(false);

  // Safely extract the week data
  const planName = planData?.plan_name || "Custom Workout Plan";
  const weekData = planData?.["Week 1"] || {};
  const days = Object.keys(weekData).filter(day => {
    const d = weekData[day];
    return d !== "Rest" && typeof d === 'object' && d?.exercises;
  });

  // Set initial active day to the first day with exercises if possible
  React.useEffect(() => {
    if (days.length > 0 && !activeDay) {
      setActiveDay(days[0]);
    }
  }, [days]);

  const currentDayData = activeDay ? weekData[activeDay] : null;

  // Count total selected exercises
  const totalSelected = Object.values(selectedExercises).reduce((sum, arr) => sum + arr.length, 0);

  // Check if a specific exercise is selected
  const isExerciseSelected = (dayName: string, exName: string): boolean => {
    return (selectedExercises[dayName] || []).includes(exName);
  };

  // Check if a day has any selected exercises
  const dayHasSelections = (dayName: string): boolean => {
    return (selectedExercises[dayName] || []).length > 0;
  };

  // Toggle exercise selection
  const toggleExercise = (dayName: string, exName: string) => {
    if (!isEditMode) return;
    setSelectedExercises(prev => {
      const dayList = prev[dayName] || [];
      if (dayList.includes(exName)) {
        // Deselect
        const newList = dayList.filter(n => n !== exName);
        const newState = { ...prev, [dayName]: newList };
        if (newList.length === 0) delete newState[dayName];
        return newState;
      } else {
        // Select
        return { ...prev, [dayName]: [...dayList, exName] };
      }
    });
  };

  // Enter / Exit edit mode
  const handleToggleEditMode = () => {
    if (isEditMode) {
      // Exiting edit mode — clear selections
      setSelectedExercises({});
    }
    setIsEditMode(!isEditMode);
  };

  // Handle bulk swap
  const handleBulkSwap = async () => {
    // Build the payload
    const exerciseList: { day_name: string; exercise_name: string }[] = [];
    for (const [dayName, names] of Object.entries(selectedExercises)) {
      for (const name of names) {
        exerciseList.push({ day_name: dayName, exercise_name: name });
      }
    }
    
    if (exerciseList.length === 0) return;

    setIsSwapping(true);
    try {
      const response = await bulkSwapExercises(planId, {
        user_id: userId,
        exercises: exerciseList
      });

      if (response.status === 'no_changes') {
        Alert.alert("No Changes", response.message || "Could not find alternatives.");
      } else {
        onPlanUpdated(response.workout_plan);
        
        // Show failures if any
        if (response.failures && response.failures.length > 0) {
          const failNames = response.failures.map((f: any) => f.exercise_name).join(', ');
          Alert.alert(
            "Partial Success",
            `Some exercises could not be replaced: ${failNames}`
          );
        }
      }

      // Exit edit mode
      setSelectedExercises({});
      setIsEditMode(false);
    } catch (error: any) {
      Alert.alert("Swap Failed", error.message);
    } finally {
      setIsSwapping(false);
    }
  };

  const handleRestructure = async (splitName: string) => {
    setIsRestructuring(true);
    try {
      const response = await restructureWorkout(planId, {
        user_id: userId,
        new_split_name: splitName
      });
      onPlanUpdated(response.workout_plan);
      setModalVisible(false);
      const newDays = Object.keys(response.workout_plan["Week 1"] || {});
      if (newDays.length > 0) setActiveDay(newDays[0]);
    } catch (error: any) {
      Alert.alert("Restructure Failed", error.message);
    } finally {
      setIsRestructuring(false);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>{planName}</Text>
        <View style={styles.headerButtons}>
            <TouchableOpacity 
              style={[
                styles.headerBtn, 
                { borderColor: isEditMode ? colors.accent : colors.primary },
                isEditMode && { backgroundColor: colors.accent + '20' }
              ]} 
              onPress={handleToggleEditMode}
            >
              <Text style={[styles.headerBtnText, { color: isEditMode ? colors.accent : colors.primary }]}>
                {isEditMode ? "Cancel" : "Modify\nExercises"}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.headerBtn, { borderColor: colors.primary }, isEditMode && styles.headerBtnDisabled]} 
              onPress={() => !isEditMode && setModalVisible(true)}
              disabled={isEditMode}
            >
              <Text style={[styles.headerBtnText, { color: isEditMode ? colors.textMuted : colors.primary }]}>{"Change\nSplit"}</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.headerBtn, { borderColor: colors.primary }, isEditMode && styles.headerBtnDisabled]} 
              onPress={() => !isEditMode && onReset()}
              disabled={isEditMode}
            >
              <Text style={[styles.headerBtnText, { color: isEditMode ? colors.textMuted : colors.primary }]}>{"New\nPlan"}</Text>
            </TouchableOpacity>
        </View>
      </View>

      {/* Edit mode banner */}
      {isEditMode && (
        <View style={[styles.editBanner, { backgroundColor: colors.accent + '15' }]}>
          <Text style={[styles.editBannerText, { color: colors.accent }]}>
            ✏️ Tap exercises to select them ({totalSelected} selected)
          </Text>
        </View>
      )}

      {/* Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={[styles.tabContainer, { borderBottomColor: colors.surface }]}>
        {days.map(day => (
          <TouchableOpacity 
            key={day} 
            style={[styles.tab, activeDay === day && { borderBottomColor: colors.primaryGlow }]}
            onPress={() => setActiveDay(day)}
          >
            <View style={styles.tabInner}>
              <Text style={[styles.tabText, { color: colors.textMuted }, activeDay === day && { color: colors.primaryGlow }]}>
                {day}
              </Text>
              {/* Selection indicator dot */}
              {isEditMode && dayHasSelections(day) && (
                <View style={[styles.tabDot, { backgroundColor: colors.accent }]} />
              )}
            </View>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.content}>
        {currentDayData === "Rest" || !currentDayData?.exercises ? (
          <View style={styles.restDay}>
            <Text style={[styles.restText, { color: colors.accent }]}>Rest Day</Text>
            <Text style={[styles.restSubText, { color: colors.textMuted }]}>Take time to recover!</Text>
          </View>
        ) : (
          <View>
            {/* Show the day's overall method if it exists */}
            {currentDayData.method && (
              <View style={[styles.methodBadge, { backgroundColor: colors.primary + '20' }]}>
                <Text style={[styles.methodText, { color: colors.primaryGlow }]}>Focus: {currentDayData.method}</Text>
              </View>
            )}

            {currentDayData.exercises.map((ex: any, idx: number) => {
              const selected = isEditMode && activeDay && isExerciseSelected(activeDay, ex.name);
              return (
                <TouchableOpacity 
                  key={idx} 
                  activeOpacity={isEditMode ? 0.7 : 1}
                  onPress={() => activeDay && toggleExercise(activeDay, ex.name)}
                >
                  <View style={[
                    styles.card, 
                    { backgroundColor: colors.surface, borderColor: colors.textMuted + '50' },
                    selected && { borderColor: colors.accent, borderWidth: 2, backgroundColor: colors.accent + '10' }
                  ]}>
                    <View style={styles.cardHeader}>
                      <Text style={[styles.exName, { color: colors.text }, selected && { color: colors.accent }]}>{ex.name}</Text>
                      {selected && (
                        <View style={[styles.checkBadge, { backgroundColor: colors.accent }]}>
                          <Text style={styles.checkText}>✓</Text>
                        </View>
                      )}
                    </View>
                    
                    <View style={styles.metricsRow}>
                      <View style={[styles.metricBox, { backgroundColor: colors.background }]}>
                        <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Sets</Text>
                        <Text style={[styles.metricValue, { color: colors.text }]}>{ex.sets}</Text>
                      </View>
                      <View style={[styles.metricBox, { backgroundColor: colors.background }]}>
                        <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Reps</Text>
                        <Text style={[styles.metricValue, { color: colors.text }]}>{ex.reps}</Text>
                      </View>
                      <View style={[styles.metricBox, { backgroundColor: colors.background }]}>
                        <Text style={[styles.metricLabel, { color: colors.textMuted }]}>Rest</Text>
                        <Text style={[styles.metricValue, { color: colors.text }]}>{ex.rest}</Text>
                      </View>
                    </View>

                    {/* Display the new creative fields! */}
                    {(ex.method || ex.intensity) && (
                      <View style={styles.advancedRow}>
                        {ex.method && <Text style={[styles.tagText, { color: colors.accent }]}>⚡ {ex.method}</Text>}
                        {ex.intensity && <Text style={[styles.tagText, { color: colors.accent }]}>🔥 {ex.intensity}</Text>}
                      </View>
                    )}

                    {ex.notes && <Text style={[styles.notes, { color: colors.textMuted }]}>{ex.notes}</Text>}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>
        )}
        {/* Bottom spacer so FAB doesn't cover last exercise */}
        {isEditMode && <View style={{ height: 80 }} />}
      </ScrollView>

      {/* Floating Action Button for Bulk Swap */}
      {isEditMode && totalSelected > 0 && (
        <TouchableOpacity
          style={[styles.fab, { backgroundColor: colors.accent }]}
          onPress={handleBulkSwap}
          disabled={isSwapping}
          activeOpacity={0.8}
        >
          {isSwapping ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.fabText}>Replace {totalSelected} ✦</Text>
          )}
        </TouchableOpacity>
      )}

      {/* Restructure Modal */}
      <Modal visible={isModalVisible} animationType="slide" transparent={true}>
        <View style={styles.modalOverlay}>
          <View style={[styles.modalContent, { backgroundColor: colors.surface }]}>
            <Text style={[styles.modalTitle, { color: colors.text }]}>Change Workout Split</Text>
            <Text style={[styles.modalSub, { color: colors.textMuted }]}>
              Keep your exercises, but change how they are structured throughout the week.
            </Text>

            {isRestructuring ? (
              <View style={{ padding: 40, alignItems: 'center' }}>
                <ActivityIndicator size="large" color={colors.primaryGlow} />
                <Text style={{ marginTop: 10, color: colors.text }}>Re-building your plan...</Text>
              </View>
            ) : (
              <View style={styles.splitList}>
                {splits.map(split => (
                  <TouchableOpacity
                    key={split}
                    style={[styles.splitButton, { backgroundColor: colors.background, borderColor: colors.primary }]}
                    onPress={() => handleRestructure(split)}
                  >
                    <Text style={[styles.splitText, { color: colors.text }]}>{split}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            <TouchableOpacity 
              style={{ marginTop: 20, alignItems: 'center' }} 
              onPress={() => setModalVisible(false)}
              disabled={isRestructuring}
            >
              <Text style={{ color: colors.accent, fontWeight: 'bold' }}>Cancel</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  splitList: {
    gap: spacing.sm,
  },
  splitButton: {
    padding: spacing.lg,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    alignItems: 'center',
  },
  splitText: {
    fontWeight: 'bold',
    fontSize: 16,
  },
  header: {
    paddingTop: spacing.xxl,
    paddingHorizontal: spacing.sm,
    paddingBottom: spacing.sm,
  },
  headerButtons: {
    flexDirection: 'row',
    marginTop: spacing.sm,
  },
  headerBtn: {
    flex: 1,
    borderWidth: 1,
    borderRadius: borderRadius.md,
    paddingVertical: 6,
    paddingHorizontal: 2,
    marginHorizontal: 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerBtnDisabled: {
    opacity: 0.4,
  },
  headerBtnText: {
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  editBanner: {
    paddingVertical: 6,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
  },
  editBannerText: {
    fontSize: 13,
    fontWeight: '600',
  },
  title: {
    fontSize: 22,
    fontWeight: 'bold',
    paddingHorizontal: spacing.xs,
  },
  tabContainer: {
    borderBottomWidth: 1,
    flexGrow: 0,
  },
  tab: {
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.sm,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabInner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tabDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  tabText: {
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: spacing.md,
  },
  restDay: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.xxl,
  },
  restText: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  restSubText: {
    marginTop: spacing.sm,
  },
  methodBadge: {
    padding: spacing.sm,
    borderRadius: borderRadius.md,
    marginBottom: spacing.md,
    alignSelf: 'flex-start',
  },
  methodText: {
    fontWeight: 'bold',
  },
  card: {
    padding: spacing.lg,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    borderWidth: 1,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  exName: {
    fontSize: 18,
    fontWeight: 'bold',
    flex: 1,
  },
  checkBadge: {
    width: 26,
    height: 26,
    borderRadius: 13,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 8,
  },
  checkText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: 'bold',
  },
  metricsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  metricBox: {
    flex: 1,
    padding: spacing.sm,
    borderRadius: borderRadius.sm,
    marginRight: spacing.xs,
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 2,
  },
  advancedRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  tagText: {
    fontSize: 13,
    fontWeight: 'bold',
  },
  notes: {
    fontSize: 14,
    fontStyle: 'italic',
    marginTop: spacing.sm,
  },
  fab: {
    position: 'absolute',
    bottom: 30,
    right: 20,
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 30,
    elevation: 6,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
  },
  fabText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
