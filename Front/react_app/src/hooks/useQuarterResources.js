import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useQuarters } from "../context/QuartersContext";

// live resource stock for a district code (A/E/W/X/Z)
export function useQuarterResources(districtCode) {
  const { byCode, status: quartersStatus } = useQuarters();
  const [stock, setStock] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  const quarterId = byCode[districtCode]?.id;

  useEffect(() => {
    if (quartersStatus !== "ready" || !quarterId) return;
    let cancelled = false;
    setStatus("loading");
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
    return () => {
      cancelled = true;
    };
  }, [quarterId, quartersStatus]);

  if (quartersStatus === "error") return { stock: [], status: "error", error: "Could not load quarters" };
  if (quartersStatus === "loading") return { stock: [], status: "loading", error: null };
  return { stock, status, error };
}
