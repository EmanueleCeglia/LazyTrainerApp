import React, { useState, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Modal, ActivityIndicator, Alert, Animated, PanResponder, GestureResponderEvent, PanResponderGestureState } from 'react-native';
import { spacing, borderRadius } from '../styles/theme';
import { useTheme } from '../styles/ThemeContext';
import { Button } from '../components/Button';
import { restructureWorkout, getEquipmentAlternatives, smartSwapExercise, applyEquipmentSwap } from '../api/client';

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
  
  // Restructure Modal
  const [isModalVisible, setModalVisible] = useState(false);
  const [isRestructuring, setIsRestructuring] = useState(false);
  const splits = ["Full Body", "Push, Pull, Legs", "Upper / Lower", "Body Part Split"];

  // Long-press state: which exercise is "active" for modification
  const [activeExercise, setActiveExercise] = useState<string | null>(null);
  const longPressTimer = useRef<any>(null);

  // Mode 1: Swipe state
  const [swipeAlternatives, setSwipeAlternatives] = useState<any[]>([]);
  const [swipeIndex, setSwipeIndex] = useState(0);
  const [isLoadingAlternatives, setIsLoadingAlternatives] = useState(false);
  const swipeX = useRef(new Animated.Value(0)).current;

  // Mode 2: Smart swap
  const [showMode2Menu, setShowMode2Menu] = useState(false);
  const [isSmartSwapping, setIsSmartSwapping] = useState(false);

  // Plan data
  const planName = planData?.plan_name || "Custom Workout Plan";
  const weekData = planData?.["Week 1"] || {};
  const days = Object.keys(weekData).filter(day => {
    const d = weekData[day];
    return d !== "Rest" && typeof d === 'object' && d?.exercises;
  });

  React.useEffect(() => {
    if (days.length > 0 && !activeDay) {
      setActiveDay(days[0]);
    }
  }, [days]);

  const currentDayData = activeDay ? weekData[activeDay] : null;

  // --- Long Press Handling ---
  const handlePressIn = (exName: string) => {
    longPressTimer.current = setTimeout(async () => {
      setActiveExercise(exName);
      // Load Mode 1 alternatives
      setIsLoadingAlternatives(true);
      try {
        const res = await getEquipmentAlternatives(planId, {
          user_id: userId,
          day_name: activeDay,
          exercise_name: exName
        });
        setSwipeAlternatives(res.alternatives || []);
        setSwipeIndex(0);
      } catch (e: any) {
        setSwipeAlternatives([]);
      } finally {
        setIsLoadingAlternatives(false);
      }
    }, 1500); // 1.5 second long press
  };

  const handlePressOut = () => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current);
      longPressTimer.current = null;
    }
  };

  // --- Cancel active exercise ---
  const cancelEdit = () => {
    setActiveExercise(null);
    setSwipeAlternatives([]);
    setSwipeIndex(0);
    setShowMode2Menu(false);
    swipeX.setValue(0);
  };

  // --- Mode 1: Swipe to next alternative ---
  const handleSwipeLeft = () => {
    if (swipeAlternatives.length === 0) return;
    const newIdx = (swipeIndex + 1) % swipeAlternatives.length;
    Animated.timing(swipeX, { toValue: -300, duration: 150, useNativeDriver: true }).start(() => {
      setSwipeIndex(newIdx);
      swipeX.setValue(300);
      Animated.timing(swipeX, { toValue: 0, duration: 150, useNativeDriver: true }).start();
    });
  };

  const handleSwipeRight = () => {
    if (swipeAlternatives.length === 0) return;
    const newIdx = swipeIndex === 0 ? swipeAlternatives.length - 1 : swipeIndex - 1;
    Animated.timing(swipeX, { toValue: 300, duration: 150, useNativeDriver: true }).start(() => {
      setSwipeIndex(newIdx);
      swipeX.setValue(-300);
      Animated.timing(swipeX, { toValue: 0, duration: 150, useNativeDriver: true }).start();
    });
  };

  // --- Mode 1: Confirm swap ---
  const confirmMode1Swap = async () => {
    if (!activeExercise || !activeDay || swipeAlternatives.length === 0) return;
    
    const chosen = swipeAlternatives[swipeIndex];
    
    try {
      const res = await applyEquipmentSwap(planId, {
        user_id: userId,
        day_name: activeDay,
        exercise_name: activeExercise,
        new_exercise_name: chosen.name
      });
      onPlanUpdated(res.workout_plan);
      Alert.alert("✓ Swapped!", `${activeExercise} → ${chosen.name}`);
    } catch (e: any) {
      Alert.alert("Swap Failed", e.message);
    } finally {
      cancelEdit();
    }
  };

  // --- Mode 2: Smart AI swap ---
  const handleSmartSwap = async (targetZone: string) => {
    if (!activeExercise || !activeDay) return;
    
    setShowMode2Menu(false);
    setIsSmartSwapping(true);
    
    try {
      const res = await smartSwapExercise(planId, {
        user_id: userId,
        day_name: activeDay,
        exercise_name: activeExercise,
        target_zone: targetZone
      });
      
      if (res.status === 'no_alternatives') {
        Alert.alert("No Alternatives", res.message);
      } else {
        onPlanUpdated(res.workout_plan);
        const replacement = res.replacement;
        Alert.alert(
          "✓ Smart Swap!",
          `${activeExercise} → ${replacement?.name || 'New exercise'}\n${replacement?.reason || ''}`
        );
      }
    } catch (e: any) {
      Alert.alert("Swap Failed", e.message);
    } finally {
      setIsSmartSwapping(false);
      cancelEdit();
    }
  };

  // --- Restructure ---
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

  // --- Pan Responder for swipe gestures ---
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt: GestureResponderEvent, gestureState: PanResponderGestureState) => {
        return Math.abs(gestureState.dx) > 20 && Math.abs(gestureState.dy) < 40;
      },
      onPanResponderRelease: (evt: GestureResponderEvent, gestureState: PanResponderGestureState) => {
        if (gestureState.dx < -50) {
          handleSwipeLeft();
        } else if (gestureState.dx > 50) {
          handleSwipeRight();
        }
      },
    })
  ).current;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>{planName}</Text>
        <View style={styles.headerButtons}>
            <TouchableOpacity 
              style={[styles.headerBtn, { borderColor: colors.primary }]} 
              onPress={() => setModalVisible(true)}
            >
              <Text style={[styles.headerBtnText, { color: colors.primary }]}>{"Change\nSplit"}</Text>
            </TouchableOpacity>
            <TouchableOpacity 
              style={[styles.headerBtn, { borderColor: colors.primary }]} 
              onPress={onReset}
            >
              <Text style={[styles.headerBtnText, { color: colors.primary }]}>{"New\nPlan"}</Text>
            </TouchableOpacity>
        </View>
      </View>

      {/* Hint banner */}
      <View style={[styles.hintBanner, { backgroundColor: colors.surface }]}>
        <Text style={[styles.hintText, { color: colors.textMuted }]}>
          💡 Long-press on any exercise to modify it
        </Text>
      </View>

      {/* Tabs */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={[styles.tabContainer, { borderBottomColor: colors.surface }]}>
        {days.map(day => (
          <TouchableOpacity 
            key={day} 
            style={[styles.tab, activeDay === day && { borderBottomColor: colors.primaryGlow }]}
            onPress={() => setActiveDay(day)}
          >
            <Text style={[styles.tabText, { color: colors.textMuted }, activeDay === day && { color: colors.primaryGlow }]}>
              {day}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* Content */}
      <ScrollView style={styles.content}>
        {currentDayData === "Rest" || !currentDayData?.exercises ? (
          <View style={styles.restDay}>
            <Text style={[styles.restText, { color: colors.accent }]}>Rest Day</Text>
          </View>
        ) : (
          <View>
            {currentDayData.method && (
              <View style={[styles.methodBadge, { backgroundColor: colors.primary + '20' }]}>
                <Text style={[styles.methodText, { color: colors.primaryGlow }]}>Focus: {currentDayData.method}</Text>
              </View>
            )}

            {currentDayData.exercises.map((ex: any, idx: number) => {
              const isActive = activeExercise === ex.name;

              return (
                <View key={idx}>
                  <TouchableOpacity
                    activeOpacity={0.7}
                    onPressIn={() => handlePressIn(ex.name)}
                    onPressOut={handlePressOut}
                    onPress={() => {
                      // Regular tap does nothing special
                    }}
                  >
                    <View style={[
                      styles.card, 
                      { backgroundColor: colors.surface, borderColor: colors.textMuted + '50' },
                      isActive && { borderColor: colors.accent, borderWidth: 2, backgroundColor: colors.accent + '10' }
                    ]}>
                      <View style={styles.cardHeader}>
                        <Text style={[styles.exName, { color: colors.text }, isActive && { color: colors.accent }]}>
                          {ex.name}
                        </Text>
                        {isActive && (
                          <TouchableOpacity onPress={cancelEdit}>
                            <Text style={{ color: colors.accent, fontWeight: 'bold', fontSize: 14 }}>✕</Text>
                          </TouchableOpacity>
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

                      {(ex.method || ex.intensity) && (
                        <View style={styles.advancedRow}>
                          {ex.method && <Text style={[styles.tagText, { color: colors.accent }]}>⚡ {ex.method}</Text>}
                          {ex.intensity && <Text style={[styles.tagText, { color: colors.accent }]}>🔥 {ex.intensity}</Text>}
                        </View>
                      )}

                      {ex.notes && <Text style={[styles.notes, { color: colors.textMuted }]}>{ex.notes}</Text>}
                    </View>
                  </TouchableOpacity>

                  {/* Mode 1: Swipe panel (appears below the active exercise card) */}
                  {isActive && !showMode2Menu && (
                    <View style={[styles.swipePanel, { backgroundColor: colors.surface, borderColor: colors.accent }]}>
                      {isLoadingAlternatives ? (
                        <View style={{ padding: 20, alignItems: 'center' }}>
                          <ActivityIndicator color={colors.accent} />
                          <Text style={{ color: colors.textMuted, marginTop: 8 }}>Loading alternatives...</Text>
                        </View>
                      ) : swipeAlternatives.length > 0 ? (
                        <View>
                          <Text style={[styles.swipeTitle, { color: colors.accent }]}>🔄 Same muscle, different equipment</Text>
                          <View style={styles.browseRow}>
                            <TouchableOpacity 
                              style={[styles.arrowBtn, { backgroundColor: colors.background, borderColor: colors.accent + '40' }]} 
                              onPress={handleSwipeRight}
                            >
                              <Text style={[styles.arrowText, { color: colors.accent }]}>◀</Text>
                            </TouchableOpacity>
                            <View style={[styles.altCard, { backgroundColor: colors.background, borderColor: colors.accent + '40', flex: 1 }]}>
                              <Text style={[styles.altName, { color: colors.text }]}>
                                {swipeAlternatives[swipeIndex]?.name}
                              </Text>
                              <Text style={[styles.altEquip, { color: colors.textMuted }]}>
                                {swipeAlternatives[swipeIndex]?.equipment?.join(' + ') || 'Bodyweight'}
                              </Text>
                              <Text style={[styles.altCounter, { color: colors.textMuted }]}>
                                {swipeIndex + 1} / {swipeAlternatives.length}
                              </Text>
                            </View>
                            <TouchableOpacity 
                              style={[styles.arrowBtn, { backgroundColor: colors.background, borderColor: colors.accent + '40' }]} 
                              onPress={handleSwipeLeft}
                            >
                              <Text style={[styles.arrowText, { color: colors.accent }]}>▶</Text>
                            </TouchableOpacity>
                          </View>
                          <View style={styles.swipeBtnRow}>
                            <TouchableOpacity style={[styles.swipeActionBtn, { backgroundColor: colors.accent }]} onPress={confirmMode1Swap}>
                              <Text style={styles.swipeActionBtnText}>✓ Confirm</Text>
                            </TouchableOpacity>
                            <TouchableOpacity 
                              style={[styles.swipeActionBtn, { backgroundColor: colors.primary }]} 
                              onPress={() => setShowMode2Menu(true)}
                            >
                              <Text style={styles.swipeActionBtnText}>🔀 Different</Text>
                            </TouchableOpacity>
                          </View>
                        </View>
                      ) : (
                        <View style={{ padding: 16 }}>
                          <Text style={{ color: colors.textMuted, textAlign: 'center' }}>No same-muscle alternatives found.</Text>
                          <TouchableOpacity 
                            style={[styles.swipeActionBtn, { backgroundColor: colors.primary, marginTop: 12, alignSelf: 'center' }]} 
                            onPress={() => setShowMode2Menu(true)}
                          >
                            <Text style={styles.swipeActionBtnText}>🔀 Different Exercise</Text>
                          </TouchableOpacity>
                        </View>
                      )}
                    </View>
                  )}

                  {/* Mode 2: Target zone selection menu */}
                  {isActive && showMode2Menu && (
                    <View style={[styles.mode2Panel, { backgroundColor: colors.surface, borderColor: colors.primary }]}>
                      <Text style={[styles.swipeTitle, { color: colors.primary }]}>🔀 Choose target zone</Text>
                      {isSmartSwapping ? (
                        <View style={{ padding: 20, alignItems: 'center' }}>
                          <ActivityIndicator color={colors.primary} />
                          <Text style={{ color: colors.textMuted, marginTop: 8 }}>AI is finding the best replacement...</Text>
                        </View>
                      ) : (
                        <View style={styles.zoneRow}>
                          {["Upper", "Lower", "Core"].map(zone => (
                            <TouchableOpacity
                              key={zone}
                              style={[styles.zoneBtn, { borderColor: colors.primary, backgroundColor: colors.background }]}
                              onPress={() => handleSmartSwap(zone)}
                            >
                              <Text style={[styles.zoneBtnText, { color: colors.primary }]}>
                                {zone === 'Upper' ? '💪' : zone === 'Lower' ? '🦵' : '🏋️'} {zone}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      )}
                      {!isSmartSwapping && (
                        <TouchableOpacity onPress={() => setShowMode2Menu(false)} style={{ marginTop: 8, alignItems: 'center' }}>
                          <Text style={{ color: colors.textMuted }}>← Back to swipe</Text>
                        </TouchableOpacity>
                      )}
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        )}
      </ScrollView>

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
  headerBtnText: {
    fontSize: 12,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  hintBanner: {
    paddingVertical: 6,
    paddingHorizontal: spacing.md,
    alignItems: 'center',
  },
  hintText: {
    fontSize: 12,
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
    marginBottom: spacing.sm,
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
  // --- Swipe Panel (Mode 1) ---
  swipePanel: {
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    marginTop: -4,
    padding: spacing.md,
  },
  swipeTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  altCard: {
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    alignItems: 'center',
    minHeight: 70,
    justifyContent: 'center',
  },
  altName: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  altEquip: {
    fontSize: 12,
    marginTop: 4,
  },
  altCounter: {
    fontSize: 11,
    marginTop: 6,
  },
  swipeBtnRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: spacing.sm,
  },
  swipeActionBtn: {
    flex: 1,
    padding: 10,
    borderRadius: borderRadius.md,
    alignItems: 'center',
  },
  swipeActionBtnText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 14,
  },
  browseRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  arrowBtn: {
    width: 40,
    height: 70,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrowText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  // --- Mode 2 Panel ---
  mode2Panel: {
    borderWidth: 1,
    borderRadius: borderRadius.lg,
    marginBottom: spacing.md,
    marginTop: -4,
    padding: spacing.md,
  },
  zoneRow: {
    flexDirection: 'row',
    gap: 8,
  },
  zoneBtn: {
    flex: 1,
    padding: spacing.md,
    borderRadius: borderRadius.md,
    borderWidth: 1,
    alignItems: 'center',
  },
  zoneBtnText: {
    fontWeight: 'bold',
    fontSize: 14,
  },
  // --- Modal ---
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
});
