import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { MessageSquare, User, ChevronRight, ChevronDown } from "lucide-react";

interface User {
  id: string;
  name: string;
  email: string;
}

interface AgentProfile {
  id: string;
  name: string;
  description?: string;
  instructions?: string[];
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
}

export function Sidebar({
  selectedConversationId,
  onConversationSelect,
  onNewConversation,
  projectId,
  refreshKey,
}: SidebarProps) {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [agentProfiles, setAgentProfiles] = useState<AgentProfile[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [expandedProfiles, setExpandedProfiles] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  // Load expansion state from localStorage
  const getStorageKey = useCallback(
    (projectId: string) => `chatbot_expanded_profiles_${projectId}`,
    []
  );

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

      // Load user info
      const userResponse = await fetch(`${apiBaseUrl}/users/${userId}`);
      if (userResponse.ok) {
        const userData = await userResponse.json();
        setCurrentUser(userData);
      }

      // Load agent profiles - use project-scoped API
      if (projectId) {
        const profilesUrl = `${apiBaseUrl}/projects/${projectId}/profiles`;
        const profilesResponse = await fetch(profilesUrl);
        if (profilesResponse.ok) {
          const profilesResponseData = await profilesResponse.json();
          const profilesData = profilesResponseData.agent_profiles || [];
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
      <div className="w-80 bg-gray-900 text-white border-r border-gray-700 p-4">
        <div className="text-center text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="w-80 bg-gray-900 text-white border-r border-gray-700 flex flex-col h-full min-h-0 overflow-hidden">
      {/* Current User Section */}
      <div className="fixed p-4 border-b border-gray-700 z-0 bg-gray-800 w-80 flex-shrink-0">
        <div className="flex items-center space-x-3 p-3 rounded-lg bg-gray-800">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-white" />
          </div>
          <div className="min-w-0 flex-1">
            {currentUser ? (
              <>
                <div className="font-medium text-sm text-white truncate">{currentUser.name}</div>
                <div className="text-xs text-gray-400 truncate">{currentUser.email}</div>
              </>
            ) : (
              <div className="text-xs text-gray-400">No user logged in</div>
            )}
          </div>
        </div>
      </div>

      {/* Agent Profiles and Conversations */}
      <div className="mt-20 flex-1 min-h-0 p-4 overflow-x-hidden">
        <div className="space-y-2">
          {agentProfiles.length === 0 ? (
            <div className="text-center text-gray-400 text-sm py-8">No agent profiles found</div>
          ) : (
            agentProfiles.map((profile) => {
              const profileConversations = getConversationsForProfile(profile.id);
              const isExpanded = expandedProfiles.has(profile.id);

              return (
                <div key={profile.id} className="space-y-1">
                  {/* Agent Profile Header */}
                  <div className="flex items-center group">
                    <Button
                      variant="ghost"
                      className="flex-1 justify-start text-left font-medium text-sm p-3 h-auto text-white hover:bg-gray-800 rounded-lg"
                      onClick={() => {
                        toggleProfileExpansion(profile.id);
                        // Auto-start new conversation when clicking on agent profile
                        onNewConversation(profile.id);
                      }}
                    >
                      <div className="flex items-center space-x-2 min-w-0 flex-1">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-gray-400" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-gray-400" />
                        )}
                        <div className="min-w-0 flex-1">
                          <div className="truncate text-white">{profile.name}</div>
                          {profile.description && (
                            <div className="text-xs text-gray-400 truncate">
                              {profile.description}
                            </div>
                          )}
                        </div>
                      </div>
                    </Button>
                  </div>

                  {/* Conversations for this profile */}
                  {isExpanded && (
                    <div className="ml-6 space-y-1">
                      {profileConversations.length === 0 ? (
                        <div className="text-xs text-gray-500 py-2 px-3">No conversations yet</div>
                      ) : (
                        profileConversations.map((conversation) => (
                          <Button
                            key={conversation.id}
                            variant="ghost"
                            className={cn(
                              "w-full justify-start text-left text-sm p-3 h-auto rounded-lg group",
                              selectedConversationId === conversation.id
                                ? "bg-gray-800 text-white"
                                : "text-gray-300 hover:bg-gray-800 hover:text-white"
                            )}
                            onClick={() => onConversationSelect(conversation.id)}
                          >
                            <div className="flex items-center space-x-2 min-w-0 flex-1">
                              <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
                              <div className="min-w-0 flex-1">
                                <div className="truncate">{getConversationTitle(conversation)}</div>
                                <div className="text-xs text-gray-500">
                                  {new Date(conversation.started_at).toLocaleDateString()}
                                </div>
                              </div>
                            </div>
                          </Button>
                        ))
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
