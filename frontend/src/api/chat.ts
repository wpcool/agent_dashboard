import axios from 'axios';
import { ChatRequest, ChatResponse, Conversation, Message } from '../types/chat';

const API_BASE = '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const chatApi = {
  createConversation: () =>
    api.post<Conversation>('/conversations', {}),

  listConversations: (skip = 0, limit = 20) =>
    api.get<Conversation[]>(`/conversations?skip=${skip}&limit=${limit}`),

  getConversation: (id: string) =>
    api.get<Conversation & { messages: Message[] }>(`/conversations/${id}`),

  sendMessage: (data: ChatRequest) =>
    api.post<ChatResponse>('/chat', data),
};
