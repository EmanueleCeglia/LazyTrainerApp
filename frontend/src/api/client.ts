import * as SecureStore from 'expo-secure-store';

// Automatically switch URLs: 
// - If testing in Expo Go (Development mode), use your local IP.
// - If building an APK (Production mode), use the Localtunnel URL.
export const API_BASE_URL = __DEV__ 
  ? 'http://10.107.17.6:8000' 
  : 'https://lazytrainer-api.loca.lt';

// Helper to automatically attach JWT token
async function authFetch(url: string, options: any = {}) {
  const token = await SecureStore.getItemAsync('userToken');
  const headers = {
    'Content-Type': 'application/json',
    'Bypass-Tunnel-Reminder': 'true', // Bypasses localtunnel's security screen
    ...options.headers,
  };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return fetch(url, { ...options, headers });
}

// --- AUTHENTICATION ---
export async function registerUser(payload: any) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Bypass-Tunnel-Reminder': 'true'
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Registration Failed: ${errorText}`);
  }
  return await response.json();
}

export async function loginUser(username: string, password: string) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);

  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/x-www-form-urlencoded',
      'Bypass-Tunnel-Reminder': 'true'
    },
    body: formData.toString(),
  });
  if (!response.ok) {
    throw new Error("Invalid username or password");
  }
  return await response.json();
}

// --- WORKOUTS ---
export async function generateWorkout(payload: any) {
  const response = await authFetch(`${API_BASE_URL}/generate`, {
    method: 'POST',
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

export async function restructureWorkout(planId: string, payload: any) {
  const response = await authFetch(`${API_BASE_URL}/plans/${planId}/restructure`, {
    method: 'POST',
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

export async function getEquipmentAlternatives(planId: string, payload: any) {
  const response = await authFetch(`${API_BASE_URL}/plans/${planId}/equipment-alternatives`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }
  return await response.json();
}

export async function applyEquipmentSwap(planId: string, payload: any) {
  const response = await authFetch(`${API_BASE_URL}/plans/${planId}/apply-equipment-swap`, {
    method: 'POST',
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

export async function smartSwapExercise(planId: string, payload: any) {
  const response = await authFetch(`${API_BASE_URL}/plans/${planId}/smart-swap`, {
    method: 'POST',
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
