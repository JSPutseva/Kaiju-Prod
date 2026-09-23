import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { getDistrict } from "../data/districts";

const ACTIONS = [
  { id: "reserve", label: "Reserve..." },
  { id: "send", label: "Send resources to" },
  { id: "get", label: "Get resources from" },
  { id: "maritime", label: "Maritime route" },
  { id: "view", label: "View the zone" },
];

const GAP = 14;
const MARGIN = 8;

// anchor: { x, top, bottom } from getBoundingClientRect()
export default function ZoneActionMenu({ districtId, anchor, onSelectAction, onClose }) {
  const ref = useRef(null);
  const district = getDistrict(districtId);
  const [placement, setPlacement] = useState(null);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const h = el.offsetHeight;
    const w = el.offsetWidth;

    const fitsBelow = anchor.bottom + GAP + h <= window.innerHeight - MARGIN;
    const openUp = !fitsBelow;
    const top = openUp ? anchor.top - GAP - h : anchor.bottom + GAP;
    const left = Math.max(MARGIN, Math.min(anchor.x - w / 2, window.innerWidth - w - MARGIN));

    setPlacement({ top, left, openUp, arrowLeft: anchor.x - left });
  }, [anchor]);

  useEffect(() => {
    const onClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) onClose?.();
    };
    const onKeyDown = (e) => e.key === "Escape" && onClose?.();
    document.addEventListener("mousedown", onClickOutside);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onClickOutside);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose]);

  if (!district) return null;

  return (
    <div
      ref={ref}
      role="menu"
      aria-label={`${district.name} actions`}
      className="fixed z-50 w-60 rounded-md border border-[#FBD98A] bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800"
      style={{
        left: placement?.left ?? anchor.x,
        top: placement?.top ?? anchor.bottom,
        visibility: placement ? "visible" : "hidden",
      }}
    >
      <div
        className={`absolute h-3 w-3 -translate-x-1/2 rotate-45 border-[#FBD98A] bg-white dark:border-gray-700 dark:bg-gray-800 ${
          placement?.openUp
            ? "top-full -translate-y-1/2 border-b border-r"
            : "bottom-full translate-y-1/2 border-l border-t"
        }`}
        style={{ left: placement?.arrowLeft ?? "50%" }}
      />
      <p className="border-b border-gray-100 px-3 py-1.5 text-sm font-bold uppercase tracking-wide text-gray-400 dark:border-gray-700 dark:text-gray-500">
        {district.name}
      </p>
      {ACTIONS.map((action) => (
        <button
          key={action.id}
          type="button"
          role="menuitem"
          onClick={() => onSelectAction(action.id)}
          className="block w-full px-3 py-2 text-left text-base text-gray-800 hover:bg-[#FFF3D9] dark:text-gray-200 dark:hover:bg-gray-700"
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}
