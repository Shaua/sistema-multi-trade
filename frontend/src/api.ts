export const getAuthToken = () => localStorage.getItem('token');
export const setAuthToken = (token: string) => localStorage.setItem('token', token);
export const removeAuthToken = () => localStorage.removeItem('token');

export const BASE_URL = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_URL || 'http://localhost:8000');

export const apiFetch = async (url: string, options: RequestInit = {}) => {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const finalUrl = url.replace('http://localhost:8000', BASE_URL);

  const response = await fetch(finalUrl, {
    ...options,
    headers
  });

  if (response.status === 401) {
    removeAuthToken();
    window.dispatchEvent(new Event('auth_error'));
  }

  return response;
};
