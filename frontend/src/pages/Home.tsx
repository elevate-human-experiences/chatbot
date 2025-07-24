import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

interface User {
  id: string;
  name: string;
  email: string;
  created_at: string;
}

interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
}

interface AgentProfile {
  id: string;
  name: string;
  description?: string;
  instructions: string[];
  created_at: string;
}

interface Conversation {
  id: string;
  title?: string;
  project_id?: string;
  user_id?: string;
  agent_profile_id: string;
  started_at: string;
  messages: Array<{
    role: "user" | "assistant" | "system" | "tool";
    content?: string;
  }>;
}

export function Home() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [agentProfiles, setAgentProfiles] = useState<AgentProfile[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [newUserName, setNewUserName] = useState("");
  const [newUserEmail, setNewUserEmail] = useState("");

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  const loadUserData = useCallback(
    async (userId: string) => {
      try {
        // Load projects for this user
        const projectsResponse = await fetch(`${apiBaseUrl}/projects?user_id=${userId}`);
        if (projectsResponse.ok) {
          const projectsResponseData = await projectsResponse.json();
          const projectsData = projectsResponseData.projects || [];
          setProjects(projectsData);

          // Get the first project as default
          const firstProject = projectsData[0];
          if (firstProject) {
            // Load agent profiles for the first project using project-scoped API
            const agentProfilesResponse = await fetch(
              `${apiBaseUrl}/projects/${firstProject.id}/profiles`
            );
            if (agentProfilesResponse.ok) {
              const agentProfilesResponseData = await agentProfilesResponse.json();
              const agentProfilesData = agentProfilesResponseData.profiles || [];
              setAgentProfiles(agentProfilesData);
            }

            // Load conversations for the first project using project-scoped API
            const conversationsResponse = await fetch(
              `${apiBaseUrl}/projects/${firstProject.id}/conversations`
            );
            if (conversationsResponse.ok) {
              const conversationsResponseData = await conversationsResponse.json();
              const conversationsData = conversationsResponseData.conversations || [];
              setConversations(conversationsData);
            }

            // Navigate to the chat page with the first project
            navigate(`/projects/${firstProject.id}/agent`);
          }
        }
      } catch (err) {
        console.error("Error loading user data:", err);
        setError(err instanceof Error ? err.message : "Failed to load user data");
      }
    },
    [apiBaseUrl, navigate]
  );

  const initializeUser = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Check localStorage for existing user UUID
      const userId = localStorage.getItem("chatbot_user_id");

      if (userId) {
        // Try to fetch existing user
        const userResponse = await fetch(`${apiBaseUrl}/users/${userId}`);

        if (userResponse.ok) {
          const userData = await userResponse.json();
          setUser(userData);
          await loadUserData(userId);
        } else if (userResponse.status === 404) {
          // User not found, clear localStorage and show create form
          localStorage.removeItem("chatbot_user_id");
          setShowCreateUser(true);
        } else {
          throw new Error(`Failed to fetch user: ${userResponse.statusText}`);
        }
      } else {
        // No user ID in localStorage, show create form
        setShowCreateUser(true);
      }
    } catch (err) {
      console.error("Error initializing user:", err);
      setError(err instanceof Error ? err.message : "Failed to initialize user");
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl, loadUserData]);

  useEffect(() => {
    initializeUser();
  }, [initializeUser]);

  const createUser = async () => {
    if (!newUserName.trim() || !newUserEmail.trim()) {
      setError("Please enter both name and email");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${apiBaseUrl}/users`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: newUserName.trim(),
          email: newUserEmail.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create user: ${response.statusText}`);
      }

      const userData = await response.json();

      // Store user ID in localStorage
      localStorage.setItem("chatbot_user_id", userData.id);
      setUser(userData);
      setShowCreateUser(false);

      // Load user data (projects, agent profiles, conversations)
      await loadUserData(userData.id);
    } catch (err) {
      console.error("Error creating user:", err);
      setError(err instanceof Error ? err.message : "Failed to create user");
    } finally {
      setLoading(false);
    }
  };

  const handleStartOver = () => {
    localStorage.removeItem("chatbot_user_id");
    setUser(null);
    setProjects([]);
    setAgentProfiles([]);
    setConversations([]);
    setShowCreateUser(true);
    setNewUserName("");
    setNewUserEmail("");
    setError(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Card className="w-[400px] border-neutral-50 bg-gray-50">
          <CardContent className="p-6">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Initializing...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (showCreateUser) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <Card className="w-[400px] border-border bg-background">
          <CardHeader>
            <CardTitle>Welcome to ChatBot</CardTitle>
            <p className="text-sm text-muted-foreground">Let's get you set up with an account</p>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive rounded">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Full Name
              </label>
              <Input
                id="name"
                placeholder="Enter your full name"
                value={newUserName}
                onChange={(e) => setNewUserName(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="Enter your email address"
                value={newUserEmail}
                onChange={(e) => setNewUserEmail(e.target.value)}
                disabled={loading}
              />
            </div>
            <Button
              onClick={createUser}
              className="w-full"
              disabled={loading || !newUserName.trim() || !newUserEmail.trim()}
            >
              {loading ? "Creating Account..." : "Create Account"}
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center h-screen bg-background">
      <Card className="w-[500px] border-border bg-background">
        <CardHeader>
          <CardTitle>Welcome back, {user?.name}!</CardTitle>
          <p className="text-sm text-muted-foreground">We're setting up your workspace...</p>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 border border-destructive rounded">
              {error}
            </div>
          )}
          hi
          <div className="space-y-2">
            <p>
              <strong>Projects:</strong> {projects.length}
            </p>
            <p>
              <strong>Agent Profiles:</strong> {agentProfiles.length}
            </p>
            <p>
              <strong>Conversations:</strong> {conversations.length}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => user && loadUserData(user.id)}
              className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground"
              disabled={!user}
            >
              Continue to Chat
            </Button>
            <Button onClick={handleStartOver} variant="outline">
              Start Over
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
