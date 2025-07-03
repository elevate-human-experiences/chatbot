import { Outlet, useParams, useNavigate, Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageCircle, Info, Settings } from "lucide-react";
import { ChatLogicContext } from "@/hooks/ChatLogicContext";
import { useChatLogic } from "@/hooks/useChatLogic";
import { Sidebar } from "@/components/Sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

export function Layout() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";
  const [sidebarVisible, setSidebarVisible] = useState(true);

  // Navigation menu items
  const navItems = [
    { path: "/", label: "Chat", icon: MessageCircle },
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
              {/* Navigation menu */}
              <nav
                className={cn(
                  "flex flex-col h-auto p-3 gap-2 border-b border-gray-200",
                  sidebarVisible ? "items-start gap-8" : "items-center gap-4"
                )}
              >
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={cn(
                        "flex items-center text-gray-700 hover:text-blue-600 transition-colors w-full py-2",
                        sidebarVisible ? "gap-3" : "justify-center",
                        isActive ? "text-blue-500" : ""
                      )}
                    >
                      <Icon className="w-6 h-6" />
                      {sidebarVisible && (
                        <span className="text-base font-normal">{item.label}</span>
                      )}
                    </Link>
                  );
                })}
              </nav>
              {/* Sidebar (conversaciones, perfiles, etc) solo si expandido */}
              {showChat && sidebarVisible && (
                <ScrollArea className="flex-1 min-h-0 h-0 bg-gray-900 overflow-hidden">
                  <Sidebar
                    selectedConversationId={chatLogic.selectedConversationId}
                    onConversationSelect={chatLogic.handleConversationSelect}
                    onNewConversation={chatLogic.handleNewConversation}
                    projectId={projectId}
                    refreshKey={chatLogic.refreshSidebar}
                  />
                </ScrollArea>
              )}
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
                  <Link
                    key={item.path}
                    to={item.path}
                    className={cn(
                      "flex items-center text-gray-700 hover:text-blue-600 transition-colors w-full py-2",
                      sidebarVisible ? "gap-3" : "justify-center",
                      isActive ? "text-blue-500" : ""
                    )}
                  >
                    <Icon className="w-6 h-6" />
                    {sidebarVisible && <span className="text-base font-normal">{item.label}</span>}
                  </Link>
                );
              })}
            </nav>
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
