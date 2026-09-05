import * as SecureStore from 'expo-secure-store';

// The API host is no longer hardcoded. Set EXPO_PUBLIC_API_URL in frontend/.env
// (Expo inlines any EXPO_PUBLIC_* variable at build time) and neither the LAN IP
// nor the tunnel URL needs a code change again.
//
//   frontend/.env
//   EXPO_PUBLIC_API_URL=http://192.168.1.42:8000
//
// Without it we fall back to the previous behaviour: LAN IP in dev, tunnel in a build.
const FALLBACK_DEV_URL = 'http://10.107.17.6:8000';
const FALLBACK_PROD_URL = 'https://lazytrainer-api.loca.lt';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL || (__DEV__ ? FALLBACK_DEV_URL : FALLBACK_PROD_URL);

// AuthContext registers a callback here so an expired token logs the user out
// instead of surfacing a confusing "401" alert on every screen.
let onUnauthorized: (() => void) | null = null;
export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler;
}

const BASE_HEADERS: Record<string, string> = {
  'Content-Type': 'application/json',
  'Bypass-Tunnel-Reminder': 'true', // Bypasses localtunnel's security screen
};

/** Pull a readable message out of FastAPI's {"detail": ...} error body. */
async function describeError(response: Response): Promise<string> {
  const text = await response.text();
  try {
    const body = JSON.parse(text);
    if (typeof body?.detail === 'string') return body.detail;
    if (Array.isArray(body?.detail)) {
      // Pydantic validation errors
      return body.detail.map((d: any) => `${d.loc?.slice(-1)}: ${d.msg}`).join('\n');
    }
  } catch {
    // not JSON - fall through to the raw text
  }
  return text || `Request failed (${response.status})`;
}

/** Single place where every authenticated call attaches its token and handles failures. */
async function request(path: string, options: RequestInit = {}) {
  const token = await SecureStore.getItemAsync('userToken');
  const headers: Record<string, string> = {
    ...BASE_HEADERS,
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (response.status === 401) {
    onUnauthorized?.();
    throw new Error('Your session expired. Please log in again.');
  }
  if (!response.ok) {
    throw new Error(await describeError(response));
  }

  const data = await response.json();
  // The backend ships the schedule as a JSON string; unwrap it once, here.
  if (typeof data?.workout_plan === 'string') {
    data.workout_plan = JSON.parse(data.workout_plan);
  }
  return data;
}

// --- AUTHENTICATION ---
export async function registerUser(payload: { username: string; password: string }) {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: BASE_HEADERS,
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(await describeError(response));
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
      'Bypass-Tunnel-Reminder': 'true',
    },
    body: formData.toString(),
  });
  if (!response.ok) {
    throw new Error('Invalid username or password');
  }
  return await response.json();
}

// --- PLANS ---
/** Every saved plan for the logged-in user, newest first. */
export async function listPlans(): Promise<
  { plan_id: string; name: string | null; status: string | null; created_at: string | null }[]
> {
  return await request('/plans');
}

/** Reload one saved plan (this is what survives a logout). */
export async function getPlan(planId: string) {
  return await request(`/plans/${planId}`);
}

// --- WORKOUTS ---
export async function generateWorkout(payload: any) {
  return await request('/generate', { method: 'POST', body: JSON.stringify(payload) });
}

export async function restructureWorkout(planId: string, payload: any) {
  return await request(`/plans/${planId}/restructure`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function getEquipmentAlternatives(planId: string, payload: any) {
  return await request(`/plans/${planId}/equipment-alternatives`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function applyEquipmentSwap(planId: string, payload: any) {
  return await request(`/plans/${planId}/apply-equipment-swap`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function smartSwapExercise(planId: string, payload: any) {
  return await request(`/plans/${planId}/smart-swap`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function bulkSwapExercises(planId: string, payload: any) {
  return await request(`/plans/${planId}/bulk-swap`, { method: 'POST', body: JSON.stringify(payload) });
}

export async function generateNextBlock(payload: any) {
  return await request('/generate/next', { method: 'POST', body: JSON.stringify(payload) });
}
