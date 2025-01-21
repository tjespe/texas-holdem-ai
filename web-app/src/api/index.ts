export const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export const apiClient = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem("token");

  // Add the Authorization header if a token exists
  const headers = {
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  // Call fetch with the updated headers
  return fetch(API_BASE_URL + url, { ...options, headers });
};
