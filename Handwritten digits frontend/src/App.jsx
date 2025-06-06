import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Sidebar from './components/Navbar';
import Home    from './pages/Home';
import OCRPage from './pages/OCRPage';
import History from './pages/History';

export default function App() {
  return (
    <BrowserRouter>
      {/* Full‐screen animated background */}
      <div className="relative min-h-screen overflow-hidden">
        {/* Blobs & gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-400 to-yellow-300" />
        <div className="absolute -top-16 -left-16 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply opacity-70 animate-blob"></div>
        <div className="absolute top-10 right-[-4rem] w-80 h-80 bg-yellow-200 rounded-full mix-blend-multiply opacity-60 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-[-3rem] left-20 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply opacity-50 animate-blob animation-delay-4000"></div>

        {/* Layout container sits above the background */}
        <div className="relative flex">
          <Sidebar />

          <main className="ml-56 flex-1 p-8 overflow-auto bg-transparent">
            <Routes>
              <Route path="/"        element={<Home />} />
              <Route path="/ocr"     element={<OCRPage />} />
              <Route path="/history" element={<History />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}
