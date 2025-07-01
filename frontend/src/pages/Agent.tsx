import { useState } from "react";
import { ChevronLeft, ChevronRight, MessageCircle, Info, Settings, Bot } from "lucide-react";

export function Agent() {
  const [sidebarVisible, setSidebarVisible] = useState(true);

  return (
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
          <a
            href="#"
            className={`flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
              sidebarVisible ? "" : "justify-center"
            }`}
          >
            <MessageCircle className="w-5 h-5" />
            {sidebarVisible && <span className="text-sm font-medium">Chat</span>}
          </a>
          <a
            href="#"
            className={`flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
              sidebarVisible ? "" : "justify-center"
            }`}
          >
            <Info className="w-5 h-5" />
            {sidebarVisible && <span className="text-sm font-medium">About</span>}
          </a>
          <a
            href="#"
            className={`flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
              sidebarVisible ? "" : "justify-center"
            }`}
          >
            <Settings className="w-5 h-5" />
            {sidebarVisible && <span className="text-sm font-medium">Settings</span>}
          </a>
          <a
            href="#"
            className={`flex items-center gap-3 text-gray-700 hover:text-blue-600 transition-colors w-full ${
              sidebarVisible ? "" : "justify-center"
            }`}
          >
            <Bot className="w-5 h-5" />
            {sidebarVisible && <span className="text-sm font-medium">Agent</span>}
          </a>
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
        <div className="absolute left-1/2 bottom-0 transform -translate-x-1/2 mb-6 w-full max-w-md">
          <div className="bg-yellow-300 rounded-lg shadow-lg p-6 w-full">
            {/* Contenido centrado y fijo abajo */}
            <div className="text-center font-semibold">Contenedor centrado y fijo abajo</div>
          </div>
        </div>
      </div>
    </div>
  );
}
