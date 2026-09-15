// src/lib/utils.js
import clsx from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs) {
  // clsx concatena condicionalmente; twMerge resuelve conflictos de Tailwind
  return twMerge(clsx(...inputs)).trim();
}

export default cn;
