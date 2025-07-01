import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Home, About, Settings, Chat, Agent } from "@/pages";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="about" element={<About />} />
          <Route path="settings" element={<Settings />} />
          <Route path="projects/:projectId/agent" element={<Chat />} />
          <Route path="agent" element={<Agent />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
