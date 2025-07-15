import { useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

interface AgentProfile {
  id: string;
  name: string;
  description?: string;
  instructions?: string[];
}

interface SidebarProps {
  onNewConversation: (agentProfileId: string) => void;
  projectId?: string;
  refreshKey?: number;
  hideDetails?: boolean;
}

export function NewChat({ onNewConversation, projectId, refreshKey, hideDetails }: SidebarProps) {
  const [agentProfiles, setAgentProfiles] = useState<AgentProfile[]>([]);
  const [loading, setLoading] = useState(true);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const userId = localStorage.getItem("chatbot_user_id");
      if (!userId) {
        console.error("No user ID found in localStorage");
        return;
      }
      if (projectId) {
        const profilesUrl = `${apiBaseUrl}/projects/${projectId}/profiles`;
        const profilesResponse = await fetch(profilesUrl);
        if (profilesResponse.ok) {
          const profilesResponseData = await profilesResponse.json();
          const profilesData = profilesResponseData.agent_profiles || [];
          setAgentProfiles(Array.isArray(profilesData) ? profilesData : []);
        } else {
          console.error("Failed to load agent profiles:", profilesResponse.statusText);
          setAgentProfiles([]);
        }
      } else {
        setAgentProfiles([]);
      }
    } catch (error) {
      console.error("Error loading sidebar data:", error);
    } finally {
      setLoading(false);
    }
  }, [projectId, apiBaseUrl]);

  useEffect(() => {
    loadData();
  }, [projectId, refreshKey, loadData]);

  if (loading) {
    return (
      <div className="w-80 text-white border-r border-gray-700 p-4">
        <div className="text-center text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div className="">
      {agentProfiles.length === 0 ? (
        <div className="text-center text-gray-400 text-sm">No agent profiles found</div>
      ) : (
        agentProfiles.map((profile) => (
          <div key={profile.id} className="w-full flex items-center justify-center p-2">
            <Button
              className="w-[99%] bg-stone-200 text-stone-800 hover:bg-stone-300 font-medium px-4  transition-colors cursor-pointer flex items-center gap-2"
              onClick={() => onNewConversation(profile.id)}
            >
              {hideDetails && <Plus className="w-4 h-4 mr-1" />}
              {!hideDetails && "New chat"}
            </Button>
          </div>
        ))
      )}
    </div>
  );
}
