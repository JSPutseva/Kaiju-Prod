import { useEffect, useState } from "react";
import { EVENT_TYPES } from "../data/calendarEvents";
import { COLORS } from "../data/colors";
import { useTheme } from "../context/ThemeContext";
import { useQuarters } from "../context/QuartersContext";
import { useWebSocket } from "../context/WebSocketContext";
import { LEVEL_NAMES } from "../context/DisasterLevelContext";
import { api } from "../api/client";

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
  const { byCode: quarterByCode, status: quartersStatus } = useQuarters();
  // level alerts are captured app-wide in WebSocketContext (not locally
  // here), so one triggered while this modal wasn't open — e.g. from the
  // Kaiju POV page — still shows up once you open it
  const { subscribe, levelAlerts } = useWebSocket();

  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);
  // lifted out of the loader effect below so the level-alert mapping (which
  // isn't tied to that fetch) can resolve names too
  const [nameById, setNameById] = useState({});

  const quarterNameById = Object.fromEntries(
    Object.values(quarterByCode).map((q) => [q.id, q.name])
  );

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

  useEffect(() => {
    if (quartersStatus !== "ready") return;

    let cancelled = false;

    const load = () => {
      setStatus((s) => (s === "ready" ? s : "loading"));
      Promise.all([
        api.getRequests(),
        api.getReservations(),
        api.getResourceTypes(),
        api.listUsers(),
      ])
        .then(([requests, reservations, resourceTypes, users]) => {
          if (cancelled) return;

          const resourceNameById = Object.fromEntries(
            resourceTypes.map((rt) => [rt.id, rt.name])
          );
          const nameById = Object.fromEntries(users.map((u) => [u.id, u.name]));
          setNameById(nameById);

          const REQUEST_VERBS = {
            PENDING: "requested",
            APPROVED: "approved",
            REJECTED: "denied",
            CANCELLED: "cancelled",
            COMPLETED: "completed",
          };

          const requestEvents = requests.map((r) => {
            const sourceName = quarterNameById[r.source_quarter_id] ?? "?";
            const destName = quarterNameById[r.destination_quarter_id] ?? "?";
            const resourceName = resourceNameById[r.resource_type_id] ?? "resource";
            const requesterName = nameById[r.requester_id] ?? "Someone";
            const deciderName = r.decided_by_id ? nameById[r.decided_by_id] ?? "Someone" : null;
            const verb = REQUEST_VERBS[r.status] ?? r.status.toLowerCase();
            const actorName = deciderName ?? requesterName;
            const viaName = r.transit_via_id ? quarterNameById[r.transit_via_id] : null;
            const viaSuffix = viaName ? ` via ${viaName}` : "";

            const tooltipLines = [
              `${r.requisition ? "Requisition" : "Transfer"} request: ${sourceName} → ${destName}${viaSuffix}`,
              `${resourceName} × ${r.quantity}`,
              `Requested by ${requesterName} on ${new Date(r.created_at).toLocaleString()}`,
            ];
            if (deciderName) {
              tooltipLines.push(
                `${r.status === "REJECTED" ? "Denied" : "Approved"} by ${deciderName} on ${new Date(
                  r.decided_at
                ).toLocaleString()}`
              );
            }
            if (r.status === "REJECTED" && r.rejection_reason) {
              tooltipLines.push(`Reason: ${r.rejection_reason}`);
            }

            return {
              id: `req-${r.id}`,
              date: r.created_at,
              type: r.requisition ? "requisition" : "transfer",
              label: `${actorName} ${verb}: ${sourceName} → ${destName}${viaSuffix} (${resourceName})`,
              tooltip: tooltipLines.join("\n"),
            };
          });

          const RESERVATION_VERBS = {
            PENDING: "requested",
            APPROVED: "approved",
            CANCELLED: "cancelled",
            COMPLETED: "completed",
          };

          const reservationEvents = reservations.map((r) => {
            const quarterName = quarterNameById[r.quarter_id] ?? "?";
            const resourceName = resourceNameById[r.resource_type_id] ?? "resource";
            const userName = nameById[r.user_id] ?? "Someone";
            const verb = RESERVATION_VERBS[r.status] ?? r.status.toLowerCase();

            return {
              id: `res-${r.id}`,
              date: r.created_at,
              type: "reservation",
              label: `${userName} ${verb} reservation: ${quarterName} (${resourceName})`,
              tooltip: [
                `Reservation: ${quarterName}, ${resourceName} × ${r.quantity}`,
                `Requested by ${userName} on ${new Date(r.created_at).toLocaleString()}`,
                `Status: ${r.status}`,
              ].join("\n"),
            };
          });

          const merged = [...requestEvents, ...reservationEvents].sort(
            (a, b) => new Date(a.date) - new Date(b.date)
          );

          setEvents(merged);
          setStatus("ready");
        })
        .catch((err) => {
          if (cancelled) return;
          setError(err.message);
          setStatus("error");
        });
    };

    load();

    // live refresh: refetch whenever a request is created or decided, or a
    // reservation-driven resource change is broadcast (level changes are
    // handled separately below, from the app-wide WebSocketContext state)
    const unsubscribe = subscribe((event) => {
      if (
        ["REQUEST_CREATED", "REQUEST_APPROVED", "REQUEST_DENIED", "RESOURCE_UPDATE"].includes(
          event.type
        )
      ) {
        load();
      }
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [quartersStatus, subscribe]);

  const levelChangeEvents = levelAlerts.map((a) => {
    const quarterName = quarterNameById[a.quarter_id] ?? "?";
    const levelName = LEVEL_NAMES[a.level] ?? a.level;
    const changedByName = a.changed_by_id ? nameById[a.changed_by_id] ?? "Someone" : null;
    return {
      id: a.id,
      date: new Date(a.timestamp).toISOString(),
      type: "levelChange",
      label: `${quarterName} → Level ${a.level} (${levelName})`,
      tooltip: [
        `${quarterName} disaster level changed to ${levelName}`,
        changedByName ? `By ${changedByName} on ${new Date(a.timestamp).toLocaleString()}` : null,
      ]
        .filter(Boolean)
        .join("\n"),
    };
  });

  const allEvents = [...events, ...levelChangeEvents].sort(
    (a, b) => new Date(a.date) - new Date(b.date)
  );

  const width = Math.max(PAD_X * 2, PAD_X * 2 + (allEvents.length - 1) * STEP_X);

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

        {status === "loading" && (
          <p className="py-10 text-center text-sm text-gray-500 dark:text-gray-400">
            Loading operational history…
          </p>
        )}
        {status === "error" && (
          <p className="py-10 text-center text-sm text-[#dc2626] dark:text-red-400">
            Couldn't load the operational calendar: {error}
          </p>
        )}
        {status === "ready" && allEvents.length === 0 && (
          <p className="py-10 text-center text-sm text-gray-500 dark:text-gray-400">
            No transfers, requisitions or reservations yet.
          </p>
        )}

        {status === "ready" && allEvents.length > 0 && (
          <div className="overflow-x-auto">
            <svg viewBox={`0 0 ${width} 300`} width={width} height="300" role="img" aria-label="Timeline of operational events">
              <line x1={PAD_X - 20} y1={AXIS_Y} x2={width - PAD_X + 20} y2={AXIS_Y} stroke={axisColor} strokeWidth="1.5" />

              {allEvents.map((event, i) => {
                const x = PAD_X + i * STEP_X;
                const level = LEVELS[i % LEVELS.length];
                const tipY = AXIS_Y - level * UNIT;
                const meta = eventTypes[event.type];
                const colorHex = meta?.dot ?? "#111827";
                const above = level > 0;

                return (
                  <g key={event.id}>
                    {event.tooltip && <title>{event.tooltip}</title>}
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
        )}
      </div>
    </div>
  );
}
