import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useCurrentUser } from "./CurrentUserContext";
import { api } from "../api/client";

const WS_BASE_URL = (process.env.REACT_APP_API_URL || "http://localhost:8000").replace(
  /^http/,
  "ws"
);

const WebSocketContext = createContext(null);

// capped so a long session doesn't grow this unboundedly — matches the
// backend history endpoint's own limit
const MAX_LEVEL_ALERTS = 50;

// real-time KAIJU event stream: resource updates, requests, disaster alerts.
// Captured here (rather than in whichever page happens to be open) so an
// alert isn't lost just because the Dashboard/calendar weren't mounted at
// the moment it was broadcast — e.g. triggering it from the Kaiju POV page.
export function WebSocketProvider({ children }) {
  const { isAuthenticated } = useCurrentUser();
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const [levelAlerts, setLevelAlerts] = useState([]);
  const listenersRef = useRef(new Set());

  // seed with real history on login, so a page refresh (or joining mid-crisis)
  // still shows past attacks, not just ones broadcast while connected
  useEffect(() => {
    if (!isAuthenticated) {
      setLevelAlerts([]);
      return;
    }

    let cancelled = false;
    api
      .getDisasterLevelEvents()
      .then((events) => {
        if (cancelled) return;
        const historical = events
          .slice()
          .reverse() // backend returns newest-first; keep oldest-first internally
          .map((e) => ({
            id: `level-hist-${e.id}`,
            quarter_id: e.quarter_id,
            level: e.level,
            changed_by_id: e.changed_by_id,
            timestamp: new Date(e.created_at).getTime(),
          }));
        // merge rather than replace: a live event may have already arrived
        // while this fetch was in flight
        setLevelAlerts((prev) => [...historical, ...prev].slice(-MAX_LEVEL_ALERTS));
      })
      .catch(() => {
        // non-critical: live alerts still work even if history fails to load
      });

    return () => {
      cancelled = true;
    };
  }, [isAuthenticated]);

  useEffect(() => {
    const token = localStorage.getItem("kaiju_token");
    if (!isAuthenticated || !token) {
      setConnected(false);
      return;
    }

    let cancelled = false;
    let socket = null;
    let reconnectTimer = null;

    const connect = () => {
      socket = new WebSocket(`${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`);

      socket.onopen = () => {
        if (!cancelled) setConnected(true);
      };

      socket.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        reconnectTimer = setTimeout(connect, 3000);
      };

      socket.onerror = () => {
        socket.close();
      };

      socket.onmessage = (message) => {
        if (cancelled) return;
        try {
          const event = JSON.parse(message.data);
          setLastEvent(event);
          if (event.type === "LEVEL_CHANGED") {
            const data = event.data ?? {};
            setLevelAlerts((prev) =>
              [
                ...prev,
                {
                  id: `level-${Date.now()}-${data.quarter_id}`,
                  quarter_id: data.quarter_id,
                  level: data.level,
                  changed_by_id: data.changed_by_id ?? null,
                  timestamp: Date.now(),
                },
              ].slice(-MAX_LEVEL_ALERTS)
            );
          }
          listenersRef.current.forEach((callback) => callback(event));
        } catch {
          // ignore malformed frames
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [isAuthenticated]);

  const subscribe = (callback) => {
    listenersRef.current.add(callback);
    return () => listenersRef.current.delete(callback);
  };

  return (
    <WebSocketContext.Provider value={{ connected, lastEvent, subscribe, levelAlerts }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocket() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) {
    throw new Error("useWebSocket must be used within a WebSocketProvider");
  }
  return ctx;
}
