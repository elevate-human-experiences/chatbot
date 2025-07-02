import { Outlet, useLocation, Link } from "react-router-dom";

import { cn } from "@/lib/utils";

import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageCircle, Info, Settings } from "lucide-react";

export function Layout() {
  const location = useLocation();

  const [sidebarVisible, setSidebarVisible] = useState(true);

  // Don't show navigation on the home page (chat interface)
  const showNavigation = location.pathname !== "/";

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
      icon: Settings,
    },
  ];

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {showNavigation && (
        <div
          className={`bg-gray-100 border-r border-gray-200 transition-all duration-200`}
          style={{
            width: sidebarVisible ? "10%" : "80px",
            minWidth: sidebarVisible ? "10px" : "80px",
            maxWidth: sidebarVisible ? undefined : "50px",
            overflow: sidebarVisible ? "visible" : "hidden",
          }}
        >
          {/* Columna izquierda */}

          <nav className="flex flex-col items-start h-full p-3 gap-8">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    `flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
                      sidebarVisible ? "" : "justify-center"
                    }`
                  )}
                >
                  <Icon
                    className={cn(
                      "transition-colors relative group w-5 h-5",
                      isActive ? "text-blue-500" : "hover:bg-transparent"
                    )}
                  />
                  {sidebarVisible && (
                    <span
                      className={cn(
                        "transition-colors relative group px-2",
                        isActive ? "text-blue-500" : "hover:bg-transparent"
                      )}
                    >
                      {item.label}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      )}

      {/* Main content area */}
      <div className="flex-1 bg-white relative">
        {/* Toggle button */}
        {showNavigation && (
          <button
            onClick={() => setSidebarVisible((v) => !v)}
            className="absolute top-4 left-0 z-20 bg-white border border-gray-300 rounded-full shadow p-1 hover:bg-gray-50 transition"
            style={{
              transform: "translateX(-50%)",
              left: sidebarVisible ? "0" : "0",
            }}
          >
            {sidebarVisible ? (
              <ChevronLeft className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
        )}

        {/* Columna derecha */}
        <div className="w-full">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
