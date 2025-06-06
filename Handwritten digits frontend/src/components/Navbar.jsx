import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(true);

  // Base styling for each link
  const baseLink = "block px-6 py-3 mb-2 rounded transition-colors duration-200";
  const activeLink = "bg-white/30 text-white";
  const inactiveLink = "text-white/80 hover:text-white";

  const toggleSidebar = () => setIsOpen(prev => !prev);

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* —————— Blobs & Gradient Background —————— */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500 via-pink-400 to-yellow-300" />
      <div className="absolute -top-16 -left-16 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply opacity-70 animate-blob" />
      <div className="absolute top-10 right-[-4rem] w-80 h-80 bg-yellow-200 rounded-full mix-blend-multiply opacity-60 animate-blob animation-delay-2000" />
      <div className="absolute bottom-[-3rem] left-20 w-96 h-96 bg-purple-300 rounded-full mix-blend-multiply opacity-50 animate-blob animation-delay-4000" />

      {/* —————— ChatGPT‐Style Toggle Button (Rounded Rectangle) —————— */}
      <button
        onClick={toggleSidebar}
        aria-label="Toggle sidebar"
        className="fixed top-6 left-4 z-50 bg-white/20 hover:bg-white/30 w-10 h-8 rounded-md flex items-center justify-center focus:outline-none transition-colors duration-200"
      >
        {isOpen ? (
          /* Chevron-Left (close) */
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        ) : (
          /* Chevron-Right (open) */
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5 text-white"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        )}
      </button>

      {/* —————— Sidebar (transparent background) —————— */}
      <div
        className={`
          fixed top-0 left-0 h-full
          w-56
          bg-transparent
          transform transition-transform duration-300
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Increased top margin so links sit below the toggle */}
        <nav className="mt-16">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `${baseLink} ${isActive ? activeLink : inactiveLink}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to="/ocr"
            className={({ isActive }) =>
              `${baseLink} ${isActive ? activeLink : inactiveLink}`
            }
          >
            Cheque Processer
          </NavLink>
          <NavLink
            to="/history"
            className={({ isActive }) =>
              `${baseLink} ${isActive ? activeLink : inactiveLink}`
            }
          >
            History
          </NavLink>
        </nav>
      </div>
    </div>
  );
};

export default Navbar;
