import { Outlet, useParams, useNavigate } from "react-router-dom";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { ChatLogicContext } from "@/hooks/ChatLogicContext";
import { useChatLogic } from "@/hooks/useChatLogic";
import { Sidebar } from "@/components/Sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { useState, useEffect } from "react";
import { UserInfo } from "@/components/UserInfo";

export function Layout() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [currentUser, setCurrentUser] = useState<{
    id: string;
    name: string;
    email: string;
  } | null>(null);

  // Load user info once on mount
  useEffect(() => {
    const fetchUser = async () => {
      const userId = localStorage.getItem("chatbot_user_id");
      if (!userId) return;
      try {
        const response = await fetch(`${apiBaseUrl}/users/${userId}`);
        if (response.ok) {
          const userData = await response.json();
          setCurrentUser(userData);
        }
      } catch {
        // Silently fail
      }
    };
    fetchUser();
  }, [apiBaseUrl]);

  // Siempre llama el hook, pero solo usa el resultado si hay projectId
  const chatLogic = useChatLogic(projectId, apiBaseUrl, navigate);
  const showChat = Boolean(projectId);

  // Sidebar width depending on state and projectId
  const expandedSidebarWidth = 280;
  const collapsedSidebarWidth = 90; // Más ancho cuando está oculta
  const sidebarWidth = sidebarVisible ? expandedSidebarWidth : collapsedSidebarWidth;

  return (
    <>
      {showChat ? (
        <ChatLogicContext.Provider value={{ ...chatLogic, projectId, apiBaseUrl, navigate }}>
          {/* Main layout with sidebar toggle */}
          <div className="flex h-screen">
            {/* Sidebar */}
            <div
              className="flex flex-col bg-background border-r border-border transition-all duration-200"
              style={{ width: sidebarWidth, minWidth: collapsedSidebarWidth }}
            >
              {/* Fixed top menu item: Elevate */}
              <div
                className={cn(
                  "sticky top-0 z-10 bg-background w-full px-4 pt-6 pb-2 flex items-center",
                  sidebarVisible ? "justify-start" : "justify-center"
                )}
              >
                {sidebarVisible && (
                  <span className="font-semibold text-lg text-primary ml-2">Elevate</span>
                )}
              </div>

              {/* Sidebar (profiles and conversations) */}
              <ScrollArea className="flex-1 min-h-0 h-0 overflow-hidden">
                <Sidebar
                  selectedConversationId={chatLogic.selectedConversationId}
                  onConversationSelect={chatLogic.handleConversationSelect}
                  onNewConversation={chatLogic.handleNewConversation}
                  projectId={projectId}
                  refreshKey={chatLogic.refreshSidebar}
                  collapsed={!sidebarVisible}
                />
              </ScrollArea>

              {/* UserInfo fixed at the bottom of sidebar */}
              <div className="absolute bottom-0 left-0 w-full border-t border-border bg-background">
                <UserInfo user={currentUser} hideDetails={!sidebarVisible} />
              </div>
            </div>

            {/* Main content area */}
            <div className="flex-1 bg-background relative">
              <button
                onClick={() => setSidebarVisible((v) => !v)}
                className="fixed top-4 z-30 bg-background border border-border rounded-full shadow p-1 hover:bg-accent transition"
                style={{
                  left: sidebarWidth,
                  transform: "translateX(-50%)",
                  transition: "left 0.2s",
                }}
                aria-label={sidebarVisible ? "Hide sidebar" : "Show sidebar"}
              >
                {sidebarVisible ? (
                  <ChevronLeft className="w-4 h-4" />
                ) : (
                  <ChevronRight className="w-4 h-4" />
                )}
              </button>
              <div className="h-full w-full">
                <Outlet />
              </div>
            </div>
          </div>
        </ChatLogicContext.Provider>
      ) : (
        <Outlet />
      )}
    </>
  );
}
