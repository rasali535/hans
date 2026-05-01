import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import Nav from "@/components/Nav";
import Landing from "@/pages/Landing";
import Console from "@/pages/Console";
import Feed from "@/pages/Feed";
import Blueprint from "@/pages/Blueprint";
import Journal from "@/pages/Journal";

function App() {
  return (
    <div className="App min-h-screen bg-[#0A0A0A] text-white">
      <BrowserRouter>
        <Nav />
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/console" element={<Console />} />
          <Route path="/feed" element={<Feed />} />
          <Route path="/blueprint" element={<Blueprint />} />
          <Route path="/journal" element={<Journal />} />
        </Routes>
        <Toaster theme="dark" position="bottom-right" />
      </BrowserRouter>
    </div>
  );
}

export default App;
