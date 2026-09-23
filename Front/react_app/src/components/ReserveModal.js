import { useEffect, useState } from "react";
import { getDistrict } from "../data/districts";
import { useQuarterResources } from "../hooks/useQuarterResources";
import { useQuarters } from "../context/QuartersContext";
import { api } from "../api/client";

// reservations hold a resource for a fixed 24h window from now (no date
// picker in this UI yet)
const RESERVATION_WINDOW_MS = 24 * 60 * 60 * 1000;

export default function ReserveModal({ districtId, onClose }) {
  const district = getDistrict(districtId);
  const { stock, status } = useQuarterResources(districtId);
  const { byCode: quarterByCode } = useQuarters();
  const [resourceName, setResourceName] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  if (!district) return null;

  const selectedItem = stock.find((item) => item.name === resourceName);
  const maxReservable = selectedItem ? Math.max(selectedItem.quantity - selectedItem.retentionMin, 0) : 0;

  const handleReserve = async () => {
    const quarter = quarterByCode[districtId];
    if (!quarter || !selectedItem) return;

    setSubmitting(true);
    setSubmitError(null);
    try {
      const startAt = new Date();
      const endAt = new Date(startAt.getTime() + RESERVATION_WINDOW_MS);
      await api.createReservation({
        quarter_id: quarter.id,
        resource_type_id: selectedItem.resourceTypeId,
        quantity,
        start_at: startAt.toISOString(),
        end_at: endAt.toISOString(),
      });
      setSubmitted(true);
    } catch (err) {
      setSubmitError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`Reserve ${district.name} resources`}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">{district.name}: reserve...</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        {submitted ? (
          <div className="text-center">
            <p className="mb-4 text-base text-gray-800 dark:text-gray-200">
              Reserved {quantity} × {resourceName} in {district.name}.
              <br />
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Held for the next 24 hours.
              </span>
            </p>
            <button
              type="button"
              onClick={onClose}
              className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2 text-base font-bold text-white hover:bg-[#D98C00]"
            >
              Close
            </button>
          </div>
        ) : status === "loading" ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Loading resources…</p>
        ) : status === "error" ? (
          <p className="text-sm text-[#dc2626] dark:text-red-400">Couldn't reach the backend.</p>
        ) : (
          <>
            <label className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
              Resource
              <select
                value={resourceName ?? ""}
                onChange={(e) => setResourceName(e.target.value || null)}
                className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-base dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
              >
                <option value="">Select a resource…</option>
                {stock.map((item) => (
                  <option key={item.name} value={item.name}>
                    {item.name} ({item.quantity} available)
                  </option>
                ))}
              </select>
            </label>

            {selectedItem && (
              <label className="mb-3 block text-sm font-medium text-gray-700 dark:text-gray-300">
                Quantity (retention floor: {selectedItem.retentionMin}, max reservable: {maxReservable})
                <input
                  type="number"
                  min={1}
                  max={maxReservable}
                  value={quantity}
                  onChange={(e) => setQuantity(Number(e.target.value))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-base dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                />
              </label>
            )}

            {submitError && (
              <p className="mb-3 text-sm text-[#dc2626] dark:text-red-400">{submitError}</p>
            )}

            <button
              type="button"
              disabled={!selectedItem || quantity < 1 || quantity > maxReservable || submitting}
              onClick={handleReserve}
              className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2 text-base font-bold text-white hover:bg-[#D98C00] disabled:cursor-not-allowed disabled:bg-gray-300"
            >
              {submitting ? "Reserving…" : "Reserve"}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
