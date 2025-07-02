import { useState, useCallback, useEffect } from "react";
import type { NavigateFunction } from "react-router-dom";

export function useChatLogic(
  projectId: string | undefined,
  apiBaseUrl: string,
  navigate: NavigateFunction
) {
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [selectedAgentProfileId, setSelectedAgentProfileId] = useState<string | undefined>();
  const [refreshSidebar, setRefreshSidebar] = useState(0);
  const [hasInitialized, setHasInitialized] = useState(false);

  // Redirige si no hay projectId, pero solo si la ruta es de chat
  useEffect(() => {
    // Solo redirige si la ruta actual es / o /projects/:projectId/...
    const isChatRoute =
      window.location.pathname === "/" || window.location.pathname.startsWith("/projects/");
    if (!projectId && isChatRoute) {
      navigate("/");
      return;
    }
  }, [projectId, navigate]);

  // Carga el perfil de agente por defecto al inicio
  useEffect(() => {
    const loadDefaultAgent = async () => {
      if (!projectId || hasInitialized || selectedConversationId || selectedAgentProfileId) return;
      try {
        const profilesResponse = await fetch(`${apiBaseUrl}/projects/${projectId}/profiles`);
        if (profilesResponse.ok) {
          const profilesData = await profilesResponse.json();
          const profiles = profilesData.agent_profiles || [];
          if (profiles.length > 0) {
            setSelectedAgentProfileId(profiles[0].id);
          }
        }
      } catch (error) {
        // Puedes manejar el error aquí si lo deseas
        // console.error("Error loading default agent:", error);
      } finally {
        setHasInitialized(true);
      }
    };
    loadDefaultAgent();
  }, [projectId, hasInitialized, selectedConversationId, selectedAgentProfileId, apiBaseUrl]);

  // Handlers
  const handleConversationSelect = useCallback((conversationId: string) => {
    setSelectedConversationId(conversationId);
    setSelectedAgentProfileId(undefined);
  }, []);

  const handleNewConversation = useCallback((agentProfileId: string) => {
    setSelectedAgentProfileId(agentProfileId);
    setSelectedConversationId(undefined);
  }, []);

  const handleNewChat = useCallback(() => {
    setSelectedConversationId(undefined);
  }, []);

  const handleConversationCreated = useCallback((conversationId: string) => {
    setSelectedConversationId(conversationId);
    setSelectedAgentProfileId(undefined);
    setRefreshSidebar((prev) => prev + 1);
  }, []);

  return {
    selectedConversationId,
    selectedAgentProfileId,
    refreshSidebar,
    handleConversationSelect,
    handleNewConversation,
    handleNewChat,
    handleConversationCreated,
  };
}
