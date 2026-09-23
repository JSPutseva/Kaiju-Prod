import { useEffect, useState } from "react";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useQuarters } from "../context/QuartersContext";
import { getRole } from "../data/roles";
import { api } from "../api/client";

const ROLE_CODES = ["QC", "LC", "CD"];

function RoleSwitcher({ value, onChange, disabled }) {
  return (
    <div className="flex overflow-hidden rounded-full border border-gray-300 shadow-sm dark:border-gray-600">
      {ROLE_CODES.map((code) => (
        <button
          key={code}
          type="button"
          disabled={disabled}
          onClick={() => onChange(code)}
          className={`px-3.5 py-1.5 text-sm font-bold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
            value === code
              ? "bg-[#F47E00] dark:bg-[#F8A201] text-white"
              : "bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          }`}
        >
          {code}
        </button>
      ))}
    </div>
  );
}

// QC: single quarter. LC: any number of quarters. CD: city-wide, no picker.
function QuarterPicker({ role, quarterIds, quarters, disabled, onChange }) {
  if (role === "CD") {
    return (
      <span className="inline-block rounded-full bg-gray-100 px-3 py-1 text-xs font-semibold text-gray-500 dark:bg-gray-700 dark:text-gray-400">
        City-wide
      </span>
    );
  }

  if (role === "QC") {
    return (
      <select
        value={quarterIds[0] ?? ""}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value ? [Number(e.target.value)] : [])}
        className="rounded-md border border-gray-300 bg-white px-2 py-1 text-sm text-gray-700 disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200"
      >
        <option value="">No quarter</option>
        {quarters.map((q) => (
          <option key={q.id} value={q.id}>
            {q.name}
          </option>
        ))}
      </select>
    );
  }

  // LC: multi-select as toggle chips
  const toggle = (id) => {
    const next = quarterIds.includes(id)
      ? quarterIds.filter((v) => v !== id)
      : [...quarterIds, id];
    onChange(next);
  };

  return (
    <div className="flex flex-wrap gap-1.5">
      {quarters.map((q) => {
        const active = quarterIds.includes(q.id);
        return (
          <button
            key={q.id}
            type="button"
            disabled={disabled}
            onClick={() => toggle(q.id)}
            className={`rounded-full border px-2.5 py-1 text-xs font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
              active
                ? "border-[#F47E00] bg-[#FFF3D9] text-[#F47E00] dark:border-[#FFC966] dark:bg-[#4A3300] dark:text-[#FFC966]"
                : "border-gray-300 bg-white text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
            }`}
          >
            {q.name}
          </button>
        );
      })}
      {quarters.length === 0 && <span className="text-xs text-gray-400 dark:text-gray-500">No quarters loaded.</span>}
    </div>
  );
}

export default function ManageRolesModal({ onClose }) {
  const { user: me, setRoleCode: setMyRoleCode } = useCurrentUser();
  const { byCode: quarterByCode } = useQuarters();
  const quarters = Object.values(quarterByCode).sort((a, b) => a.name.localeCompare(b.name));

  const [users, setUsers] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error
  const [query, setQuery] = useState("");
  const [pendingId, setPendingId] = useState(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState(null);
  const [error, setError] = useState(null);

  const iAmCD = me?.role === "CD";

  useEffect(() => {
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  useEffect(() => {
    api
      .listUsers()
      .then((rows) => {
        setUsers(rows);
        setStatus("ready");
      })
      .catch((err) => {
        setError(err.message);
        setStatus("error");
      });
  }, []);

  const updateUser = async (user, { role, quarterIds }) => {
    setPendingId(user.id);
    setError(null);
    // CD is city-wide (no quarters); QC is scoped to at most one.
    const normalizedQuarterIds =
      role === "CD" ? [] : role === "QC" ? quarterIds.slice(0, 1) : quarterIds;
    try {
      const updated = await api.assignRole(user.id, {
        role,
        quarter_ids: normalizedQuarterIds,
      });
      setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));
      if (updated.id === me?.id) {
        setMyRoleCode(updated.role);
      }
    } catch (err) {
      setError(err.message || "Unable to update this user.");
    } finally {
      setPendingId(null);
    }
  };

  const handleDelete = async (user) => {
    setPendingId(user.id);
    setError(null);
    try {
      await api.deleteUser(user.id);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
    } catch (err) {
      setError(err.message || "Unable to delete this user.");
    } finally {
      setPendingId(null);
      setConfirmDeleteId(null);
    }
  };

  const q = query.trim().toLowerCase();
  const filteredUsers = users.filter(
    (u) => !q || u.name.toLowerCase().includes(q) || (u.role ?? "").toLowerCase().includes(q)
  );

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Manage roles"
        onClick={(e) => e.stopPropagation()}
        className="w-full max-w-xl rounded-xl bg-white p-6 shadow-2xl dark:bg-gray-800"
      >
        <div className="mb-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Manage roles</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">Assign each officer a role and their quarter scope.</p>
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

        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name or role (QC, LC, CD)…"
          className="mb-4 w-full rounded-md border border-gray-300 px-3 py-2 text-base focus:border-[#F47E00] dark:focus:border-[#F8A201] focus:outline-none dark:border-gray-600 dark:bg-gray-900 dark:text-gray-100"
        />

        {status === "loading" && <p className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">Loading users…</p>}
        {status === "error" && (
          <p className="py-6 text-center text-sm text-[#dc2626] dark:text-red-400">Couldn't load users: {error}</p>
        )}

        {status === "ready" && (
          <ul className="max-h-[60vh] space-y-2 overflow-y-auto">
            {filteredUsers.map((u) => {
              const role = getRole(u.role);
              const isPending = pendingId === u.id;
              return (
                <li
                  key={u.id}
                  className="flex items-center gap-4 rounded-lg border border-gray-200 bg-gray-50/60 p-3 transition-shadow hover:shadow-sm dark:border-gray-700 dark:bg-gray-700/30"
                >
                  {role ? (
                    <img
                      src={role.avatar}
                      alt={role.label}
                      className="h-11 w-11 shrink-0 rounded-full bg-white object-contain p-1.5 shadow-sm dark:bg-gray-800"
                    />
                  ) : (
                    <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-400 dark:bg-indigo-900/40 dark:text-indigo-300">
                      ?
                    </span>
                  )}

                  <div className="min-w-0 flex-1">
                    <p className="truncate text-base font-semibold text-gray-900 dark:text-gray-100">
                      {u.name}
                      {u.id === me?.id && (
                        <span className="ml-1.5 text-sm font-normal text-gray-400 dark:text-gray-500">(you)</span>
                      )}
                    </p>
                    <p className="truncate text-xs text-gray-400 dark:text-gray-500">{u.email}</p>
                    <div className="mt-1.5">
                      <QuarterPicker
                        role={u.role}
                        quarterIds={u.quarter_ids}
                        quarters={quarters}
                        disabled={isPending}
                        onChange={(quarterIds) => updateUser(u, { role: u.role, quarterIds })}
                      />
                    </div>
                  </div>

                  <RoleSwitcher
                    value={u.role}
                    disabled={isPending}
                    onChange={(role) => updateUser(u, { role, quarterIds: u.quarter_ids })}
                  />

                  {iAmCD && u.id !== me?.id && (
                    <>
                      {confirmDeleteId === u.id ? (
                        <div className="flex shrink-0 items-center gap-1.5">
                          <span className="text-xs text-gray-500 dark:text-gray-400">Delete?</span>
                          <button
                            type="button"
                            disabled={isPending}
                            onClick={() => handleDelete(u)}
                            className="rounded-md bg-[#dc2626] px-2 py-1 text-xs font-bold text-white hover:bg-[#b91c1c] disabled:opacity-50"
                          >
                            Yes
                          </button>
                          <button
                            type="button"
                            disabled={isPending}
                            onClick={() => setConfirmDeleteId(null)}
                            className="rounded-md border border-gray-300 px-2 py-1 text-xs font-semibold text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <button
                          type="button"
                          disabled={isPending}
                          onClick={() => setConfirmDeleteId(u.id)}
                          aria-label={`Delete ${u.name}`}
                          className="shrink-0 rounded-full p-2 text-gray-400 hover:bg-red-50 hover:text-[#dc2626] disabled:cursor-not-allowed disabled:opacity-50 dark:text-gray-500 dark:hover:bg-red-900/30 dark:hover:text-red-400"
                        >
                          <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M4 7h16M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2m-8 0v13a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V7" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </button>
                      )}
                    </>
                  )}
                </li>
              );
            })}
            {filteredUsers.length === 0 && (
              <li className="py-6 text-center text-sm text-gray-500 dark:text-gray-400">No users match "{query}".</li>
            )}
          </ul>
        )}

        {error && status === "ready" && (
          <p className="mt-3 text-sm text-[#dc2626] dark:text-red-400">{error}</p>
        )}

        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
          QC is scoped to one quarter, LC can span several, CD is city-wide. The first City Director
          can self-assign; after that, only a City Director can reassign roles.
        </p>
      </div>
    </div>
  );
}
