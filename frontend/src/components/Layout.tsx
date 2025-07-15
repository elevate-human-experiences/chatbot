import { Outlet, useParams, useNavigate, useLocation } from "react-router-dom";
import { Asterisk, ChevronLeft, ChevronRight, MessageCircle, Info, Settings } from "lucide-react";
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
  const location = useLocation();
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

  // Navigation menu items
  const navItems = [
    { path: "/", label: "Chats", icon: MessageCircle },
    { path: "/about", label: "About", icon: Info },
    { path: "/settings", label: "Settings", icon: Settings },
  ];

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
            {/* Sidebar + Navigation */}
            <div
              className="flex flex-col bg-gray-100 border-r border-gray-200 transition-all duration-200"
              style={{ width: sidebarWidth, minWidth: collapsedSidebarWidth }}
            >
              {/* Fixed top menu item: Claude Chat */}
              <div
                className={cn(
                  "sticky top-0 z-10 bg-gray-100 w-full px-4 py-6 flex items-center", // py-6 for more top/bottom padding
                  sidebarVisible ? "justify-start" : "justify-center"
                )}
              >
                <Asterisk className="w-5 h-5 text-gray-700" />
                {sidebarVisible && (
                  <span className="font-semibold text-lg text-gray-700 ml-2">Claude Chat</span>
                )}
              </div>
              {/* Navigation menu */}
              <nav
                className={cn(
                  "flex flex-col h-auto p-3 gap-2 border-b border-gray-200",
                  sidebarVisible ? "items-start gap-8" : "items-center gap-4"
                )}
              >
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isChat = item.path === "/";
                  const isActive = isChat
                    ? location.pathname === "/" || location.pathname.startsWith("/projects")
                    : location.pathname === item.path;
                  return (
                    <button
                      key={item.path}
                      type="button"
                      disabled={isActive}
                      onClick={() => {
                        if (!isActive) navigate(item.path);
                      }}
                      className={cn(
                        "flex items-center text-stone-500 hover:text-pink-700 transition-colors w-full py-2 cursor-pointer",
                        sidebarVisible ? "gap-3" : "justify-center",
                        isActive ? "text-stone-700 font-bold" : ""
                      )}
                      style={{ background: "none", border: "none", outline: "none" }}
                    >
                      <Icon className={cn("w-6 h-6", isActive ? "text-stone-700" : "")} />
                      {sidebarVisible && (
                        <span
                          className={cn(
                            "text-base font-normal",
                            isActive && "font-bold text-stone-700"
                          )}
                        >
                          {item.label}
                        </span>
                      )}
                    </button>
                  );
                })}
              </nav>
              {/* Sidebar (conversaciones, perfiles, etc) solo si expandido */}
              {showChat && sidebarVisible && (
                <ScrollArea className="flex-1 min-h-0 h-0 overflow-hidden">
                  <Sidebar
                    selectedConversationId={chatLogic.selectedConversationId}
                    onConversationSelect={chatLogic.handleConversationSelect}
                    onNewConversation={chatLogic.handleNewConversation}
                    projectId={projectId}
                    refreshKey={chatLogic.refreshSidebar}
                  />
                </ScrollArea>
              )}
              {/* UserInfo fixed at the bottom of sidebar */}
              <div className="absolute bottom-0 left-0 w-full border-t border-gray-200 bg-gray-100">
                <UserInfo user={currentUser} hideDetails={!sidebarVisible} />
              </div>
            </div>
            {/* Main content area */}
            <div className="flex-1 bg-white relative">
              <button
                onClick={() => setSidebarVisible((v) => !v)}
                className="fixed top-4 z-30 bg-white border border-gray-300 rounded-full shadow p-1 hover:bg-gray-50 transition"
                style={{
                  left: sidebarWidth,
                  transform: "translateX(-50%)",
                  transition: "left 0.2s",
                }}
                aria-label={sidebarVisible ? "Ocultar menú" : "Mostrar menú"}
              >
                {sidebarVisible ? (
                  <ChevronLeft className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
              </button>
              <div className="h-full w-full">
                <Outlet />
              </div>
            </div>
          </div>
        </ChatLogicContext.Provider>
      ) : (
        // Layout base sin projectId, pero con botón de mostrar/ocultar sidebar
        <div className="flex h-screen">
          <div
            className="flex flex-col bg-gray-100 border-r border-gray-200 transition-all duration-200"
            style={{ width: sidebarWidth, minWidth: collapsedSidebarWidth }}
          >
            {/* Fixed top menu item: Claude Chat */}
            <div
              className={cn(
                "sticky top-0 z-10 bg-gray-100 w-full px-4 py-6 flex items-center", // py-6 for more top/bottom padding
                sidebarVisible ? "justify-start" : "justify-center"
              )}
            >
              <Asterisk className="w-5 h-5 text-gray-700" />
              {sidebarVisible && (
                <span className="font-semibold text-lg text-gray-700 ml-2">Claude Chat</span>
              )}
            </div>
            <nav
              className={cn(
                "flex flex-col h-full p-3 border-b border-gray-200",
                sidebarVisible ? "items-start gap-8" : "items-center gap-4"
              )}
            >
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <button
                    key={item.path}
                    type="button"
                    disabled={isActive}
                    onClick={() => {
                      if (!isActive) navigate(item.path);
                    }}
                    className={cn(
                      "flex items-center text-stone-500 hover:text-pink-700 transition-colors w-full py-2 cursor-pointer",
                      sidebarVisible ? "gap-3" : "justify-center",
                      isActive ? "text-stone-700 font-bold " : ""
                    )}
                    style={{ background: "none", border: "none", outline: "none" }}
                  >
                    <Icon className={cn("w-6 h-6", isActive ? "text-stone-700" : "")} />
                    {sidebarVisible && (
                      <span
                        className={cn(
                          "text-base font-normal",
                          isActive && "font-bold text-stone-700"
                        )}
                      >
                        {item.label}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
            {/* UserInfo fixed at the bottom of sidebar */}
            <div className="absolute bottom-0 left-0 w-full border-t border-gray-200 bg-gray-100">
              <UserInfo user={currentUser} hideDetails={!sidebarVisible} />
            </div>
          </div>
          <div className="flex-1 bg-white relative">
            <button
              onClick={() => setSidebarVisible((v) => !v)}
              className="fixed top-4 z-30 bg-white border border-gray-300 rounded-full shadow p-1 hover:bg-gray-50 transition"
              style={{
                left: sidebarWidth,
                transform: "translateX(-50%)",
                transition: "left 0.2s",
              }}
              aria-label={sidebarVisible ? "Ocultar menú" : "Mostrar menú"}
            >
              {sidebarVisible ? (
                <ChevronLeft className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>
            <div className="h-full w-full">
              <Outlet />
            </div>
          </div>
        </div>
      )}
    </>
  );
}
