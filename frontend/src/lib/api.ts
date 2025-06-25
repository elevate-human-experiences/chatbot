/**
 * API utilities for project-scoped endpoints
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

export const apiPaths = {
  // User endpoints
  users: (userId: string) => `${API_BASE_URL}/users/${userId}`,

  // Project endpoints
  projects: () => `${API_BASE_URL}/projects`,
  project: (projectId: string) => `${API_BASE_URL}/projects/${projectId}`,

  // Project-scoped agent profile endpoints
  projectProfiles: (projectId: string) => `${API_BASE_URL}/projects/${projectId}/profiles`,
  projectProfile: (projectId: string, profileId: string) =>
    `${API_BASE_URL}/projects/${projectId}/profiles/${profileId}`,

  // Project-scoped conversation endpoints
  projectConversations: (projectId: string) =>
    `${API_BASE_URL}/projects/${projectId}/conversations`,
  projectConversation: (projectId: string, conversationId: string) =>
    `${API_BASE_URL}/projects/${projectId}/conversations/${conversationId}`,
  projectConversationMessages: (projectId: string, conversationId: string) =>
    `${API_BASE_URL}/projects/${projectId}/conversations/${conversationId}/messages`,

  // Project-scoped instruction endpoints
  projectProfileInstructions: (projectId: string, profileId: string) =>
    `${API_BASE_URL}/projects/${projectId}/profiles/${profileId}/instructions`,
  projectProfileInstruction: (projectId: string, profileId: string, index: number) =>
    `${API_BASE_URL}/projects/${projectId}/profiles/${profileId}/instructions/${index}`,

  // Chat completions endpoint
  chatCompletions: () => `${API_BASE_URL}/chat/completions`,

  // Health check endpoint
  health: () => `${API_BASE_URL}/health`,
} as const;

/**
 * Legacy API paths for backward compatibility
 * @deprecated Use project-scoped paths instead
 */
export const legacyApiPaths = {
  agentProfiles: () => `${API_BASE_URL}/agent-profiles`,
  agentProfile: (profileId: string) => `${API_BASE_URL}/agent-profiles/${profileId}`,
  conversations: () => `${API_BASE_URL}/conversations`,
  conversation: (conversationId: string) => `${API_BASE_URL}/conversations/${conversationId}`,
  conversationMessages: (conversationId: string) =>
    `${API_BASE_URL}/conversations/${conversationId}/messages`,
} as const;

export { API_BASE_URL };
