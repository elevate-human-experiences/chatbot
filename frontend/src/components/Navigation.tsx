import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function Navigation() {
  const location = useLocation();

  const navItems = [
    { path: "/", label: "Chat" },
    { path: "/about", label: "About" },
    { path: "/settings", label: "Settings" },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-2">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-1">
          <h1 className="text-xl font-bold text-gray-900 mr-6">Claude Chat</h1>
          {navItems.map((item) => (
            <Button
              key={item.path}
              variant={location.pathname === item.path ? "default" : "outline"}
              size="sm"
              asChild
              className={cn(
                "transition-colors",
                location.pathname === item.path
                  ? "bg-blue-500 hover:bg-blue-600"
                  : "hover:bg-gray-50"
              )}
            >
              <Link to={item.path}>{item.label}</Link>
            </Button>
          ))}
        </div>
      </div>
    </nav>
  );
}
