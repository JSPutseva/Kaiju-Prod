import { LEVELS } from "../context/DisasterLevelContext";

// pill picker styled like the QC/LC/CD role switcher, for 1-5 disaster levels
export default function LevelSwitcher({ value, onChange }) {
  return (
    <div className="flex overflow-hidden rounded-full border border-gray-300 shadow-sm dark:border-gray-600">
      {LEVELS.map(({ level, name }) => (
        <button
          key={level}
          type="button"
          title={name}
          onClick={() => onChange(level)}
          className={`px-3.5 py-1.5 text-sm font-bold transition-colors ${
            value === level
              ? "bg-[#F47E00] dark:bg-[#F8A201] text-white"
              : "bg-white text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          }`}
        >
          {level}
        </button>
      ))}
    </div>
  );
}
