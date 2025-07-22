// Project Name: Thronestead©
// File Name: auth_core.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66
/**
 * Consolidated entry point exposing authentication utilities.
 *
 * This module simply re-exports functions from various auth related modules
 * so frontend code can import them from a single location:
 *
 *   import { getAuth, initCsrf, ... } from './auth_core.js';
 *
 * AuthGuard is executed for its side effects when this module is imported.
 */

// Side effect import - runs the auth guard immediately
import './components/authGuard.js';

// Re-export everything from core auth modules
export * from './auth.js';
export * from './security/csrf.js';
export * from './env.js';
export * from './progression.js';
