import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = axios.create({
  baseURL: API_URL,
});

export const getDatasets = async () => {
  const res = await api.get('/datasets');
  return res.data;
};

export const createDataset = async (name: string) => {
  const res = await api.post('/datasets', { name });
  return res.data;
};

export const uploadDocument = async (
  datasetId: number, 
  file: File, 
  options?: { chunk_size?: number, chunk_overlap?: number, chunk_method?: string, embedding_model?: string }
) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('dataset_id', datasetId.toString());
  
  if (options?.chunk_size) formData.append('chunk_size', options.chunk_size.toString());
  if (options?.chunk_overlap) formData.append('chunk_overlap', options.chunk_overlap.toString());
  if (options?.chunk_method) formData.append('chunk_method', options.chunk_method);
  if (options?.embedding_model) formData.append('embedding_model', options.embedding_model);
  
  const res = await api.post('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data;
};

export const chat = async (query: string, datasetId?: number, sessionId?: string) => {
  const res = await api.post('/chat', {
    query,
    dataset_id: datasetId,
    session_id: sessionId
  });
  return res.data;
};

export const getStats = async () => {
  const res = await api.get('/stats');
  return res.data;
};
