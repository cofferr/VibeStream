import React from 'react';
import { motion } from 'framer-motion';
import { Music } from 'lucide-react';

const AuthHeader = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -8, scale: 0.99 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.45, ease: "easeOut", delay: 0.06 }}
      className="text-center mb-6"
    >
      <div className="inline-flex items-center gap-3 mb-2 justify-center">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.45, delay: 0.12 }}
          className="w-12 h-12 bg-gradient-to-br from-indigo-600 to-pink-500 rounded-xl flex items-center justify-center"
        >
          <Music className="w-6 h-6 text-white" />
        </motion.div>

        <motion.span
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.14 }}
          className="font-bold text-2xl bg-gradient-to-r from-indigo-600 to-pink-500 bg-clip-text text-transparent"
        >
          VibeStream
        </motion.span>
      </div>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.45, delay: 0.18 }}
        className="text-sm text-gray-500"
      >
        Descubre, crea y comparte tu viaje musical
      </motion.p>
    </motion.div>
  );
};

export default AuthHeader;