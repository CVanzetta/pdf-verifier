// client/src/services/api.js
import axios from 'axios';

// On définit l'URL de base vers ton backend FastAPI.
// Par exemple : http://127.0.0.1:5000 (ou l'URL/port que tu utilises).
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:5000', 
  // On ne met pas 'Content-Type' pour que Axios détecte automatiquement
});

// ----- Intercepteurs (optionnels) -----
// 1. Intercepteur de requête
apiClient.interceptors.request.use(
  (config) => {
    // Ex : ajouter un token d'authentification si nécessaire
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 2. Intercepteur de réponse
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API error]', error);
    return Promise.reject(error);
  }
);

export default apiClient;
