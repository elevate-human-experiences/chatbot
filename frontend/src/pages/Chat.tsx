import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { ChatArea } from "@/components/ChatArea";

export function Chat() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [selectedConversationId, setSelectedConversationId] = useState<string | undefined>();
  const [selectedAgentProfileId, setSelectedAgentProfileId] = useState<string | undefined>();
  const [refreshSidebar, setRefreshSidebar] = useState(0);
  const [hasInitialized, setHasInitialized] = useState(false);
  const chatAreaWrapperRef = useRef<HTMLDivElement>(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  useEffect(() => {
    // Validate that we have a projectId
    if (!projectId) {
      navigate("/");
      return;
    }
  }, [projectId, navigate]);

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

  // Auto-scroll to bottom when ChatArea content grows
  useEffect(() => {
    const el = chatAreaWrapperRef.current;
    if (!el) return;

    // Create a MutationObserver to watch for content changes
    const observer = new MutationObserver(() => {
      el.scrollTop = el.scrollHeight;
    });

    observer.observe(el, { childList: true, subtree: true });

    // Initial scroll
    el.scrollTop = el.scrollHeight;

    return () => observer.disconnect();
  }, [selectedConversationId, selectedAgentProfileId, refreshSidebar]);

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
    return null; // This will be handled by the useEffect redirect
  }

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden">
      <Sidebar
        selectedConversationId={selectedConversationId}
        onConversationSelect={handleConversationSelect}
        onNewConversation={handleNewConversation}
        projectId={projectId}
        refreshKey={refreshSidebar}
      />
      <div className="flex-1 h-full overflow-y-auto" ref={chatAreaWrapperRef}>
        <ChatArea
          conversationId={selectedConversationId}
          agentProfileId={selectedAgentProfileId}
          onConversationCreated={handleConversationCreated}
          onNewChat={handleNewChat}
          projectId={projectId}
        />
      </div>
    </div>
  );
}
