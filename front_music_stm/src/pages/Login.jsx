import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

import Card, { CardHeader, CardContent } from "@/components/ui/card";
import { useAuth } from "@/contexts/AuthContexts";
import {
  SuccessModal,
  AuthTabs,
  LoginForm,
  RegisterForm,
  AuthHeader
} from "@/components/login";

export default function Login() {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [active, setActive] = useState("login");
  const [authError, setAuthError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);

  const onLogin = async (values) => {
    try {
      setIsLoading(true);
      setAuthError("");
      
      const credentials = {
        identifier: values.email,
        password: values.password,
      };

      const response = await login(credentials);
      
      if (response.user.role === 'artist') {
        navigate("/dashboard/artist/studio");
      } else {
        navigate("/dashboard/home");
      }
    } catch (err) {
      setAuthError(err.message || "Error durante el login. Verifica tus credenciales.");
    } finally {
      setIsLoading(false);
    }
  };

  const onRegister = async (values) => {
    try {
      setIsLoading(true);
      setAuthError("");

      const userData = {
        username: values.username,
        email: values.email,
        password: values.password,
        birthdate: values.birthdate,
        is_artist: values.isArtist || false,
      };

      await register(userData);
      setShowSuccessModal(true);
    } catch (err) {
      setAuthError(err.message || "Error durante el registro. Intenta nuevamente.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseSuccessModal = () => {
    setShowSuccessModal(false);
    setActive("login");
  };

  // Limpiar errores al cambiar de tab
  const handleTabChange = (tab) => {
    setActive(tab);
    setAuthError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-gray-100 flex items-center justify-center px-6 py-12">
      <div className="w-full max-w-lg">
        <AuthHeader />

        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.995 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.6, ease: "easeOut", delay: 0.22 }}
        >
          <Card className="shadow-lg">
            <CardHeader className="px-4 pt-4 pb-0">
              <AuthTabs active={active} setActive={handleTabChange} />
            </CardHeader>

            <CardContent className="pt-6">
              {active === "login" ? (
                <LoginForm
                  onSubmit={onLogin}
                  error={authError}
                  loading={isLoading}
                />
              ) : (
                <RegisterForm
                  onSubmit={onRegister}
                  error={authError}
                  loading={isLoading}
                />
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>

      <SuccessModal 
        isOpen={showSuccessModal} 
        onClose={handleCloseSuccessModal} 
      />
    </div>
  );
}