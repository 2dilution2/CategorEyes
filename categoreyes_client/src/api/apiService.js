import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL;

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const uploadImage = async (formData) => {
    try {
      const response = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      const { session_id } = response.data;
      return session_id;
    } catch (error) {
      console.error('Error uploading files:', error);
      throw error;
    }
  };

export const fetchImagesBySession = async (sessionId) => {
    try {
        const response = await api.get(`/uploaded_images/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching images by session:', error);
        throw error;
      }
};

export const fetchCategoriesBySession = async(sessionId) => {
    try {
        const response = await api.get(`/categories/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching categories by session:', error);
        throw error;
      }
};

export const fetchImagesByCategory = async (category, sessionId) => {
    try {
        const response = await api.get(`/categories/${encodeURIComponent(category)}/${sessionId}`);
        return response.data;
      } catch (error) {
        console.error('Error fetching category images:', error);
        throw error;
      }
};
