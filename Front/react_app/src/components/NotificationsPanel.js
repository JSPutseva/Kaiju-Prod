import { useCallback, useEffect, useState } from "react";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useQuarters } from "../context/QuartersContext";
import { useWebSocket } from "../context/WebSocketContext";
import { useTheme } from "../context/ThemeContext";
import { LEVEL_NAMES } from "../context/DisasterLevelContext";
import { getDistrictTextColor } from "../data/districts";
import { api } from "../api/client";
import OperationalCalendarModal from "./OperationalCalendarModal";

function LevelAlertCard({ alert }) {
  const { theme } = useTheme();
  const zoneColor = getDistrictTextColor(alert.quarterCode, theme);

  return (
    <div className="rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-900/50 dark:bg-red-950/40">
      <p className="mb-1 text-base font-bold text-[#dc2626] dark:text-red-400">
        Kaiju attack
      </p>
      <p className="text-base text-gray-800 dark:text-gray-200">
        <span className="font-bold" style={{ color: zoneColor }}>{alert.quarterName}</span> hit —
        Level {alert.level} ({alert.levelName})
        {alert.changedByName && (
          <>
            {" "}by <span className="font-bold">{alert.changedByName}</span>
          </>
        )}
      </p>
    </div>
  );
}

function DeniedRequestCard({
  request,
  sourceName,
  sourceCode,
  destinationName,
  destinationCode,
  resourceName,
  deciderName,
}) {
  const { theme } = useTheme();
  const sourceColor = getDistrictTextColor(sourceCode, theme);
  const destinationColor = getDistrictTextColor(destinationCode, theme);

  return (
    <div className="rounded-md border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
      <p className="mb-2 text-base text-[#dc2626] dark:text-red-400">Your request was denied</p>
      <p className="text-base text-gray-800 dark:text-gray-200">
        {request.quantity}× <span className="italic">{resourceName}</span>,{" "}
        <span className="font-bold" style={{ color: sourceColor }}>{sourceName}</span>
        {" → "}
        <span className="font-bold" style={{ color: destinationColor }}>{destinationName}</span>
        <br />
        denied by <span className="font-bold">{deciderName}</span>
        {request.rejection_reason && <>: "{request.rejection_reason}"</>}
      </p>
    </div>
  );
}

function TransferRequestCard({
  request,
  requesterName,
  destinationName,
  destinationCode,
  transitViaName,
  transitViaCode,
  resourceName,
  onApprove,
  onDeny,
}) {
  const { theme } = useTheme();
  const destinationColor = getDistrictTextColor(destinationCode, theme);
  const transitViaColor = getDistrictTextColor(transitViaCode, theme);
  const [denying, setDenying] = useState(false);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);

  const handleApprove = async () => {
    setBusy(true);
    setActionError(null);
    try {
      await onApprove(request.id);
    } catch (err) {
      setActionError(err.message);
    } finally {
      setBusy(false);
    }
  };

  const submitDeny = async () => {
    if (!reason.trim()) return;
    setBusy(true);
    setActionError(null);
    try {
      await onDeny(request.id, reason.trim());
    } catch (err) {
      setActionError(err.message);
      setBusy(false);
    }
  };

  return (
    <div className="rounded-md border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-800">
      <p className="mb-2 text-base text-[#B36B00] dark:text-[#FFC966]">
        {request.requisition ? "CD requisition" : "Incoming transfer request"}
      </p>
      <p className="text-base text-gray-800 dark:text-gray-200">
        <span className="font-bold">{requesterName}</span> wants {request.quantity}× <span className="italic">{resourceName}</span>
        <br />
        sent to <span className="font-bold" style={{ color: destinationColor }}>{destinationName}</span>
        {transitViaName && (
          <>
            {" "}via <span className="font-bold" style={{ color: transitViaColor }}>{transitViaName}</span>
          </>
        )}
      </p>

      {actionError && (
        <p className="mt-1.5 text-sm text-[#dc2626] dark:text-red-400">{actionError}</p>
      )}

      {denying ? (
        <div className="mt-2 flex items-center gap-1.5">
          <input
            autoFocus
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Reason for denial…"
            className="min-w-0 flex-1 rounded-md border border-gray-300 px-2 py-1 text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
          />
          <button
            type="button"
            disabled={busy || !reason.trim()}
            onClick={submitDeny}
            className="rounded-md bg-[#dc2626] px-2 py-1 text-xs font-bold text-white hover:bg-[#b91c1c] disabled:opacity-50"
          >
            Deny
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={() => {
              setDenying(false);
              setReason("");
              setActionError(null);
            }}
            className="rounded-md border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-600 hover:bg-gray-50 disabled:opacity-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Cancel
          </button>
        </div>
      ) : (
        <div className="mt-2 flex justify-end gap-2">
          <button
            type="button"
            disabled={busy}
            onClick={() => setDenying(true)}
            aria-label="Deny request"
            className="flex h-7 w-7 items-center justify-center rounded-full text-red-600 hover:bg-red-50 disabled:opacity-50 dark:text-red-400 dark:hover:bg-red-900/40"
          >
            ✕
          </button>
          <button
            type="button"
            disabled={busy}
            onClick={handleApprove}
            aria-label="Approve request"
            className="flex h-7 w-7 items-center justify-center rounded-full text-green-600 hover:bg-green-50 disabled:opacity-50 dark:text-green-400 dark:hover:bg-green-900/40"
          >
            ✓
          </button>
        </div>
      )}
    </div>
  );
}

export default function NotificationsPanel() {
  const [calendarOpen, setCalendarOpen] = useState(false);
  const { roleCode, quarterId, user } = useCurrentUser();
  const { byCode: quarterByCode, status: quartersStatus } = useQuarters();
  // level alerts are captured app-wide in WebSocketContext (not locally
  // here), so one triggered from another page — e.g. the Kaiju POV page —
  // isn't lost just because this panel wasn't mounted at that moment
  const { subscribe, levelAlerts } = useWebSocket();

  const [requests, setRequests] = useState([]);
  const [myDeniedRequests, setMyDeniedRequests] = useState([]);
  const [nameById, setNameById] = useState({});
  const [resourceNameById, setResourceNameById] = useState({});
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [error, setError] = useState(null);

  // only QC (own quarter, as the source being asked to give up resources)
  // and CD (city-wide) can decide on requests — see
  // Back/app/routers/requests.py:_get_pending_request. GET /requests itself
  // is unfiltered (it also feeds the city-wide operational calendar), so the
  // "can I act on this" scoping happens here instead.
  const canDecide = roleCode === "QC" || roleCode === "CD";

  // user names are needed by everyone (request cards AND attack alerts, the
  // latter shown regardless of role), so this isn't gated behind canDecide
  useEffect(() => {
    api
      .listUsers()
      .then((users) => setNameById(Object.fromEntries(users.map((u) => [u.id, u.name]))))
      .catch(() => {
        // non-critical: cards fall back to "Unknown" / omit the "by X" clause
      });
  }, []);

  // unconditional: GET /requests needs no special role, and "my denied
  // requests" below applies to anyone who can create a request, not just
  // roles that can decide on one
  const load = useCallback(() => {
    if (quartersStatus !== "ready") return;

    setStatus((s) => (s === "ready" ? s : "loading"));
    Promise.all([api.getRequests(), api.getResourceTypes()])
      .then(([reqs, resourceTypes]) => {
        const actionable = canDecide
          ? reqs.filter(
              (r) =>
                r.status === "PENDING" &&
                (roleCode === "CD" || r.source_quarter_id === quarterId)
            )
          : [];
        const myDenied = reqs.filter(
          (r) => r.status === "REJECTED" && r.requester_id === user?.id
        );
        setRequests(actionable);
        setMyDeniedRequests(myDenied);
        setResourceNameById(Object.fromEntries(resourceTypes.map((rt) => [rt.id, rt.name])));
        setStatus("ready");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, [canDecide, quartersStatus, roleCode, quarterId, user?.id]);

  const quarterNameById = Object.fromEntries(
    Object.values(quarterByCode).map((q) => [q.id, q.name])
  );
  const quarterCodeById = Object.fromEntries(
    Object.entries(quarterByCode).map(([code, q]) => [q.id, code])
  );

  useEffect(() => {
    load();
    const unsubscribe = subscribe((event) => {
      if (["REQUEST_CREATED", "REQUEST_APPROVED", "REQUEST_DENIED"].includes(event.type)) {
        load();
      }
    });
    return unsubscribe;
  }, [load, subscribe]);

  const handleApprove = async (requestId) => {
    await api.approveRequest(requestId);
    load();
  };

  const handleDeny = async (requestId, reason) => {
    await api.denyRequest(requestId, reason);
    load();
  };

  // one time-sorted feed: pending requests (only for roles that can act on
  // them), your own denied requests (any role), and attack/level-change
  // alerts (shown to everyone — an attack affects the whole city, not just
  // whoever can approve a transfer)
  const feedItems = [
    ...(canDecide && status === "ready"
      ? requests.map((r) => ({
          kind: "request",
          key: `req-${r.id}`,
          time: new Date(r.created_at).getTime(),
          request: r,
        }))
      : []),
    ...(status === "ready"
      ? myDeniedRequests.map((r) => ({
          kind: "myDenied",
          key: `denied-${r.id}`,
          time: new Date(r.decided_at ?? r.updated_at).getTime(),
          request: r,
        }))
      : []),
    ...levelAlerts.map((a) => ({
      kind: "alert",
      key: a.id,
      time: a.timestamp,
      alert: {
        quarterName: quarterNameById[a.quarter_id] ?? "?",
        quarterCode: quarterCodeById[a.quarter_id],
        level: a.level,
        levelName: LEVEL_NAMES[a.level] ?? a.level,
        changedByName: a.changed_by_id ? nameById[a.changed_by_id] : null,
      },
    })),
  ].sort((a, b) => b.time - a.time);

  return (
    <div className="flex h-[80vh] flex-col overflow-hidden rounded-lg border border-[#FBD98A] shadow-sm dark:border-gray-700">
      <h2 className="bg-white border-b border-[#FBD98A] px-4 py-3 text-center text-xl font-semibold text-gray-900 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-100">
        Notifs
      </h2>

      <div className="relative flex-1 overflow-y-auto bg-[#fff9ea] dark:bg-[#3a362d]">
        <div
          className="pointer-events-none absolute inset-0 bg-repeat-space opacity-10"
          style={{ backgroundImage: "url(/kaiju_fone.png)", backgroundSize: "40px auto" }}
          aria-hidden="true"
        />
        <div className="relative space-y-2 p-4">
          {status === "loading" && (
            <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Loading…</p>
          )}

          {status === "error" && (
            <p className="py-6 text-center text-sm text-[#dc2626] dark:text-red-400">
              Couldn't load requests: {error}
            </p>
          )}

          {feedItems.length === 0 && status === "ready" && (
            <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">
              Nothing to show.
            </p>
          )}

          {feedItems.map((item) => {
            if (item.kind === "alert") {
              return <LevelAlertCard key={item.key} alert={item.alert} />;
            }
            if (item.kind === "myDenied") {
              return (
                <DeniedRequestCard
                  key={item.key}
                  request={item.request}
                  sourceName={quarterNameById[item.request.source_quarter_id] ?? "?"}
                  sourceCode={quarterCodeById[item.request.source_quarter_id]}
                  destinationName={quarterNameById[item.request.destination_quarter_id] ?? "?"}
                  destinationCode={quarterCodeById[item.request.destination_quarter_id]}
                  resourceName={resourceNameById[item.request.resource_type_id] ?? "resource"}
                  deciderName={
                    item.request.decided_by_id
                      ? nameById[item.request.decided_by_id] ?? "Someone"
                      : "Someone"
                  }
                />
              );
            }
            return (
              <TransferRequestCard
                key={item.key}
                request={item.request}
                requesterName={nameById[item.request.requester_id] ?? "Unknown"}
                destinationName={quarterNameById[item.request.destination_quarter_id] ?? "?"}
                destinationCode={quarterCodeById[item.request.destination_quarter_id]}
                transitViaName={
                  item.request.transit_via_id
                    ? quarterNameById[item.request.transit_via_id] ?? null
                    : null
                }
                transitViaCode={
                  item.request.transit_via_id
                    ? quarterCodeById[item.request.transit_via_id]
                    : undefined
                }
                resourceName={resourceNameById[item.request.resource_type_id] ?? "resource"}
                onApprove={handleApprove}
                onDeny={handleDeny}
              />
            );
          })}
        </div>
      </div>

      <button
        type="button"
        onClick={() => setCalendarOpen(true)}
        className="w-full bg-[#F47E00] dark:bg-[#F8A201] py-3 text-base font-bold text-white hover:bg-[#D98C00]"
      >
        go to Operational calendar
      </button>

      {calendarOpen && (
        <OperationalCalendarModal onClose={() => setCalendarOpen(false)} />
      )}
    </div>
  );
}
