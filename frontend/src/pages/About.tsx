import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function About() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto p-4">
        <Card className="flex-1 border-neutral-50 bg-stone-50">
          <CardHeader>
            <CardTitle className="text-center">About Claude Reasoning Chat</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="prose max-w-none">
              <p className="text-lg text-gray-700">
                This is a modern chat interface built with React and TypeScript that connects to
                Claude's advanced reasoning model. The application demonstrates real-time streaming
                responses with thinking and reasoning processes.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-3">Features</h3>
              <ul className="space-y-2 text-gray-700">
                <li>• Real-time streaming chat responses</li>
                <li>• Visible thinking and reasoning processes</li>
                <li>• Modern, responsive UI with shadcn/ui components</li>
                <li>• Built with React 19 and TypeScript</li>
                <li>• Falcon backend with Python</li>
              </ul>

              <h3 className="text-xl font-semibold mt-6 mb-3">Technology Stack</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold">Frontend</h4>
                  <ul className="text-sm text-gray-600 mt-1">
                    <li>• React 19</li>
                    <li>• TypeScript</li>
                    <li>• Vite</li>
                    <li>• shadcn/ui</li>
                    <li>• Tailwind CSS</li>
                    <li>• React Router</li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold">Backend</h4>
                  <ul className="text-sm text-gray-600 mt-1">
                    <li>• Python 3.12</li>
                    <li>• Falcon framework</li>
                    <li>• Uvicorn ASGI server</li>
                    <li>• LiteLLM integration</li>
                    <li>• MongoDB & Redis</li>
                  </ul>
                </div>
              </div>
            </div>

            <div className="flex justify-center pt-6">
              <Button asChild className="bg-stone-500 hover:bg-stone-600 text-white">
                <Link to="/">Start Chatting</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
