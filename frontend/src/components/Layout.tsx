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

  if (showChat) {
    return (
      <ChatLogicContext.Provider value={{ ...chatLogic, projectId, apiBaseUrl, navigate }}>
        <div className="flex h-screen">
          {/* Sidebar + Navigation */}
          {sidebarVisible && (
            <div
              className="flex flex-col bg-gray-100 border-r border-gray-200 transition-all duration-200"
              style={{ width: 280, minWidth: 80 }}
            >
              {/* Navigation menu */}
              <nav className="flex flex-col items-start h-auto p-3 gap-8 border-b border-gray-200">
                {navItems.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.path;
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={cn(
                        "flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full",
                        isActive ? "text-blue-500" : ""
                      )}
                    >
                      <Icon className="w-5 h-5" />
                      <span>{item.label}</span>
                    </Link>
                  );
                })}
              </nav>
              {/* Sidebar (conversaciones, perfiles, etc) */}
              <ScrollArea className="h-full bg-gray-900 flex-1">
                <Sidebar
                  selectedConversationId={chatLogic.selectedConversationId}
                  onConversationSelect={chatLogic.handleConversationSelect}
                  onNewConversation={chatLogic.handleNewConversation}
                  projectId={projectId}
                  refreshKey={chatLogic.refreshSidebar}
                />
              </ScrollArea>
            </div>
          )}
          {/* Main content area */}
          <div className="flex-1 bg-white relative">
            <button
              onClick={() => setSidebarVisible((v) => !v)}
              className="absolute top-4 left-0 z-20 bg-white border border-gray-300 rounded-full shadow p-1 hover:bg-gray-50 transition"
              style={{
                transform: "translateX(-50%)",
                left: sidebarVisible ? 280 : 0,
              }}
            >
              {sidebarVisible ? (
                <ChevronLeft className="w-5 h-5" />
              ) : (
                <ChevronRight className="w-5 h-5" />
              )}
            </button>
            <div className="w-full">
              <Outlet />
            </div>
          </div>
        </div>
      </ChatLogicContext.Provider>
    );
  }

  // Si no hay projectId, solo renderiza el layout base y el menú
  return (
    <div className="flex h-screen">
      <div
        className="flex flex-col bg-gray-100 border-r border-gray-200 transition-all duration-200"
        style={{ width: 80, minWidth: 80 }}
      >
        <nav className="flex flex-col items-center h-full p-3 gap-8">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "flex flex-col items-center justify-center text-gray-700 hover:text-blue-600 transition-colors w-full py-2",
                  isActive ? "text-blue-500" : ""
                )}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs mt-1">{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex-1 bg-white relative">
        <div className="w-full">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
