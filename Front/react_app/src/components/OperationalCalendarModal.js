import { useEffect } from "react";
import { CALENDAR_EVENTS, EVENT_TYPES } from "../data/calendarEvents";
import { COLORS } from "../data/colors";
import { useTheme } from "../context/ThemeContext";

const UNIT = 24;
// stem heights, alternating so labels don't collide
const LEVELS = [2, -1.5, 3, -1, 1.5, -2.5, 2.5, -1.5, 3.5, -2];
const STEP_X = 115;
const PAD_X = 60;
const AXIS_Y = 150;

function formatDate(iso) {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function OperationalCalendarModal({ onClose }) {
  const { theme } = useTheme();
  const axisColor = theme === "dark" ? "#4B5563" : "#D1D5DB";
  const dateTextColor = theme === "dark" ? "#9CA3AF" : "#6B7280";
  // transfer dot uses the site's primary color, which differs per theme
  const transferColor = theme === "dark" ? COLORS.primary : COLORS.primaryLight;
  const eventTypes = {
    ...EVENT_TYPES,
    transfer: { ...EVENT_TYPES.transfer, text: transferColor, dot: transferColor },
  };

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const width = PAD_X * 2 + (CALENDAR_EVENTS.length - 1) * STEP_X;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Operational calendar"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-3xl rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Operational calendar</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        <div className="mb-4 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600 dark:text-gray-400">
          {Object.values(eventTypes).map((t) => (
            <span key={t.label} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: t.dot }} />
              {t.label}
            </span>
          ))}
        </div>

        <div className="overflow-x-auto">
          <svg viewBox={`0 0 ${width} 300`} width={width} height="300" role="img" aria-label="Timeline of operational events">
            <line x1={PAD_X - 20} y1={AXIS_Y} x2={width - PAD_X + 20} y2={AXIS_Y} stroke={axisColor} strokeWidth="1.5" />

            {CALENDAR_EVENTS.map((event, i) => {
              const x = PAD_X + i * STEP_X;
              const level = LEVELS[i % LEVELS.length];
              const tipY = AXIS_Y - level * UNIT;
              const meta = eventTypes[event.type];
              const colorHex = meta.dot ?? "#111827";
              const above = level > 0;

              return (
                <g key={event.id}>
                  <line x1={x} y1={AXIS_Y} x2={x} y2={tipY} stroke={colorHex} strokeWidth="1.5" />
                  <circle cx={x} cy={AXIS_Y} r="3" fill={colorHex} />
                  <text
                    x={x}
                    y={above ? tipY - 6 : tipY + 6}
                    textAnchor="middle"
                    dominantBaseline={above ? "baseline" : "hanging"}
                    fontSize="13"
                    fontWeight="600"
                    fill={colorHex}
                  >
                    {event.label}
                  </text>
                  <text
                    x={x}
                    y={AXIS_Y + 18}
                    textAnchor="middle"
                    fontSize="12"
                    fill={dateTextColor}
                  >
                    {formatDate(event.date)}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>
    </div>
  );
}
