import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { MessageCircle, Info, Settings as SettingsIcon } from "lucide-react";

export function Navigation() {
  const location = useLocation();

  const navItems = [
    {
      path: "/",
      label: "Chat",
      icon: MessageCircle,
    },
    {
      path: "/about",
      label: "About",
      icon: Info,
    },
    {
      path: "/settings",
      label: "Settings",
      icon: SettingsIcon,
    },
  ];

  return (
    <nav className="bg-white border-b border-gray-200 px-4 py-4">
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex justify-center">
          <h1 className="font-bold text-gray-900 flex items-center gap-1">
            <span className="text-lg pt-1">Claude Chat</span>
          </h1>
        </div>
        <div className="flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                variant={isActive ? "default" : "outline"}
                size="sm"
                asChild
                className={cn(
                  "transition-colors relative group p-2",
                  isActive ? "bg-blue-500 hover:bg-blue-600" : "hover:bg-gray-50"
                )}
              >
                <Link to={item.path}>
                  <Icon className="w-5 h-5" />
                  <span className="absolute left-1/2 -translate-x-1/2 top-full mt-2 px-2 py-1 rounded bg-gray-900 text-white text-xs opacity-0 group-hover:opacity-100 pointer-events-none whitespace-nowrap z-10 transition-opacity">
                    {item.label}
                  </span>
                </Link>
              </Button>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
