import { useState, useEffect, useCallback } from "react";

function truncateText(text: string, maxLength: number = 28): string {
  if (!text) return "";
  return text.length > maxLength ? text.slice(0, maxLength) + "..." : text;
}
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { ChevronRight, ChevronDown } from "lucide-react";

interface AgentProfile {
  id: string;
  name: string;
  description?: string;
  instructions?: string[];
  avatar?: string;
}

interface Conversation {
  id: string;
  title: string;
  agent_profile_id: string;
  started_at: string;
  messages: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
}

interface SidebarProps {
  selectedConversationId?: string;
  onConversationSelect: (conversationId: string) => void;
  onNewConversation: (agentProfileId: string) => void;
  projectId?: string;
  refreshKey?: number; // Add this to force re-renders when conversations change
  tools?: Array<{ function?: { name?: string; description?: string } }>;
  toolsLoading?: boolean;
  toolsError?: string | null;
  collapsed?: boolean;
}

export function Sidebar({
  selectedConversationId,
  onConversationSelect,
  onNewConversation,
  projectId,
  refreshKey,
  collapsed = false,
}: SidebarProps) {
  const [agentProfiles, setAgentProfiles] = useState<AgentProfile[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [expandedProfiles, setExpandedProfiles] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  // Load expansion state from localStorage
  const getStorageKey = useCallback(
    (projectId: string) => `chatbot_expanded_profiles_${projectId}`,
    []
  );

  console.log(conversations);

  const loadExpandedState = useCallback((): Set<string> => {
    if (!projectId) return new Set<string>();

    try {
      const stored = localStorage.getItem(getStorageKey(projectId));
      if (stored) {
        return new Set(JSON.parse(stored) as string[]);
      }
    } catch (error) {
      console.error("Error loading expanded state:", error);
    }
    return new Set<string>();
  }, [projectId, getStorageKey]);

  const saveExpandedState = useCallback(
    (expanded: Set<string>) => {
      if (!projectId) return;

      try {
        localStorage.setItem(getStorageKey(projectId), JSON.stringify(Array.from(expanded)));
      } catch (error) {
        console.error("Error saving expanded state:", error);
      }
    },
    [projectId, getStorageKey]
  );

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  const loadData = useCallback(async () => {
    try {
      setLoading(true);

      // Get user ID from localStorage
      const userId = localStorage.getItem("chatbot_user_id");
      if (!userId) {
        console.error("No user ID found in localStorage");
        return;
      }

      // Load agent profiles - use project-scoped API
      if (projectId) {
        const profilesUrl = `${apiBaseUrl}/projects/${projectId}/profiles`;
        const profilesResponse = await fetch(profilesUrl);
        if (profilesResponse.ok) {
          const profilesResponseData = await profilesResponse.json();
          const profilesData = profilesResponseData.profiles || [];
          setAgentProfiles(Array.isArray(profilesData) ? profilesData : []);

          // If no expansion state is stored and there are profiles, expand the first one
          const currentExpanded = loadExpandedState();
          if (currentExpanded.size === 0 && profilesData.length > 0) {
            const newExpanded = new Set([profilesData[0].id]);
            setExpandedProfiles(newExpanded);
            saveExpandedState(newExpanded);
          }
        } else {
          console.error("Failed to load agent profiles:", profilesResponse.statusText);
          setAgentProfiles([]);
        }

        // Load conversations - use project-scoped API
        const conversationsUrl = `${apiBaseUrl}/projects/${projectId}/conversations`;
        const conversationsResponse = await fetch(conversationsUrl);
        if (conversationsResponse.ok) {
          const conversationsResponseData = await conversationsResponse.json();
          const conversationsData = conversationsResponseData.conversations || [];
          setConversations(Array.isArray(conversationsData) ? conversationsData : []);
        } else {
          console.error("Failed to load conversations:", conversationsResponse.statusText);
          setConversations([]);
        }
      } else {
        // Clear data if no project is selected
        setAgentProfiles([]);
        setConversations([]);
      }
    } catch (error) {
      console.error("Error loading sidebar data:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId, apiBaseUrl, loadExpandedState, saveExpandedState]);

  useEffect(() => {
    loadData();
  }, [projectId, refreshKey, loadData]); // Add refreshKey to dependencies

  // Load expansion state and auto-expand first profile if needed
  useEffect(() => {
    if (projectId && agentProfiles.length > 0) {
      const currentExpanded = loadExpandedState();
      setExpandedProfiles(currentExpanded);

      // If no expansion state is stored and there are profiles, expand the first one
      if (currentExpanded.size === 0) {
        const newExpanded = new Set([agentProfiles[0].id]);
        setExpandedProfiles(newExpanded);
        saveExpandedState(newExpanded);
      }
    }
  }, [projectId, agentProfiles, loadExpandedState, saveExpandedState]);

  const toggleProfileExpansion = (profileId: string) => {
    const newExpanded = new Set(expandedProfiles);
    if (newExpanded.has(profileId)) {
      newExpanded.delete(profileId);
    } else {
      newExpanded.add(profileId);
    }
    setExpandedProfiles(newExpanded);
    saveExpandedState(newExpanded);
  };

  const getConversationsForProfile = (profileId: string) => {
    return conversations
      .filter((conv) => conv.agent_profile_id === profileId)
      .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
  };

  const getConversationTitle = (conversation: Conversation) => {
    if (conversation.title) return conversation.title;

    // Generate title from first user message
    const firstUserMessage = conversation.messages.find((m) => m.role === "user");
    if (firstUserMessage) {
      return (
        firstUserMessage.content.slice(0, 50) + (firstUserMessage.content.length > 50 ? "..." : "")
      );
    }

    return "New Conversation";
  };

  if (loading) {
    return (
      <div className="w-80 text-white border-r border-gray-700 p-4">
        <div className="text-center text-gray-400">Loading...</div>
      </div>
    );
  }

  if (collapsed) {
    // Collapsed view - show only avatars
    return (
      <div className="flex flex-col h-full min-h-0 overflow-hidden">
        <div className="flex-1 min-h-0 overflow-y-auto space-y-2 py-4">
          {agentProfiles.map((profile) => {
            const profileConversations = getConversationsForProfile(profile.id);
            const hasActiveConversation = profileConversations.some(
              (conv) => conv.id === selectedConversationId
            );

            return (
              <div key={profile.id} className="flex justify-center">
                <Button
                  variant="ghost"
                  className={cn(
                    "w-12 h-12 rounded-full p-0 flex items-center justify-center transition-colors",
                    hasActiveConversation
                      ? "ring-2 ring-blue-500 bg-gray-800 hover:bg-gray-700"
                      : "hover:bg-gray-200"
                  )}
                  onClick={() => onNewConversation(profile.id)}
                  title={profile.name}
                >
                  {profile.avatar ? (
                    <img
                      src={`data:image/png;base64,${profile.avatar}`}
                      alt={profile.name}
                      className="w-10 h-10 rounded-full"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded-full bg-gray-600 flex items-center justify-center text-white text-sm font-semibold">
                      {profile.name.charAt(0).toUpperCase()}
                    </div>
                  )}
                </Button>
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="text-white flex flex-col h-full min-h-0 overflow-hidden">
      {/* Agent Profiles and Conversations */}
      <div className="flex-1 min-h-0 overflow-x-hidden">
        <div className="space-y-0">
          {agentProfiles.length === 0 ? (
            <div className="text-center text-gray-400 text-sm py-8">No agent profiles found</div>
          ) : (
            agentProfiles.map((profile) => {
              const profileConversations = getConversationsForProfile(profile.id);
              const isExpanded = expandedProfiles.has(profile.id);

              return (
                <div key={profile.id} className="border-t border-b border-gray-700">
                  {/* Agent Profile Header - Level 1 */}
                  <div className="border-l-4 border-gray-600">
                    <Button
                      variant="ghost"
                      className={cn(
                        "w-full justify-start text-left font-medium text-sm h-auto rounded-none px-4 py-3 transition-colors",
                        isExpanded
                          ? "bg-gray-800 text-white hover:bg-gray-700"
                          : "text-gray-700 hover:bg-gray-200 hover:text-gray-900"
                      )}
                      onClick={() => {
                        toggleProfileExpansion(profile.id);
                        onNewConversation(profile.id);
                      }}
                    >
                      <div className="flex items-center space-x-3 min-w-0 flex-1">
                        <div className="flex items-center space-x-2">
                          {profile.avatar ? (
                            <img
                              src={`data:image/png;base64,${profile.avatar}`}
                              alt={profile.name}
                              className="w-8 h-8 rounded-full"
                            />
                          ) : (
                            <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center text-white text-xs font-semibold">
                              {profile.name.charAt(0).toUpperCase()}
                            </div>
                          )}
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-gray-400" />
                          )}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div
                            className={cn(
                              "truncate font-semibold",
                              isExpanded ? "text-white" : "text-gray-700"
                            )}
                          >
                            {profile.name}
                          </div>
                          {profile.description && (
                            <div className="text-xs text-gray-400 truncate mt-1">
                              {profile.description}
                            </div>
                          )}
                        </div>
                      </div>
                    </Button>
                  </div>

                  {/* Conversations Section - Level 2 */}
                  {isExpanded && (
                    <div className="border-l-[5px] border-gray-800">
                      {/* Conversations Header */}
                      <div className="px-6 py-2 text-xs font-semibold text-gray-600 uppercase tracking-wide border-b border-gray-800">
                        Conversations
                      </div>

                      {profileConversations.length === 0 ? (
                        <div className="text-xs text-gray-500 py-3 px-6 italic">
                          No conversations yet
                        </div>
                      ) : (
                        <div className="space-y-0">
                          {profileConversations.map((conversation) => (
                            <Button
                              key={conversation.id}
                              variant="ghost"
                              className="w-full justify-start text-left text-sm h-auto group px-6 py-2 rounded-none transition-colors text-gray-600 hover:bg-gray-200 hover:text-gray-900 border-b border-gray-100 last:border-b-0"
                              onClick={() => onConversationSelect(conversation.id)}
                            >
                              <div className="flex items-start space-x-2 min-w-0 flex-1">
                                <div
                                  className={cn(
                                    "w-2 h-2 rounded-full mt-2 flex-shrink-0 transition-colors",
                                    selectedConversationId === conversation.id
                                      ? "bg-gray-600"
                                      : "bg-transparent"
                                  )}
                                ></div>
                                <div className="min-w-0 flex-1">
                                  <div className="leading-tight text-gray-600 group-hover:text-gray-900">
                                    {truncateText(conversation.messages[0]?.content)}
                                  </div>
                                  <div className="text-xs text-gray-500 mt-1">
                                    {new Date(conversation.started_at).toLocaleDateString()}
                                  </div>
                                </div>
                              </div>
                            </Button>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
