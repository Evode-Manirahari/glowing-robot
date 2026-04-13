import { Routes, Route } from "react-router-dom";
import MissionsPage from "./pages/MissionsPage";
import MissionDetailPage from "./pages/MissionDetailPage";
import UploadPage from "./pages/UploadPage";
import Nav from "./components/Nav";

export default function App() {
  return (
    <div style={{ fontFamily: "system-ui, sans-serif", maxWidth: 1100, margin: "0 auto", padding: "0 24px" }}>
      <Nav />
      <Routes>
        <Route path="/" element={<MissionsPage />} />
        <Route path="/missions/:id" element={<MissionDetailPage />} />
        <Route path="/upload" element={<UploadPage />} />
      </Routes>
    </div>
  );
}
