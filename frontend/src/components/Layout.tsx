import { Outlet, useLocation } from "react-router-dom";
import { Navigation } from "@/components/Navigation";

export function Layout() {
  const location = useLocation();

  // Don't show navigation on the home page (chat interface)
  const showNavigation = location.pathname !== "/";

  return (
    <div className="min-h-screen bg-gray-50">
      {showNavigation && <Navigation />}
      <main className={showNavigation ? "" : "h-screen"}>
        <Outlet />
      </main>
    </div>
  );
}
