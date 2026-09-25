import { useEffect, useState } from "react";
import { DISTRICTS, getDistrict, isAdjacent, canGoBySea, transitOptions } from "../data/districts";
import { useQuarters } from "../context/QuartersContext";
import { useQuarterResources } from "../hooks/useQuarterResources";
import { api } from "../api/client";

const REASON_LABELS = {
  INVALID_QUANTITY: "Invalid quantity",
  INVALID_QUARTER: "Invalid quarter",
  SAME_QUARTER: "Same quarter",
  INVALID_RESOURCE_QUANTITY: "Invalid resource quantity",
  DISASTER_LEVEL_TOO_LOW: "Disaster level rule",
  NON_ADJACENT_TRANSFER: "Adjacency rule",
  MARITIME_NOT_ALLOWED: "Maritime rule",
  ADJACENT_SURPLUS_AVAILABLE: "Adjacency rule",
  INVALID_TRANSIT_QUARTER: "Transit rule",
  INSUFFICIENT_AVAILABLE_RESOURCE: "Insufficient stock",
  RETENTION_LIMIT: "Retention rule",
  QC_APPROVAL_REQUIRED: "Approval rule",
  PERMISSION_DENIED: "Permission rule",
};

const ROUTES = [
  { id: "direct", label: "Directly" },
  { id: "transit", label: "Throught..." },
  { id: "sea", label: "On sea" },
];

export default function TransferFlowModal({ originId, direction, seaOnly, onClose }) {
  const origin = getDistrict(originId);
  const { byCode: quarterByCode, status: quartersStatus } = useQuarters();
  const [target, setTarget] = useState(null);
  const [routeChoice, setRouteChoice] = useState(seaOnly ? "sea" : null);
  const [transitVia, setTransitVia] = useState(null);
  const [resourceName, setResourceName] = useState(null);
  const [quantity, setQuantity] = useState(1);
  const [preview, setPreview] = useState(null); // null | "loading" | RouteDecisionOut | "error"
  const [routeResult, setRouteResult] = useState(null);
  const [sending, setSending] = useState(false);

  // supplier is the target for "get", the origin for "send"
  const supplierCode = direction === "from" ? target : originId;
  const requesterCode = direction === "from" ? originId : target;
  const { stock, status: stockStatus } = useQuarterResources(supplierCode);

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const selectedItem = stock.find((item) => item.name === resourceName);
  const maxSendable = selectedItem ? Math.max(selectedItem.quantity - selectedItem.retentionMin, 0) : 0;
  const preferMaritime = routeChoice === "sea";

  // live route preview, debounced
  useEffect(() => {
    const sourceQ = quarterByCode[supplierCode];
    const destQ = quarterByCode[requesterCode];
    if (!sourceQ || !destQ || !selectedItem || quantity < 1 || quantity > maxSendable) {
      setPreview(null);
      return;
    }
    let cancelled = false;
    setPreview("loading");
    const timer = setTimeout(() => {
      api
        .routeTransfer({
          source_quarter_id: sourceQ.id,
          destination_quarter_id: destQ.id,
          resource_type_id: selectedItem.resourceTypeId,
          quantity,
          prefer_maritime: preferMaritime,
          transit_via: routeChoice === "transit" ? quarterByCode[transitVia]?.id : undefined,
        })
        .then((result) => !cancelled && setPreview(result))
        .catch((err) => !cancelled && setPreview({ networkError: true, message: err.message }));
    }, 300);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supplierCode, requesterCode, resourceName, quantity, preferMaritime, maxSendable, routeChoice, transitVia]);

  if (!origin) return null;

  const verb = direction === "from" ? "Get resources from" : "Send resources to";
  const targetOptions = DISTRICTS.filter(
    (d) => d.id !== originId && (!seaOnly || (quarterByCode[originId]?.sea_access && quarterByCode[d.id]?.sea_access))
  );

  const adjacent = target ? isAdjacent(supplierCode, requesterCode) : false;
  const bothHaveSea = target ? canGoBySea(supplierCode, requesterCode) : false;

  const step = !target
    ? "target"
    : !routeChoice
    ? "route"
    : routeChoice === "transit" && !transitVia
    ? "transit"
    : routeResult
    ? "result"
    : "resource";

  const backToTarget = () => {
    setTarget(null);
    setRouteChoice(seaOnly ? "sea" : null);
    setTransitVia(null);
    setResourceName(null);
    setPreview(null);
    setRouteResult(null);
  };

  const backToRoute = () => {
    setRouteChoice(null);
    setTransitVia(null);
    setResourceName(null);
    setPreview(null);
  };

  const backToTransit = () => {
    setTransitVia(null);
    setResourceName(null);
    setPreview(null);
  };

  const backFromResource = routeChoice === "transit" ? backToTransit : backToRoute;

  const handleSend = async () => {
    if (!preview || preview === "loading" || preview.networkError || !preview.ok) return;
    const sourceQ = quarterByCode[supplierCode];
    const destQ = quarterByCode[requesterCode];
    if (!sourceQ || !destQ || !selectedItem) return;

    setSending(true);
    try {
      await api.createRequest({
        source_quarter_id: sourceQ.id,
        destination_quarter_id: destQ.id,
        resource_type_id: selectedItem.resourceTypeId,
        quantity,
        prefer_maritime: preferMaritime,
        transit_via: routeChoice === "transit" ? quarterByCode[transitVia]?.id : undefined,
      });
      setRouteResult({
        ok: true,
        route_type: preview.route_type,
        transit_via: preview.transit_via,
        deprioritized_behind_xeno: preview.deprioritized_behind_xeno,
      });
    } catch (err) {
      setRouteResult({ ok: false, reason: err.code, message: err.message });
    } finally {
      setSending(false);
    }
  };

  const transitDistrict = (result) =>
    DISTRICTS.find((d) => quarterByCode[d.id]?.id === result.transit_via);

  const routeTypeLabel = (result) => {
    if (result.route_type === "direct") return "directly";
    if (result.route_type === "maritime") return "by maritime route";
    if (result.route_type === "transit") {
      const via = transitDistrict(result);
      return `via ${via?.name ?? `quarter #${result.transit_via}`}`;
    }
    return "";
  };

  // destination always approves, transit quarter also approves
  const pendingApprovals = (result) => {
    const names = [getDistrict(requesterCode)?.name].filter(Boolean);
    if (result.route_type === "transit") {
      const via = transitDistrict(result);
      if (via) names.push(`${via.name} (as the transit quarter)`);
    }
    return names;
  };

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={`${verb} ${origin.name}`}
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {origin.name}: {verb.toLowerCase()}...
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close"
            className="rounded-full p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-700 dark:hover:text-gray-200"
          >
            ✕
          </button>
        </div>

        {step === "target" && (
          <ul className="divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
            {targetOptions.map((d) => (
              <li key={d.id}>
                <button
                  type="button"
                  onClick={() => setTarget(d.id)}
                  className="block w-full px-3 py-2 text-left text-base text-gray-800 hover:bg-[#FFF3D9] dark:text-gray-200 dark:hover:bg-gray-700"
                >
                  {d.name}
                </button>
              </li>
            ))}
            {targetOptions.length === 0 && (
              <li className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                {quartersStatus === "loading"
                  ? "Loading zones…"
                  : `No maritime-connected zone for ${origin.name}.`}
              </li>
            )}
          </ul>
        )}

        {step === "route" && (
          <>
            <button type="button" onClick={backToTarget} className="mb-2 text-sm text-[#B36B00] hover:underline dark:text-[#FFC966]">
              ← back
            </button>
            <div className="divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
              {ROUTES.map((r) => {
                const enabled = r.id === "direct" ? adjacent : r.id === "transit" ? !adjacent : bothHaveSea;
                return (
                  <button
                    key={r.id}
                    type="button"
                    disabled={!enabled}
                    onClick={() => setRouteChoice(r.id)}
                    className={`block w-full px-3 py-2 text-left text-base ${
                      enabled
                        ? "text-gray-800 hover:bg-[#FFF3D9] dark:text-gray-200 dark:hover:bg-gray-700"
                        : "cursor-not-allowed text-gray-300 dark:text-gray-600"
                    }`}
                  >
                    {r.label}
                  </button>
                );
              })}
            </div>
          </>
        )}

        {step === "transit" && (
          <>
            <button type="button" onClick={backToRoute} className="mb-2 text-sm text-[#B36B00] hover:underline dark:text-[#FFC966]">
              ← back
            </button>
            <div className="divide-y divide-gray-200 rounded-md border border-gray-200 dark:divide-gray-700 dark:border-gray-700">
              {transitOptions(supplierCode, requesterCode).map((code) => (
                <button
                  key={code}
                  type="button"
                  onClick={() => setTransitVia(code)}
                  className="block w-full px-3 py-2 text-left text-base text-gray-800 hover:bg-[#FFF3D9] dark:text-gray-200 dark:hover:bg-gray-700"
                >
                  {getDistrict(code)?.name}
                </button>
              ))}
              {transitOptions(supplierCode, requesterCode).length === 0 && (
                <p className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
                  No district is adjacent to both {getDistrict(supplierCode)?.name} and{" "}
                  {getDistrict(requesterCode)?.name}.
                </p>
              )}
            </div>
          </>
        )}

        {step === "resource" && (
          <>
            <button type="button" onClick={backFromResource} className="mb-2 text-sm text-[#B36B00] hover:underline dark:text-[#FFC966]">
              ← back
            </button>
            <p className="mb-3 text-sm text-gray-600 dark:text-gray-400">
              {origin.name} {direction === "from" ? "←" : "→"} {getDistrict(target)?.name},{" "}
              {routeChoice === "transit"
                ? `via ${getDistrict(transitVia)?.name}`
                : ROUTES.find((r) => r.id === routeChoice)?.label.toLowerCase()}
            </p>

            {stockStatus === "loading" && <p className="text-sm text-gray-500 dark:text-gray-400">Loading resources…</p>}
            {stockStatus === "error" && (
              <p className="text-sm text-[#dc2626] dark:text-red-400">Couldn't reach the backend.</p>
            )}

            {stockStatus === "ready" && (
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
                    Quantity (retention floor: {selectedItem.retentionMin}, max: {maxSendable})
                    <input
                      type="number"
                      min={1}
                      max={maxSendable}
                      value={quantity}
                      onChange={(e) => setQuantity(Number(e.target.value))}
                      className="mt-1 w-full rounded-md border border-gray-300 px-2 py-1.5 text-base dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
                    />
                  </label>
                )}

                {selectedItem && (
                  <div className="mb-3 rounded-md bg-gray-50 px-3 py-2 text-sm dark:bg-gray-700/50">
                    <span className="font-medium text-gray-700 dark:text-gray-300">How: </span>
                    {preview === "loading" && <span className="text-gray-500 dark:text-gray-400">checking…</span>}
                    {preview && preview !== "loading" && preview.networkError && (
                      <span className="text-[#dc2626] dark:text-red-400">{preview.message || "couldn't reach the backend"}</span>
                    )}
                    {preview && preview !== "loading" && !preview.networkError && preview.ok && (
                      <span className="text-[#15803d] dark:text-green-400">
                        {routeTypeLabel(preview)}
                        {preview.deprioritized_behind_xeno && " — behind Xeno's own needs"}
                      </span>
                    )}
                    {preview && preview !== "loading" && !preview.networkError && !preview.ok && (
                      <span className="text-[#b91c1c] dark:text-red-400">
                        rejected — {REASON_LABELS[preview.reason] ?? preview.reason}: {preview.message}
                      </span>
                    )}
                  </div>
                )}

                <button
                  type="button"
                  disabled={
                    !selectedItem ||
                    quantity < 1 ||
                    quantity > maxSendable ||
                    !preview ||
                    preview === "loading" ||
                    preview.networkError ||
                    !preview.ok ||
                    sending
                  }
                  onClick={handleSend}
                  className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2 text-base font-bold text-white hover:bg-[#D98C00] disabled:cursor-not-allowed disabled:bg-gray-300"
                >
                  {sending ? "Sending…" : "Send request"}
                </button>
              </>
            )}
          </>
        )}

        {step === "result" && routeResult && (
          <div className="text-center">
            {routeResult.ok ? (
              <>
                <p className="mb-1 text-base font-semibold text-[#15803d] dark:text-green-400">Request submitted</p>
                <p className="mb-4 text-base text-gray-800 dark:text-gray-200">
                  {quantity} × {resourceName}, {origin.name} {direction === "from" ? "←" : "→"}{" "}
                  {getDistrict(target)?.name} ({routeTypeLabel(routeResult)}).
                  <br />
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    Pending approval from {pendingApprovals(routeResult).join(" and ")}.
                  </span>
                  {routeResult.deprioritized_behind_xeno && (
                    <>
                      <br />
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        Transits through Xeno — processed after Xeno's own needs.
                      </span>
                    </>
                  )}
                </p>
              </>
            ) : (
              <>
                <p className="mb-1 text-base font-semibold text-[#b91c1c] dark:text-red-400">
                  Rejected — {REASON_LABELS[routeResult.reason] ?? routeResult.reason}
                </p>
                <p className="mb-4 text-sm text-gray-700 dark:text-gray-300">{routeResult.message}</p>
              </>
            )}
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setRouteResult(null)}
                className="w-full rounded-md border border-gray-300 py-2 text-base font-semibold text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                ← try again
              </button>
              <button
                type="button"
                onClick={onClose}
                className="w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] py-2 text-base font-bold text-white hover:bg-[#D98C00]"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
