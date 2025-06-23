const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function getAuthToken() {
  const session = JSON.parse(localStorage.getItem("supabase.auth.token"));
  return session?.currentSession?.access_token || null;
}

function getHeaders(isJson = true) {
  const token = getAuthToken();
  const headers = {};

  if (isJson) headers["Content-Type"] = "application/json";
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function handleResponse(response) {
  const contentType = response.headers.get("content-type");
  const isJson = contentType && contentType.includes("application/json");
  const data = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new Error(
      `API Error (${response.status}): ${typeof data === "string" ? data : data?.detail || "Unknown error"}`
    );
  }

  return data;
}

export async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "GET",
    headers: getHeaders(),
  });
  return handleResponse(response);
}

export async function apiPost(endpoint, body = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiPut(endpoint, body = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "PUT",
    headers: getHeaders(),
    body: JSON.stringify(body),
  });
  return handleResponse(response);
}

export async function apiDelete(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "DELETE",
    headers: getHeaders(),
  });
  return handleResponse(response);
}
