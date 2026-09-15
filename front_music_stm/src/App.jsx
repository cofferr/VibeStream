import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "@/components/ProtectedRoute";
import Login from "@/pages/Login";
import UserDashboard from "@/pages/UserDashboard";
import ProfilePage from "@/pages/ProfilePage";
import AppShell from "./components/layout/AppShell";
import ArtistStudio from "./pages/ArtistStudio";
import SearchPage from "./pages/SearchPage";
import PlaylistsPage from "./pages/PlaylistPage";

const LibraryPage = () => <div className="p-6 text-white">Biblioteca - En desarrollo</div>;
const SettingsPage = () => <div className="p-6 text-white">Configuración - En desarrollo</div>;

export default function App() {
  return (
    <Routes>
      {/* Rutas públicas */}
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Navigate to="/dashboard/home" replace />} />
      
      {/* Rutas protegidas con AppShell */}
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppShell />
        </ProtectedRoute>
      }>
        {/* Ruta por defecto del dashboard */}
        <Route index element={<Navigate to="home" replace />} />
        
        {/* Rutas principales */}
        <Route path="home" element={<UserDashboard />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="library" element={<LibraryPage />} />
        <Route path="playlists" element={<PlaylistsPage/>} />
        <Route path="artist/studio" element={<ArtistStudio />} />
        
        {/* Rutas de usuario */}
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      
      {/* Ruta de fallback */}
      <Route path="*" element={<div className="p-6 text-white">Página no encontrada - 404</div>} />
    </Routes>
  );
}