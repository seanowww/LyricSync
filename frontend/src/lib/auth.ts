// lib/auth.ts
/**
 * Authentication utility - Owner Key Management
 * 
 * WHY: Abstraction layer for storing/retrieving owner keys.
 * 
 * Current implementation: SessionStorage (per-tab, cleared on tab close)
 * 
 * Future migration to auth system:
 * - Replace getOwnerKey() to call auth.getToken() or auth.getUser()?.videoOwnerKey
 * - Replace setOwnerKey() to store in auth context
 * - No other code needs to change - this is the single point of modification
 * 
 * Benefits:
 * - Easy to test (mock this module)
 * - Single point of change for future auth migration
 * - Works with cloud storage (auth stays local, data goes to cloud)
 */

const OWNER_KEY_STORAGE_KEY = "lyricsync_owner_key";

/**
 * Get the owner key for the current session.
 * 
 * @returns Owner key string, or null if not found
 */
export function getOwnerKey(): string | null {
  // Current: SessionStorage (per-tab, cleared on tab close)
  return sessionStorage.getItem(OWNER_KEY_STORAGE_KEY);
  
  // Future: Auth system (just uncomment and modify)
  // return auth.getToken();
  // or
  // return auth.getUser()?.videoOwnerKey;
}

/**
 * Store the owner key for the current session.
 * 
 * @param key - Owner key to store
 */
export function setOwnerKey(key: string): void {
  // Current: SessionStorage
  sessionStorage.setItem(OWNER_KEY_STORAGE_KEY, key);
  
  // Future: Auth system
  // auth.setToken(key);
  // or
  // auth.updateUser({ videoOwnerKey: key });
}

/**
 * Clear the stored owner key (e.g., on logout).
 */
export function clearOwnerKey(): void {
  sessionStorage.removeItem(OWNER_KEY_STORAGE_KEY);
  
  // Future: Auth system
  // auth.logout();
}

/**
 * Check if an owner key exists for the current session.
 * 
 * @returns True if owner key exists, false otherwise
 */
export function hasOwnerKey(): boolean {
  return getOwnerKey() !== null;
}

