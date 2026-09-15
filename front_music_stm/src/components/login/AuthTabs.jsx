import React, { useRef, useLayoutEffect } from 'react';
import { motion } from 'framer-motion';

const AuthTabs = ({ active, setActive }) => {
  const tabsRef = useRef(null);
  const [indicatorWidth, setIndicatorWidth] = React.useState(0);
  const [indicatorX, setIndicatorX] = React.useState(0);
  const BUFFER_PX = 6;

  useLayoutEffect(() => {
    if (!tabsRef.current) return;
    const el = tabsRef.current;

    const resize = () => {
      const w = el.clientWidth;
      const half = Math.round(w / 2) + BUFFER_PX;
      setIndicatorWidth(half);
      setIndicatorX(active === "login" ? 0 : Math.round(w / 2));
    };

    resize();

    const ro = new ResizeObserver(resize);
    ro.observe(el);
    window.addEventListener("resize", resize);
    window.addEventListener("orientationchange", resize);

    return () => {
      ro.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("orientationchange", resize);
    };
  }, [active]);

  const onKeyDownTabs = (e) => {
    if (e.key === "ArrowLeft") setActive("login");
    if (e.key === "ArrowRight") setActive("register");
  };

  return (
    <div
      role="tablist"
      aria-label="Auth tabs"
      ref={tabsRef}
      onKeyDown={onKeyDownTabs}
      tabIndex={0}
      className="relative w-full max-w-md mx-auto bg-gray-100 rounded-md p-1"
    >
      <motion.div
        animate={{ x: indicatorX }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className="pointer-events-none absolute top-0 h-full rounded-md bg-gradient-to-r from-indigo-500 to-purple-600 shadow-lg"
        style={{
          width: `${indicatorWidth}px`,
          left: 0,
          willChange: "transform",
        }}
        aria-hidden
      />

      <div className="relative z-10 flex">
        <button
          role="tab"
          aria-selected={active === "login"}
          onClick={() => setActive("login")}
          className={`flex-1 z-20 px-4 py-2 text-sm font-medium rounded-md focus:outline-none transition-colors ${
            active === "login" ? "text-white" : "text-gray-600"
          }`}
        >
          Sign In
        </button>

        <button
          role="tab"
          aria-selected={active === "register"}
          onClick={() => setActive("register")}
          className={`flex-1 z-20 px-4 py-2 text-sm font-medium rounded-md focus:outline-none transition-colors ${
            active === "register" ? "text-white" : "text-gray-600"
          }`}
        >
          Sign Up
        </button>
      </div>
    </div>
  );
};

export default AuthTabs;