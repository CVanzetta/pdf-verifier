import axios from 'axios';

// On peut utiliser une variable d’environnement pour l’URL du backend :
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Intercepteurs (optionnels) pour logger les erreurs, gérer les tokens, etc.
apiClient.interceptors.response.use(
  response => response,
  error => {
    console.error('[API error]', error);
    return Promise.reject(error);
  }
);

export default apiClient;
