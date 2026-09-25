import { useNavigate } from "react-router-dom";
import { useDisasterLevel } from "../context/DisasterLevelContext";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useTheme } from "../context/ThemeContext";
import { useWebSocket } from "../context/WebSocketContext";
import { getRole } from "../data/roles";

function SpeakerIcon({ muted }) {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 9v6h4l5 5V4L8 9H4z" strokeLinejoin="round" />
      {muted ? (
        <path d="M16 9l5 6M21 9l-5 6" strokeLinecap="round" />
      ) : (
        <path d="M17.5 8.5a5 5 0 0 1 0 7" strokeLinecap="round" />
      )}
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M16 17l5-5-5-5M21 12H9" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ThemeIcon({ dark }) {
  return dark ? (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
      <path
        d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="4" />
      <path
        d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function Header() {
  const navigate = useNavigate();
  const { level, muted, toggleMuted } = useDisasterLevel();
  const { name, roleCode, logout } = useCurrentUser();
  const { theme, toggleTheme } = useTheme();
  const { connected } = useWebSocket();
  const role = getRole(roleCode);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="flex items-center justify-between bg-gray-50 px-6 py-3 dark:bg-gray-900">
      <div className="flex items-center gap-2">
        <img
          src={theme === "dark" ? "/logo_dark.png" : "/logo.png"}
          alt="Kaiju logo"
          className="h-12 w-12 shrink-0 object-contain"
        />
        <span className="font-display text-3xl leading-none text-gray-900 dark:text-gray-100">
          Kaiju
        </span>
        <span
          className={`font-display text-3xl leading-none ${
            level > 1 ? "text-red-600 dark:text-red-500" : "text-gray-900 dark:text-gray-100"
          }`}
        >
          !Alert
        </span>
        <span
          className="ml-1 flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500"
          title={connected ? "Live updates connected" : "Live updates disconnected"}
        >
          <span
            className={`h-2 w-2 rounded-full ${connected ? "bg-green-500" : "bg-gray-300 dark:bg-gray-600"}`}
            aria-hidden="true"
          />
          {connected ? "live" : "offline"}
        </span>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={toggleTheme}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          className="rounded-full border border-gray-200 bg-white p-2.5 text-gray-600 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <ThemeIcon dark={theme === "dark"} />
        </button>

        <button
          type="button"
          onClick={toggleMuted}
          aria-label={muted ? "Unmute alert sounds" : "Mute alert sounds"}
          aria-pressed={muted}
          className="rounded-full border border-gray-200 bg-white p-2.5 text-gray-600 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <SpeakerIcon muted={muted} />
        </button>

        <div className="flex items-center gap-3 rounded-full border border-gray-200 bg-white px-3 py-1.5 shadow-sm dark:border-gray-700 dark:bg-gray-800">
          {role ? (
            <img
              src={role.avatar}
              alt={role.label}
              className="h-12 w-12 shrink-0 rounded-full bg-gray-100 object-contain p-1.5 dark:bg-gray-700"
            />
          ) : (
            <span className="h-10 w-10 shrink-0 rounded-full bg-indigo-300 dark:bg-indigo-800" aria-hidden="true" />
          )}
          <div className="leading-tight">
            <p className="text-base font-semibold text-gray-900 dark:text-gray-100">{name}</p>
            <p className="text-sm text-[#B36B00] dark:text-[#FFC966]">{role?.label ?? roleCode}</p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleLogout}
          aria-label="Log out"
          className="rounded-full border border-gray-200 bg-white p-2.5 text-gray-600 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
        >
          <LogoutIcon />
        </button>
      </div>
    </header>
  );
}
