import { Outlet, useLocation, Link } from "react-router-dom";
//import { Navigation } from "@/components/Navigation";

import { cn } from "@/lib/utils";

import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageCircle, Info, Settings } from "lucide-react";

export function Layout() {
  //const location = useLocation();

  const [sidebarVisible, setSidebarVisible] = useState(true);

  // Don't show navigation on the home page (chat interface)
  //const showNavigation = location.pathname !== "/" && !location.pathname.startsWith("/agent");

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
    // <div className="fixed inset-0 bg-gray-50 flex flex-col">
    //   {showNavigation && <Navigation />}
    //   <main className="flex-1 flex flex-col">
    //     <Outlet />
    //   </main>
    // </div>

    <div className="flex h-screen">
      {/* Sidebar */}
      <div
        className={`bg-gray-100 border-r border-gray-200 transition-all duration-200`}
        style={{
          width: sidebarVisible ? "10%" : "50px",
          minWidth: sidebarVisible ? "80px" : "50px",
          maxWidth: sidebarVisible ? undefined : "50px",
          overflow: sidebarVisible ? "visible" : "hidden",
        }}
      >
        {/* Columna izquierda */}
        <nav className="flex flex-col items-start py-8 h-full px-2 gap-8 mt-10">
          {navItems.map((item) => {
            const Icon = item.icon;
            //const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
                  sidebarVisible ? "" : "justify-center"
                }`}
              >
                <Icon className="w-5 h-5" />
                {sidebarVisible && <span className="text-sm font-medium">{item.label}</span>}
              </Link>
            );
          })}
        </nav>
      </div>
      <div className="flex-1 bg-white relative">
        {/* Toggle button */}
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

        {/* Columna derecha */}
        <div className="w-full">
          <Outlet />
        </div>
      </div>
    </div>
  );
}
