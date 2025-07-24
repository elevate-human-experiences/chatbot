import { useState, useCallback, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Send,
  Square,
  Bot,
  User as UserIcon,
  ChevronDown,
  ChevronRight,
  ChevronUp,
} from "lucide-react";

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

  // Ref for the scrollable messages container
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [showScrollTopButton, setShowScrollTopButton] = useState(false);

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

  // Show button only if scrollable, with smooth show/hide
  useEffect(() => {
    const container = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    ) as HTMLDivElement;
    if (!container) return;

    const handleScroll = () => {
      setShowScrollTopButton(container.scrollTop > 100);
    };

    const checkScrollable = () => {
      if (!container) return;
      setShowScrollTopButton(
        container.scrollHeight > container.clientHeight && container.scrollTop > 100
      );
    };

    container.addEventListener("scroll", handleScroll);
    checkScrollable();

    return () => {
      container.removeEventListener("scroll", handleScroll);
    };
  }, [messages.length, currentStreamingMessage]);

  // Scroll to bottom when messages grow
  useEffect(() => {
    const container = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    ) as HTMLDivElement;
    if (!container) return;
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, [messages.length, currentStreamingMessage]);

  // Scroll to top handler
  const handleScrollTop = () => {
    const container = scrollAreaRef.current?.querySelector(
      "[data-radix-scroll-area-viewport]"
    ) as HTMLDivElement;
    if (container) {
      container.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const createNewConversation = async () => {
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
          title: "New Conversation",
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
      currentConversationId = await createNewConversation();
      if (currentConversationId && onConversationCreated) {
        onConversationCreated(currentConversationId);
      }
    }

    if (!currentConversationId) {
      console.error("No conversation ID available");
      setIsLoading(false);
      return;
    }

    // Add user message to state first
    setMessages((prev) => [...prev, userMessage]);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      // Send message to conversation endpoint which will handle LLM streaming
      const response = await fetch(
        `${apiBaseUrl}/projects/${projectId}/conversations/${currentConversationId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            role: userMessage.role,
            content: userMessage.content,
          }),
          signal: abortControllerRef.current.signal,
        }
      );

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

                // Handle all choices (most data seems to come through index 0)
                for (const choice of parsed.choices) {
                  const delta = choice.delta;

                  // Handle thinking content
                  if (delta?.thinking) {
                    assistantMessage.thinking = (assistantMessage.thinking || "") + delta.thinking;
                    setCurrentStreamingMessage({ ...assistantMessage });
                  }

                  // Handle reasoning content (alternative field)
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

                  // Handle thinking blocks (structured thinking)
                  if (delta?.thinking_blocks && delta.thinking_blocks.length > 0) {
                    for (const block of delta.thinking_blocks) {
                      if (block.thinking) {
                        assistantMessage.thinking =
                          (assistantMessage.thinking || "") + block.thinking;
                        setCurrentStreamingMessage({ ...assistantMessage });
                      }
                    }
                  }

                  // Handle main response content
                  if (delta?.content) {
                    assistantMessage.content += delta.content;
                    setCurrentStreamingMessage({ ...assistantMessage });
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

      // Add the completed assistant message to the conversation state
      // Note: The backend already saves it to the database, so we just need to update UI
      if (assistantMessage.content || assistantMessage.thinking || assistantMessage.reasoning) {
        setMessages((prev) => [...prev, assistantMessage]);
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

  // Render thinking section for messages
  const renderThinking = (message: Message, isStreaming = false) => {
    const thinkingContent = message.thinking || message.reasoning;
    if (!thinkingContent) return null;

    const expandKey = isStreaming ? "streaming" : message.id;
    const isExpanded = expandedReasoning[expandKey];

    return (
      <div className="mb-4 text-sm">
        <button
          onClick={() =>
            setExpandedReasoning((prev) => ({
              ...prev,
              [expandKey]: !prev[expandKey],
            }))
          }
          className="flex items-center space-x-2 text-muted-foreground hover:text-foreground font-medium transition-colors"
        >
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          <span>💭 {isStreaming ? "Thinking..." : "Thought"}</span>
        </button>
        {isExpanded && (
          <div className="mt-2 p-3 bg-accent rounded border-l-4 border-border">
            <div className="whitespace-pre-wrap text-foreground text-sm font-mono">
              {thinkingContent}
              {isStreaming && (
                <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse"></span>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  // Empty state when no agent profile is selected
  if (!agentProfileId && !conversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center text-muted-foreground max-w-md">
          <Bot className="w-16 h-16 mx-auto mb-4 text-muted" />
          <h2 className="text-xl font-semibold mb-2 text-foreground">Welcome to the Chat</h2>
          <p>Loading your default agent profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-background h-full">
      {/* Header */}
      {agentProfile && (
        <div className="border-b border-border p-4 bg-background flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-foreground" />
              </div>
              <div>
                <h1 className="font-semibold text-foreground">{agentProfile.name}</h1>
                {agentProfile.description && (
                  <p className="text-sm text-muted-foreground">{agentProfile.description}</p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="h-full px-4" ref={scrollAreaRef}>
        <div className="max-w-3xl mx-auto py-6">
          {messages.length === 0 && !currentStreamingMessage && agentProfile && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center mx-auto mb-4">
                <Bot className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Chat with {agentProfile.name}
              </h3>
              <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                {agentProfile.description || "Start a conversation by typing a message below."}
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-md mx-auto">
                <button
                  onClick={() => setInput("Hello! How can you help me today?")}
                  className="p-3 text-left border border-border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="font-medium text-sm text-foreground">Say hello</div>
                  <div className="text-xs text-muted-foreground">Start with a greeting</div>
                </button>
                <button
                  onClick={() => setInput("What can you help me with?")}
                  className="p-3 text-left border border-border rounded-lg hover:bg-accent transition-colors"
                >
                  <div className="font-medium text-sm text-foreground">Get help</div>
                  <div className="text-xs text-muted-foreground">Learn about capabilities</div>
                </button>
              </div>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((message) => (
              <div key={message.id} className="flex space-x-3">
                <div className="flex-shrink-0">
                  {message.role === "user" ? (
                    <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center">
                      <UserIcon className="w-5 h-5 text-secondary-foreground" />
                    </div>
                  ) : (
                    <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-primary-foreground" />
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="bg-muted rounded-lg p-4">
                    {message.role === "assistant" && renderThinking(message, false)}

                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-foreground">{message.content}</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}

            {currentStreamingMessage && (
              <div className="flex space-x-3">
                <div className="flex-shrink-0">
                  <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center">
                    <Bot className="w-5 h-5 text-primary-foreground" />
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="bg-muted rounded-lg p-4">
                    {renderThinking(currentStreamingMessage, true)}

                    <div className="prose prose-sm max-w-none">
                      <div className="whitespace-pre-wrap text-foreground">
                        {currentStreamingMessage.content}
                        {currentStreamingMessage.content && (
                          <span className="inline-block w-2 h-5 bg-muted-foreground ml-1 animate-pulse"></span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </ScrollArea>

      {/* Scroll to top button */}
      <div
        className={`fixed bottom-24 right-6 transition-opacity duration-300 ${
          showScrollTopButton ? "opacity-100 pointer-events-auto" : "opacity-0 pointer-events-none"
        }`}
      >
        <button
          className="bg-muted hover:bg-accent text-muted-foreground rounded-full w-9 h-9 flex items-center justify-center transition-all duration-300 cursor-pointer shadow-lg"
          type="button"
          onClick={handleScrollTop}
          aria-label="Scroll to top"
        >
          <ChevronUp className="w-5 h-5" />
        </button>
      </div>

      {/* Input */}
      <div className="border-t border-border bg-background flex-shrink-0">
        <div className="max-w-3xl mx-auto p-4">
          <div className="flex items-end space-x-3">
            <div className="flex-1 relative">
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                  }
                }}
                placeholder={getPlaceholder()}
                disabled={isLoading || !agentProfileId}
                className="min-h-[52px] max-h-[120px] resize-none border-border focus:border-ring focus:ring-ring rounded-lg pr-12"
                rows={1}
              />
              <div className="absolute right-3 bottom-3">
                {isLoading ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={stopGeneration}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-destructive"
                  >
                    <Square className="w-4 h-4" />
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={sendMessage}
                    disabled={!input.trim() || !agentProfileId}
                    className="h-8 w-8 p-0 text-muted-foreground hover:text-primary disabled:text-muted-foreground/50"
                  >
                    <Send className="w-4 h-4" />
                  </Button>
                )}
              </div>
            </div>
          </div>
          <div className="mt-2 text-xs text-muted-foreground text-center">
            Press Enter to send, Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  );
}
