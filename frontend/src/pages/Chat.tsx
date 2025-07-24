import { ChatArea } from "@/components/ChatArea";
import { useParams } from "react-router-dom";
import { useChatLogicContext } from "@/hooks/ChatLogicContext";

export function Chat() {
  const { projectId } = useParams<{ projectId: string }>();
  const chatLogic = useChatLogicContext();

  if (!projectId) {
    return null;
  }

  return (
    <div className="flex-1 h-full overflow-y-auto bg-background text-foreground">
      <ChatArea
        conversationId={chatLogic.selectedConversationId}
        agentProfileId={chatLogic.selectedAgentProfileId}
        onConversationCreated={chatLogic.handleConversationCreated}
        projectId={projectId}
      />
    </div>
  );
}
