import { useEffect } from "react";
import { getDistrict } from "../data/districts";
import { resourceStatus, STATUS } from "../data/resources";
import { useQuarterResources } from "../hooks/useQuarterResources";

export default function ZoneModal({ districtId, onClose }) {
  const district = getDistrict(districtId);
  const { stock, status, error } = useQuarterResources(districtId);

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  if (!district) return null;

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${district.name} zone`}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {district.name} zone
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        <div className="mb-3 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600 dark:text-gray-400">
          {Object.values(STATUS).map((s) => (
            <span key={s.label} className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.dot }} />
              {s.label}
            </span>
          ))}
        </div>

        {status === "loading" && <p className="text-sm text-gray-500 dark:text-gray-400">Loading resources…</p>}
        {status === "error" && (
          <p className="text-sm text-[#dc2626] dark:text-red-400">Couldn't reach the backend: {error}</p>
        )}

        {status === "ready" && (
          <table className="w-full border-collapse overflow-hidden rounded-md border border-[#FBD98A] text-base dark:border-gray-700">
            <tbody>
              {stock.map((item) => {
                const rowStatus = STATUS[resourceStatus(item)];
                return (
                  <tr key={item.name} className="border-b border-[#FBD98A] last:border-b-0 dark:border-gray-700">
                    <td className="border-r border-[#FBD98A] px-3 py-2 text-gray-800 dark:border-gray-700 dark:text-gray-200">
                      {item.name}
                    </td>
                    <td
                      className={`px-3 py-2 ${rowStatus.bold ? "font-semibold" : ""}`}
                      style={{ color: rowStatus.text }}
                    >
                      {item.quantity}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
