import { DISTRICTS } from "../data/districts";
import { useCurrentUser } from "../context/CurrentUserContext";

export default function Navigation({ onSelectZone, onManageRoles }) {
  const { roleCode } = useCurrentUser();

  return (
    <nav className="px-4 py-3">
      <h2 className="mb-2 text-xl font-semibold text-gray-900 dark:text-gray-100">Navigation</h2>
      <p className="mb-2 text-sm font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
        Zones
      </p>
      <ul className="space-y-2">
        {DISTRICTS.map((d) => (
          <li key={d.id}>
            <button
              type="button"
              onClick={(e) => onSelectZone?.(d.id, e)}
              className="flex w-full items-center gap-2 rounded-md border border-[#FBD98A] bg-white px-3 py-2 text-left text-base font-medium text-gray-800 shadow-sm hover:border-[#F0B94D] hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:border-gray-500 dark:hover:bg-gray-700"
            >
              <span className={`h-2.5 w-2.5 shrink-0 rounded-full bg-${d.color}`} />
              {d.name}
            </button>
          </li>
        ))}
      </ul>

      {(roleCode === "CD" || roleCode === null) && (
        <button
          type="button"
          onClick={onManageRoles}
          className="mt-4 w-full rounded-md bg-[#F47E00] dark:bg-[#F8A201] px-3 py-2 text-base font-semibold text-white shadow-sm hover:bg-[#D98C00]"
        >
          {roleCode === null ? "Assign my role" : "Manage roles"}
        </button>
      )}
    </nav>
  );
}
