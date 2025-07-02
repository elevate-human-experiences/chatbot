import { createContext, useContext } from "react";
import type { NavigateFunction } from "react-router-dom";

export interface ChatLogicContextProps {
  selectedConversationId?: string;
  selectedAgentProfileId?: string;
  refreshSidebar?: number;
  handleConversationSelect: (conversationId: string) => void;
  handleNewConversation: (agentProfileId: string) => void;
  handleNewChat: (message: string) => void;
  handleConversationCreated: (conversationId: string) => void;
  projectId?: string;
  apiBaseUrl: string;
  navigate: NavigateFunction;
}

export const ChatLogicContext = createContext<ChatLogicContextProps | undefined>(undefined);

export function useChatLogicContext() {
  const ctx = useContext(ChatLogicContext);
  if (!ctx) throw new Error("useChatLogicContext must be used within ChatLogicProvider");
  return ctx;
}
