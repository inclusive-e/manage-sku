import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Dashboard } from "./pages/Dashboard";
import { Products } from "./pages/Products";
import { Users } from "./pages/Users";
import { Settings } from "./pages/Settings";
import { DataUpload } from "./pages/DataUpload";

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-[#FAFAF5]">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/products" element={<Products />} />
            <Route path="/users" element={<Users />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/upload" element={<DataUpload />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
