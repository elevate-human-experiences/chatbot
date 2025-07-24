import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Home, Chat } from "@/pages";
import "./App.css";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="projects/:projectId/agent" element={<Chat />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
