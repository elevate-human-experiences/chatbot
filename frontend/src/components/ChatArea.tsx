import { useState, useRef, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Textarea } from "@/components/ui/textarea";
import { Send, Square, Bot, User as UserIcon, ChevronDown, ChevronRight } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  thinking?: string;
  reasoning?: string;
  timestamp: Date;
}

interface StreamChunk {
  choices: Array<{
    index?: number;
    delta: {
      content?: string;
      thinking?: string;
      reasoning?: string;
      reasoning_content?: string;
      thinking_blocks?: Array<{
        type: string;
        thinking: string;
        signature?: string;
      }>;
      role?: string;
    };
    finish_reason?: string;
  }>;
}

interface ChatAreaProps {
  conversationId?: string;
  agentProfileId?: string;
  onConversationCreated?: (conversationId: string) => void;
  onNewChat?: () => void; // Add this prop
  projectId?: string;
}

export function ChatArea({
  conversationId,
  agentProfileId,
  onConversationCreated,
  onNewChat: _onNewChat, // Reserved for future "New Chat" functionality
  projectId,
}: ChatAreaProps) {
  // Fake usage to silence TypeScript warning - reserved for future functionality
  void _onNewChat;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<Message | null>(null);
  const [agentProfile, setAgentProfile] = useState<{
    id: string;
    name: string;
    description?: string;
    instructions?: string[];
  } | null>(null);
  const [expandedReasoning, setExpandedReasoning] = useState<{ [key: string]: boolean }>({});
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

  const loadConversation = useCallback(async () => {
    if (!conversationId || !projectId) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/projects/${projectId}/conversations/${conversationId}`
      );
      if (response.ok) {
        const conversation = await response.json();
        if (conversation.messages) {
          // Clear existing messages to avoid duplicates
          setMessages([]);
          setExpandedReasoning({});

          const formattedMessages: Message[] = conversation.messages.map(
            (
              msg: {
                role: "user" | "assistant";
                content: string;
                thinking?: string;
                reasoning?: string;
                timestamp?: string | number;
              },
              index: number
            ) => ({
              id: `${msg.role}-${index}-${msg.timestamp || Date.now()}`,
              role: msg.role,
              content: msg.content,
              thinking: msg.thinking,
              reasoning: msg.reasoning,
              timestamp: new Date(msg.timestamp || Date.now()),
            })
          );

          // Remove any potential duplicates based on content and timestamp
          const uniqueMessages = formattedMessages.filter(
            (message, index, arr) =>
              index ===
              arr.findIndex(
                (m) =>
                  m.role === message.role &&
                  m.content === message.content &&
                  Math.abs(m.timestamp.getTime() - message.timestamp.getTime()) < 1000 // within 1 second
              )
          );

          setMessages(uniqueMessages);
        }
      }
    } catch (error) {
      console.error("Error loading conversation:", error);
    }
  }, [conversationId, projectId, apiBaseUrl]);

  const loadAgentProfile = useCallback(async () => {
    if (!agentProfileId || !projectId) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/projects/${projectId}/profiles/${agentProfileId}`
      );
      if (response.ok) {
        const profile = await response.json();
        setAgentProfile(profile);
      }
    } catch (error) {
      console.error("Error loading agent profile:", error);
    }
  }, [agentProfileId, projectId, apiBaseUrl]);

  // Load conversation messages when conversationId or projectId changes
  useEffect(() => {
    if (conversationId && projectId) {
      loadConversation();
    } else {
      setMessages([]);
      setExpandedReasoning({});
    }
  }, [conversationId, projectId, loadConversation]);

  // Load agent profile when agentProfileId or projectId changes
  useEffect(() => {
    if (agentProfileId && projectId) {
      loadAgentProfile();
    }
  }, [agentProfileId, projectId, loadAgentProfile]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + "px";
    }
  }, [input]);

  const createNewConversation = async (firstMessage: Message) => {
    if (!agentProfileId || !projectId) return null;

    try {
      // Get user ID from localStorage
      const userId = localStorage.getItem("chatbot_user_id");

      const response = await fetch(`${apiBaseUrl}/projects/${projectId}/conversations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_profile_id: agentProfileId,
          user_id: userId,
          title:
            firstMessage.content.slice(0, 50) + (firstMessage.content.length > 50 ? "..." : ""),
          messages: [
            {
              role: firstMessage.role,
              content: firstMessage.content,
              timestamp: firstMessage.timestamp.toISOString(),
            },
          ],
        }),
      });

      if (response.ok) {
        const newConversation = await response.json();
        return newConversation.id;
      }
    } catch (error) {
      console.error("Error creating conversation:", error);
    }
    return null;
  };

  const addMessageToConversation = async (conversationId: string, message: Message) => {
    if (!projectId) return;

    try {
      await fetch(`${apiBaseUrl}/projects/${projectId}/conversations/${conversationId}/messages`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          role: message.role,
          content: message.content,
          thinking: message.thinking,
          reasoning: message.reasoning,
          timestamp: message.timestamp.toISOString(),
        }),
      });
    } catch (error) {
      console.error("Error adding message to conversation:", error);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setInput("");
    setIsLoading(true);

    // Create conversation if this is the first message and we have an agent profile
    let currentConversationId = conversationId;
    if (!currentConversationId && agentProfileId) {
      // Add user message to state first
      setMessages((prev) => [...prev, userMessage]);

      currentConversationId = await createNewConversation(userMessage);
      if (currentConversationId && onConversationCreated) {
        onConversationCreated(currentConversationId);
      }
    } else {
      // Add user message to state
      setMessages((prev) => [...prev, userMessage]);

      // Add user message to existing conversation
      if (currentConversationId) {
        try {
          await addMessageToConversation(currentConversationId, userMessage);
        } catch (error) {
          console.error("Error saving user message:", error);
        }
      }
    }

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      // Prepare system message from agent profile instructions
      const systemMessages = [];
      if (agentProfile?.instructions && agentProfile.instructions.length > 0) {
        systemMessages.push({
          role: "system",
          content: agentProfile.instructions.join("\n\n"),
        });
      }

      const response = await fetch(`${apiBaseUrl}/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [
            ...systemMessages,
            ...messages.map((m) => ({ role: m.role, content: m.content })),
            { role: userMessage.role, content: userMessage.content },
          ],
          model: "anthropic/claude-sonnet-4-20250514",
          stream: true,
          reasoning_effort: "medium",
          thinking: { type: "enabled", budget_tokens: 2048 },
          temperature: 1.0,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("No reader available");
      }

      const decoder = new TextDecoder();
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: "",
        thinking: "",
        reasoning: "",
        timestamp: new Date(),
      };

      setCurrentStreamingMessage(assistantMessage);

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") {
                break;
              }
              try {
                const parsed: StreamChunk = JSON.parse(data);

                // Handle multiple streams by index
                for (const choice of parsed.choices) {
                  const delta = choice.delta;
                  const index = choice.index || 0;

                  // Index 0 is typically thinking/reasoning
                  if (index === 0) {
                    // Handle reasoning content
                    if (delta?.reasoning_content) {
                      assistantMessage.reasoning =
                        (assistantMessage.reasoning || "") + delta.reasoning_content;
                      setCurrentStreamingMessage({ ...assistantMessage });
                    }
                    if (delta?.reasoning) {
                      assistantMessage.reasoning =
                        (assistantMessage.reasoning || "") + delta.reasoning;
                      setCurrentStreamingMessage({ ...assistantMessage });
                    }

                    // Handle thinking blocks
                    if (delta?.thinking_blocks && delta.thinking_blocks.length > 0) {
                      for (const block of delta.thinking_blocks) {
                        if (block.thinking) {
                          assistantMessage.thinking =
                            (assistantMessage.thinking || "") + block.thinking;
                          setCurrentStreamingMessage({ ...assistantMessage });
                        }
                      }
                    }
                    if (delta?.thinking) {
                      assistantMessage.thinking =
                        (assistantMessage.thinking || "") + delta.thinking;
                      setCurrentStreamingMessage({ ...assistantMessage });
                    }

                    // Sometimes content comes through index 0 as well (fallback)
                    if (delta?.content && !assistantMessage.content) {
                      assistantMessage.thinking = (assistantMessage.thinking || "") + delta.content;
                      setCurrentStreamingMessage({ ...assistantMessage });
                    }
                  }

                  // Index 1 is typically the main assistant response
                  if (index === 1) {
                    if (delta?.content) {
                      assistantMessage.content += delta.content;
                      setCurrentStreamingMessage({ ...assistantMessage });
                    }
                  }

                  if (choice?.finish_reason) {
                    break;
                  }
                }
              } catch (parseError) {
                console.error("Error parsing SSE data:", parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      // Add the completed assistant message to the conversation
      if (assistantMessage.content || assistantMessage.thinking || assistantMessage.reasoning) {
        setMessages((prev) => [...prev, assistantMessage]);

        // Save assistant message to conversation after streaming is complete
        if (currentConversationId) {
          try {
            await addMessageToConversation(currentConversationId, assistantMessage);
          } catch (error) {
            console.error("Error saving assistant message:", error);
          }
        }
      }

      setCurrentStreamingMessage(null);
    } catch (error: unknown) {
      if (error instanceof Error && error.name === "AbortError") {
        console.log("Request was aborted");
      } else {
        console.error("Error sending message:", error);
        const errorMessage: Message = {
          id: `error-${Date.now()}`,
          role: "assistant",
          content: `Error: ${error instanceof Error ? error.message : "Unknown error occurred"}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
      setCurrentStreamingMessage(null);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const getPlaceholder = () => {
    if (agentProfile) {
      return `Message ${agentProfile.name}...`;
    }
    return "Select an agent profile to start chatting...";
  };

  // Empty state when no agent profile is selected
  if (!agentProfileId && !conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white">
        <div className="text-center text-gray-500 max-w-md">
          <Bot className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <h2 className="text-xl font-semibold mb-2">Welcome to the Chat</h2>
          <p>Loading your default agent profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white h-[95vh]">
      {/* Header */}
      {agentProfile && (
        <div className="relative border-gray-200 p-4 bg-white flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900">{agentProfile.name}</h1>
                {agentProfile.description && (
                  <p className="text-sm text-gray-500">{agentProfile.description}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 px-4 inset-0 z-0" style={{ height: "auto" }}>
        <div className="max-w-3xl mx-auto pt-3 pb-32 mb-32">
          {messages.length === 0 && !currentStreamingMessage && agentProfile && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-purple-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Chat with {agentProfile.name}
              </h3>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                {agentProfile.description || "Start a conversation by typing a message below."}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-md mx-auto">
                <button
                  onClick={() => setInput("Hello! How can you help me today?")}
                  className="p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="font-medium text-sm text-gray-900">Say hello</div>
                  <div className="text-xs text-gray-500">Start with a greeting</div>
                </button>
                <button
                  onClick={() => setInput("What can you help me with?")}
                  className="p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="font-medium text-sm text-gray-900">Get help</div>
                  <div className="text-xs text-gray-500">Learn about capabilities</div>
                </button>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="flex space-x-3">
                <div className="flex-shrink-0">
                  {message.role === "user" ? (
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <UserIcon className="w-5 h-5 text-white" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="bg-gray-50 rounded-lg p-4">
                    {message.reasoning && (
                      <div className="mb-4 text-sm">
                        <button
                          onClick={() =>
                            setExpandedReasoning((prev) => ({
                              ...prev,
                              [message.id]: !prev[message.id],
                            }))
                          }
                          className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
                        >
                          {expandedReasoning[message.id] ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          <span>💭 thinking</span>
                        </button>
                        {expandedReasoning[message.id] && (
                          <div className="mt-2 p-3 bg-blue-50 rounded border-l-4 border-blue-200">
                            <div className="whitespace-pre-wrap text-gray-700">
                              {message.reasoning}
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap">{message.content}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {currentStreamingMessage && (
              <div className="flex space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-purple-600 rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="bg-gray-50 rounded-lg p-4">
                    {currentStreamingMessage.reasoning && (
                      <div className="mb-4 text-sm">
                        <button
                          onClick={() =>
                            setExpandedReasoning((prev) => ({
                              ...prev,
                              ["streaming"]: !prev["streaming"],
                            }))
                          }
                          className="flex items-center space-x-2 text-gray-600 hover:text-gray-800 font-medium transition-colors"
                        >
                          {expandedReasoning["streaming"] ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          <span>💭 thinking in progress...</span>
                        </button>
                        {expandedReasoning["streaming"] && (
                          <div className="mt-2 p-3 bg-blue-50 rounded border-l-4 border-blue-200">
                            <div className="whitespace-pre-wrap text-gray-700">
                              {currentStreamingMessage.reasoning}
                              <span className="inline-block w-2 h-4 bg-blue-400 ml-1 animate-pulse"></span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap">
                        {currentStreamingMessage.content}
                        <span className="inline-block w-2 h-5 bg-gray-400 ml-1 animate-pulse"></span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </ScrollArea>
      {/* Input */}
      <div className="z-10 w-full flex justify-center fixed bottom-0 left-0 bg-transparent">
        <div
          className="p-5 bg-white rounded-t-lg"
          style={{
            width: "100%",
            maxWidth: "520px", // Menos de la mitad de la pantalla típica
            marginLeft: "280px",
          }}
        >
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={getPlaceholder()}
                disabled={isLoading || !agentProfileId}
                className="min-h-[52px] max-h-[120px] resize-none border-gray-300 focus:border-blue-500 focus:ring-blue-500 rounded-lg pr-12 w-full"
                rows={1}
              />
              <div className="absolute right-3 bottom-3">
                {isLoading ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={stopGeneration}
                    className="h-8 w-8 p-0 text-gray-500 hover:text-red-600"
                  >
                    <Square className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={sendMessage}
                    disabled={!input.trim() || !agentProfileId}
                    className="h-8 w-8 p-0 text-gray-500 hover:text-blue-600 disabled:text-gray-300"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 text-center">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
}
