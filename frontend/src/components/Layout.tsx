import { Outlet, useLocation } from "react-router-dom";
import { Navigation } from "@/components/Navigation";

export function Layout() {
  const location = useLocation();

  // Don't show navigation on the home page (chat interface)
  const showNavigation = location.pathname !== "/" && !location.pathname.startsWith("/agent");

  return (
    <div className="fixed inset-0 bg-gray-50 flex flex-col">
      {showNavigation && <Navigation />}
      <main className="flex-1 flex flex-col">
        <Outlet />
      </main>
    </div>
  );
}
