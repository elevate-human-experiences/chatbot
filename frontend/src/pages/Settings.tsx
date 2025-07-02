import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

export function Settings() {
  return (
    <div className="flex items-center justify-center h-screen">
      <div className="flex-1 flex flex-col max-w-4xl mx-auto p-4">
        <Card className="flex-1">
          <CardHeader>
            <CardTitle className="text-center">Settings</CardTitle>
            <p className="text-center text-sm text-gray-600">Configure your chat preferences</p>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold mb-3">Chat Configuration</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Model</label>
                    <select className="border rounded px-3 py-1 text-sm">
                      <option>anthropic/claude-sonnet-4-20250514</option>
                      <option>gpt-4o</option>
                      <option>gpt-4o-mini</option>
                    </select>
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Temperature</label>
                    <input
                      type="range"
                      min="0"
                      max="2"
                      step="0.1"
                      defaultValue="1.0"
                      className="w-32"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Reasoning Effort</label>
                    <select className="border rounded px-3 py-1 text-sm">
                      <option>low</option>
                      <option selected>medium</option>
                      <option>high</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Display Preferences</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Show Thinking Process</label>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Show Reasoning</label>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Auto-scroll</label>
                    <input type="checkbox" defaultChecked className="rounded" />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-6">
              <Button variant="outline" asChild>
                <Link to="/">Back to Chat</Link>
              </Button>
              <Button>Save Settings</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
