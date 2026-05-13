import axios from "axios";

// In Docker: requests go to /api/* which Traefik strips to /* before hitting the gateway.
// In local dev (vite dev server): vite.config.js proxies /api → http://api-gateway:8000
const BASE = "/api";

const client = axios.create({ baseURL: BASE });

// Attach JWT on every request if present
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("sa_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, clear stored token so the app returns to login
client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("sa_token");
      localStorage.removeItem("sa_email");
      // Trigger a page reload — App.jsx will see no token and show LoginPage
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

export default client;