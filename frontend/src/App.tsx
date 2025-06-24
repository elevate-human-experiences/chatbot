import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import "./App.css";

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
    delta: {
      content?: string;
      thinking?: string;
      reasoning?: string;
      role?: string;
    };
    finish_reason?: string;
  }>;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<Message | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages, currentStreamingMessage]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Create abort controller for this request
    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch("http://localhost:8080/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [
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
      let assistantMessage: Message = {
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
                setMessages((prev) => [...prev, assistantMessage]);
                setCurrentStreamingMessage(null);
                return;
              }

              try {
                const parsed: StreamChunk = JSON.parse(data);
                const delta = parsed.choices[0]?.delta;

                if (delta?.content) {
                  assistantMessage = {
                    ...assistantMessage,
                    content: assistantMessage.content + delta.content,
                  };
                }

                if (delta?.thinking) {
                  assistantMessage = {
                    ...assistantMessage,
                    thinking: (assistantMessage.thinking || "") + delta.thinking,
                  };
                }

                if (delta?.reasoning) {
                  assistantMessage = {
                    ...assistantMessage,
                    reasoning: (assistantMessage.reasoning || "") + delta.reasoning,
                  };
                }

                setCurrentStreamingMessage({ ...assistantMessage });

                if (parsed.choices[0]?.finish_reason) {
                  setMessages((prev) => [...prev, assistantMessage]);
                  setCurrentStreamingMessage(null);
                  return;
                }
              } catch {
                console.warn("Failed to parse chunk:", data);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
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

  return (
    <div className="flex min-h-screen bg-gray-50">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto p-4">
        <Card className="flex-1 flex flex-col">
          <CardHeader>
            <CardTitle className="text-center">Claude Reasoning Chat</CardTitle>
            <p className="text-center text-sm text-gray-600">
              Chat with Claude's advanced reasoning model
            </p>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col">
            <ScrollArea ref={scrollAreaRef} className="flex-1 p-4 border rounded-lg">
              <div className="space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg ${
                        message.role === "user"
                          ? "bg-blue-500 text-white"
                          : "bg-gray-200 text-gray-900"
                      }`}
                    >
                      <div className="whitespace-pre-wrap">{message.content}</div>
                      {message.thinking && (
                        <details className="mt-2 text-xs opacity-70">
                          <summary className="cursor-pointer">🤔 Thinking Process</summary>
                          <div className="mt-2 whitespace-pre-wrap">{message.thinking}</div>
                        </details>
                      )}
                      {message.reasoning && (
                        <details className="mt-2 text-xs opacity-70">
                          <summary className="cursor-pointer">💭 Reasoning</summary>
                          <div className="mt-2 whitespace-pre-wrap">{message.reasoning}</div>
                        </details>
                      )}
                      <div className="text-xs opacity-50 mt-1">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}

                {currentStreamingMessage && (
                  <div className="flex justify-start">
                    <div className="max-w-[80%] p-3 rounded-lg bg-gray-200 text-gray-900">
                      <div className="whitespace-pre-wrap">
                        {currentStreamingMessage.content}
                        <span className="animate-pulse">▋</span>
                      </div>
                      {currentStreamingMessage.thinking && (
                        <details className="mt-2 text-xs opacity-70">
                          <summary className="cursor-pointer">🤔 Thinking Process</summary>
                          <div className="mt-2 whitespace-pre-wrap">
                            {currentStreamingMessage.thinking}
                          </div>
                        </details>
                      )}
                      {currentStreamingMessage.reasoning && (
                        <details className="mt-2 text-xs opacity-70">
                          <summary className="cursor-pointer">💭 Reasoning</summary>
                          <div className="mt-2 whitespace-pre-wrap">
                            {currentStreamingMessage.reasoning}
                          </div>
                        </details>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </ScrollArea>

            <div className="flex gap-2 mt-4">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Claude anything..."
                disabled={isLoading}
                className="flex-1"
              />
              {isLoading ? (
                <Button onClick={stopGeneration} variant="destructive">
                  Stop
                </Button>
              ) : (
                <Button onClick={sendMessage} disabled={!input.trim()}>
                  Send
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default App;
