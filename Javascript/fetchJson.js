// Project Name: Thronestead©
// File Name: fetchJson.js
// Version: 7/1/2025 10:38
// Developer: Deathsgift66
// Thin wrapper re-exporting JSON fetch helpers from utils.js

import { jsonFetch, authJsonFetch } from './utils.js';

export const fetchJson = jsonFetch;
export const authFetchJson = authJsonFetch;
