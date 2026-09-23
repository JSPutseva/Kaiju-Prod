import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";
import { DISTRICTS } from "../data/districts";
import { useCurrentUser } from "./CurrentUserContext";

// district name -> A/E/W/X/Z code
const CODE_BY_NAME = Object.fromEntries(DISTRICTS.map((d) => [d.name, d.id]));

const QuartersContext = createContext(null);

// byCode: { A: { id, name, disaster_level, sea_access }, ... }
export function QuartersProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useCurrentUser();
  const [byCode, setByCode] = useState({});
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  useEffect(() => {
    // /quarters requires auth — wait for login to resolve before fetching,
    // and refetch whenever auth state changes (e.g. login after landing on /login).
    if (authLoading) return;

    if (!isAuthenticated) {
      setByCode({});
      setStatus("loading");
      return;
    }

    let cancelled = false;
    setStatus("loading");
    api
      .getQuarters()
      .then((quarters) => {
        if (cancelled) return;
        const map = {};
        for (const q of quarters) {
          const code = CODE_BY_NAME[q.name];
          if (code) map[code] = q;
        }
        setByCode(map);
        setStatus("ready");
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err.message);
        setStatus("error");
      });
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, authLoading]);

  return (
    <QuartersContext.Provider value={{ byCode, status, error }}>
      {children}
    </QuartersContext.Provider>
  );
}

export function useQuarters() {
  const ctx = useContext(QuartersContext);
  if (!ctx) {
    throw new Error("useQuarters must be used within a QuartersProvider");
  }
  return ctx;
}
