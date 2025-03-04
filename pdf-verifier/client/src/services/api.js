import axios from 'axios';

// On récupère l'URL de base depuis une variable d'environnement Vite :
// Crée un fichier .env ou .env.local avec : VITE_API_URL=http://ton-backend:5000
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:3000';

// On crée une instance Axios avec l'URL de base
// On ne définit pas de 'Content-Type' par défaut pour laisser Axios choisir automatiquement
const apiClient = axios.create({
  baseURL,
});

// ----- Intercepteurs (optionnels) -----
// 1. Intercepteur de requête
apiClient.interceptors.request.use(
  (config) => {
    // Ex : ajouter un token d'authentification si nécessaire
    // const token = localStorage.getItem('token');
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    // Gérer les erreurs de requête (ex : logs)
    return Promise.reject(error);
  }
);

// 2. Intercepteur de réponse
apiClient.interceptors.response.use(
  (response) => {
    // Traitement global des réponses OK
    return response;
  },
  (error) => {
    // Gestion globale des erreurs
    console.error('[API error]', error);
    // Tu peux rediriger vers une page de login, afficher une alerte, etc.
    return Promise.reject(error);
  }
);

export default apiClient;
