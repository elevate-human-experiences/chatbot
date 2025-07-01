import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatArea } from "@/components/ChatArea";

import { ArrowUp } from "lucide-react";

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
      el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
    });

    observer.observe(el, { childList: true, subtree: true });

    // Initial scroll
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });

    return () => observer.disconnect();
  }, [selectedConversationId, selectedAgentProfileId, refreshSidebar]);

  // Show/hide scroll up button and set opacity based on scroll position
  const [showScrollUp, setShowScrollUp] = useState(false);

  useEffect(() => {
    const el = chatAreaWrapperRef.current;
    if (!el) return;

    const updateButton = () => {
      const canScroll = el.scrollHeight > el.clientHeight + 1;
      const nearTop = el.scrollTop < 0;
      setShowScrollUp(canScroll && !nearTop);
    };

    // Mutation observer for content changes
    const observer = new MutationObserver(() => {
      updateButton();
    });

    observer.observe(el, { childList: true, subtree: true });

    // Listen to scroll events for opacity
    el.addEventListener("scroll", updateButton);

    // Initial state
    updateButton();

    return () => {
      observer.disconnect();
      el.removeEventListener("scroll", updateButton);
    };
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
    <div className="flex h-screen w-full bg-white">
      <ScrollArea className="h-full bg-gray-900">
        <Sidebar
          selectedConversationId={selectedConversationId}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
          projectId={projectId}
          refreshKey={refreshSidebar}
        />
      </ScrollArea>
      <div className="flex-1 h-full overflow-y-auto" ref={chatAreaWrapperRef}>
        <ChatArea
          conversationId={selectedConversationId}
          agentProfileId={selectedAgentProfileId}
          onConversationCreated={handleConversationCreated}
          onNewChat={handleNewChat}
          projectId={projectId}
        />
        <button
          type="button"
          className="bg-gray-100 text-gray-700 rounded-full shadow hover:bg-gray-200 transition flex items-center justify-center"
          style={{
            zIndex: 30,
            position: "fixed",
            right: "2rem",
            bottom: "8rem",
            width: "48px",
            height: "48px",
            padding: 0,
            pointerEvents: showScrollUp ? "auto" : "none",
            transition: "opacity 0.3s",
          }}
          onClick={() => {
            const el = chatAreaWrapperRef.current;
            if (el) el.scrollTo({ top: 0, behavior: "smooth" });
          }}
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
