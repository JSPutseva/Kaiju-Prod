import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useQuarters } from "../context/QuartersContext";
import { useWebSocket } from "../context/WebSocketContext";

// live resource stock for a district code (A/E/W/X/Z)
export function useQuarterResources(districtCode) {
  const { byCode, status: quartersStatus } = useQuarters();
  const { subscribe } = useWebSocket();
  const [stock, setStock] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  const quarterId = byCode[districtCode]?.id;

  useEffect(() => {
    if (quartersStatus !== "ready" || !quarterId) return;
    let cancelled = false;

    const fetchStock = () => {
      api
        .getQuarterResources(quarterId)
        .then((rows) => {
          if (cancelled) return;
          setStock(
            rows.map((r) => ({
              name: r.resource_name,
              resourceTypeId: r.resource_type_id,
              quantity: r.available_quantity,
              initialQuantity: r.initial_quantity,
              retentionMin: r.retention_min,
            }))
          );
          setStatus("ready");
        })
        .catch((err) => {
          if (cancelled) return;
          setError(err.message);
          setStatus("error");
        });
    };

    setStatus("loading");
    fetchStock();

    // refetch when the backend broadcasts a stock change for this quarter
    const unsubscribe = subscribe((event) => {
      if (event.type === "RESOURCE_UPDATE" && event.data?.quarter_id === quarterId) {
        fetchStock();
      }
    });

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, [quarterId, quartersStatus, subscribe]);

  if (quartersStatus === "error") return { stock: [], status: "error", error: "Could not load quarters" };
  if (quartersStatus === "loading") return { stock: [], status: "loading", error: null };
  return { stock, status, error };
}
