import { createContext, useContext, useEffect, useRef, useState } from "react";
import { LEVEL_SOUNDS } from "../data/levelSounds";

// matches the rules PDF's catastrophe-level names
export const LEVELS = [
  { level: 1, name: "Watch" },
  { level: 2, name: "Alert" },
  { level: 3, name: "Emergency" },
  { level: 4, name: "Critical" },
  { level: 5, name: "Catastrophic" },
];

export const LEVEL_NAMES = Object.fromEntries(LEVELS.map((l) => [l.level, l.name]));

const DisasterLevelContext = createContext(null);

export function DisasterLevelProvider({ children, initialLevel = 2 }) {
  const [level, setLevel] = useState(initialLevel);
  const [muted, setMuted] = useState(false);
  const levelName = LEVELS.find((l) => l.level === level)?.name ?? "Unknown";

  // plays the level's roar on change, not on first mount
  const previousLevel = useRef(level);
  useEffect(() => {
    if (previousLevel.current === level) return;
    previousLevel.current = level;
    const src = LEVEL_SOUNDS[level];
    if (src && !muted) {
      new Audio(src).play().catch(() => {});
    }
  }, [level, muted]);

  const value = {
    level,
    levelName,
    setLevel,
    isMaxLevel: level === 5,
    muted,
    toggleMuted: () => setMuted((m) => !m),
  };

  return (
    <DisasterLevelContext.Provider value={value}>
      {children}
    </DisasterLevelContext.Provider>
  );
}

export function useDisasterLevel() {
  const ctx = useContext(DisasterLevelContext);
  if (!ctx) {
    throw new Error("useDisasterLevel must be used within a DisasterLevelProvider");
  }
  return ctx;
}
