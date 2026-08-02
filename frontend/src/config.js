// Base URLs for the backend. Override at build time with Vite env vars
// (VITE_API_URL) — see .env.example.
export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8001";
