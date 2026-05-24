// Use the exact IP address of your computer so physical phones and emulators can both connect
export const API_BASE_URL = 'http://10.107.17.6:8000';

export async function generateWorkout(payload: any) {
  const response = await fetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  
  // The backend returns a JSON string in workout_plan
  if (typeof data.workout_plan === 'string') {
    data.workout_plan = JSON.parse(data.workout_plan);
  }
  
  return data;
}

export async function restructureWorkout(planId: string, payload: any) {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/restructure`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  if (typeof data.workout_plan === 'string') {
    data.workout_plan = JSON.parse(data.workout_plan);
  }
  return data;
}

// Mode 1: Get equipment alternatives (deterministic, instant)
export async function getEquipmentAlternatives(planId: string, payload: any) {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/equipment-alternatives`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }

  return await response.json();
}

// Mode 1: Apply equipment swap to DB
export async function applyEquipmentSwap(planId: string, payload: any) {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/apply-equipment-swap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  if (typeof data.workout_plan === 'string') {
    data.workout_plan = JSON.parse(data.workout_plan);
  }
  return data;
}

// Mode 2: Smart AI swap
export async function smartSwapExercise(planId: string, payload: any) {
  const response = await fetch(`${API_BASE_URL}/plans/${planId}/smart-swap`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }

  const data = await response.json();
  if (typeof data.workout_plan === 'string') {
    data.workout_plan = JSON.parse(data.workout_plan);
  }
  return data;
}
