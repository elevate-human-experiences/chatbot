import { useParams, useNavigate } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatArea } from "@/components/ChatArea";
import { useChatLogic } from "@/hooks/useChatLogic";

export function Chat() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  const {
    selectedConversationId,
    selectedAgentProfileId,
    refreshSidebar,
    handleConversationSelect,
    handleNewConversation,
    handleNewChat,
    handleConversationCreated,
  } = useChatLogic(projectId, apiBaseUrl, navigate);

  if (!projectId) {
    return null;
  }

  return (
    <div className="flex h-screen w-full bg-red">
      <ScrollArea className="h-full bg-gray-900">
        <Sidebar
          selectedConversationId={selectedConversationId}
          onConversationSelect={handleConversationSelect}
          onNewConversation={handleNewConversation}
          projectId={projectId}
          refreshKey={refreshSidebar}
        />
      </ScrollArea>
      <div className="flex-1 h-full overflow-y-auto">
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
