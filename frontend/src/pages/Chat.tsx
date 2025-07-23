import { ChatArea } from "@/components/ChatArea";
import { Sidebar } from "@/components/Sidebar";
import { useParams, useNavigate } from "react-router-dom";
import { useState, useEffect, useCallback } from "react";
import type { ToolModel } from "@/lib/api";

export function Chat() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [selectedAgentProfileId, setSelectedAgentProfileId] = useState<string | undefined>();
  const [refreshSidebar, setRefreshSidebar] = useState(0);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [tools, setTools] = useState<ToolModel[]>([]);
  const [toolsLoading, setToolsLoading] = useState(true);
  const [toolsError, setToolsError] = useState<string | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  useEffect(() => {
    // Validate that we have a projectId
    if (!projectId) {
      navigate("/");
      return;
    }
    // Fetch available tools
    const fetchTools = async () => {
      setToolsLoading(true);
      setToolsError(null);
      try {
        const resp = await fetch(`${apiBaseUrl}/tools`);
        if (!resp.ok) throw new Error(`Failed to fetch tools: ${resp.status}`);
        const data = await resp.json();
        setTools(data.tools || []);
      } catch (err: unknown) {
        setToolsError(err instanceof Error ? err.message : "Unknown error");
        setTools([]);
      } finally {
        setToolsLoading(false);
      }
    };
    fetchTools();
  }, [projectId, apiBaseUrl, navigate]);

  // Load default agent profile on first load
  useEffect(() => {
    const loadDefaultAgent = async () => {
      if (!projectId || hasInitialized || selectedConversationId || selectedAgentProfileId) return;

      try {
        const profilesResponse = await fetch(`${apiBaseUrl}/projects/${projectId}/profiles`);
        if (profilesResponse.ok) {
          const profilesData = await profilesResponse.json();
          const profiles = profilesData.agent_profiles || [];

          if (profiles.length > 0) {
            // Select the first agent profile as default
            setSelectedAgentProfileId(profiles[0].id);
          }
        }
      } catch (error) {
        console.error("Error loading default agent:", error);
      } finally {
        setHasInitialized(true);
      }
    };

    loadDefaultAgent();
  }, [projectId, hasInitialized, selectedConversationId, selectedAgentProfileId, apiBaseUrl]);

  const handleConversationSelect = useCallback((conversationId: string) => {
    setSelectedConversationId(conversationId);
    setSelectedAgentProfileId(undefined); // Clear when selecting existing conversation
  }, []);

  const handleNewConversation = useCallback((agentProfileId: string) => {
    setSelectedAgentProfileId(agentProfileId);
    setSelectedConversationId(undefined); // Clear selected conversation for new chat
  }, []);

  const handleNewChat = useCallback(() => {
    // Keep the same agent profile but start a new conversation
    setSelectedConversationId(undefined);
  }, []);

  const handleConversationCreated = useCallback((conversationId: string) => {
    setSelectedConversationId(conversationId);
    setSelectedAgentProfileId(undefined);
    // Trigger sidebar refresh to show the new conversation
    setRefreshSidebar((prev) => prev + 1);
  }, []);

  if (!projectId) {
    return null;
  }

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden">
      <Sidebar
        selectedConversationId={selectedConversationId}
        onConversationSelect={handleConversationSelect}
        onNewConversation={handleNewConversation}
        projectId={projectId}
        refreshKey={refreshSidebar}
        tools={tools}
        toolsLoading={toolsLoading}
        toolsError={toolsError}
      />
      <ChatArea
        conversationId={selectedConversationId}
        agentProfileId={selectedAgentProfileId}
        onConversationCreated={handleConversationCreated}
        projectId={projectId}
        tools={tools}
        toolsLoading={toolsLoading}
        toolsError={toolsError}
      />
    </div>
  );
}
