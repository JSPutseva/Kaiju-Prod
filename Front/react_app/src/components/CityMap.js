import { DISTRICTS } from "../data/districts";
import { useTheme } from "../context/ThemeContext";

const FILL = {
  "district-a": "#E63946",
  "district-e": "#4CAF3C",
  "district-w": "#FFA055",
  "district-x": "#F4E03A",
  "district-z": "#6EC6E8",
};

// district shapes (hand-approximated, not a traced map)
const SHAPES = {
  A: "9,12 20,7 28,6 40,4 55,4 58,10 59,18 63,24 61,32 57,36 52,38 48,44 44,48 39,52 35,56 28,54 22,52 16,50 12,46 8,40 6,34 8,28 5,22 8,16",
  E: "58,4 70,3 82,5 94,9 98,15 96,22 99,28 95,34 97,40 92,46 94,52 88,50 82,52 76,50 70,54 66,50 62,44 58,38 61,32 59,26 62,20 58,14",
  W: "7,49 16,45 24,48 33,50 38,55 40,62 38,70 41,77 38,84 40,91 33,95 24,97 15,94 9,88 5,80 7,72 4,64 6,57",
  X: "39,42 47,38 55,37 62,39 66,45 65,52 67,58 60,63 52,65 44,62 38,57 36,50 37,46",
  Z: "41,66 50,62 58,60 66,58 74,56 82,55 90,54 93,60 90,66 94,71 90,77 93,83 88,88 90,93 82,95 74,93 66,95 58,93 50,94 44,91 40,85 42,78 39,72",
};

// matches tailwind.config.js's level.* colors
const LEVEL_COLORS = {
  1: "#6B7280",
  2: "#EAB308",
  3: "#F97316",
  4: "#DC2626",
  5: "#B91C1C",
};

// decorative piers (not clickable)
const PIERS = [
  { points: "84,38 88,37 88,39.5 84,40.5" },
  { points: "90,44 94,43 94,46 90,47" },
  { points: "79,61 82,60 82,62.5 79,63.5" },
  { points: "76,90 84,88 84,90.5 76,92.5" },
  { points: "68,92 75,90.5 75,93 68,94.5" },
];

// `selected` accepts either a single district id or an array, for pages
// that need to target more than one zone at once (e.g. the Kaiju POV page)
export default function CityMap({ selected, onSelect, levels, className = "w-full max-w-2xl mx-auto" }) {
  const { theme } = useTheme();
  const dark = theme === "dark";
  const seaFill = dark ? "#0f2436" : "#BFE3F5";
  const pierFill = dark ? "#2d5170" : "#8FB9CF";
  const outline = dark ? "#e5e7eb" : "#111827";
  const badgeText = dark ? "#111827" : "#ffffff";

  const isSelected = (id) =>
    Array.isArray(selected) ? selected.includes(id) : selected === id;

  return (
    <svg
      viewBox="0 0 100 100"
      role="img"
      aria-label="Map of Tokyork districts"
      className={className}
    >
      <rect x="0" y="0" width="100" height="100" fill={seaFill} rx="4" />
      {DISTRICTS.map((d) => (
        <polygon
          key={d.id}
          points={SHAPES[d.id]}
          fill={FILL[d.color]}
          stroke={outline}
          strokeWidth={isSelected(d.id) ? 1.6 : 0.6}
          strokeLinejoin="round"
          onClick={(e) => onSelect?.(d.id, e)}
          className="cursor-pointer transition-opacity hover:opacity-80"
        />
      ))}
      <g className="pointer-events-none" fill={pierFill} stroke={outline} strokeWidth="0.35">
        {PIERS.map((pier, i) => (
          <polygon key={i} points={pier.points} />
        ))}
      </g>
      {DISTRICTS.map((d) => {
        const points = SHAPES[d.id].split(" ").map((p) => p.split(",").map(Number));
        const cx = points.reduce((s, p) => s + p[0], 0) / points.length;
        const cy = points.reduce((s, p) => s + p[1], 0) / points.length;
        return (
          <text
            key={d.id}
            x={cx}
            y={cy}
            textAnchor="middle"
            dominantBaseline="middle"
            className="font-display pointer-events-none select-none"
            fontSize="11"
            fill={outline}
          >
            {d.id}
          </text>
        );
      })}
      {levels &&
        DISTRICTS.map((d) => {
          const level = levels[d.id];
          if (!level) return null;
          const points = SHAPES[d.id].split(" ").map((p) => p.split(",").map(Number));
          const cx = points.reduce((s, p) => s + p[0], 0) / points.length;
          const cy = points.reduce((s, p) => s + p[1], 0) / points.length;
          return (
            <g key={`level-${d.id}`} className="pointer-events-none">
              <circle cx={cx + 8} cy={cy - 8} r="5" fill={LEVEL_COLORS[level] ?? LEVEL_COLORS[1]} stroke={outline} strokeWidth="0.4" />
              <text
                x={cx + 8}
                y={cy - 8}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="6"
                fontWeight="700"
                fill={badgeText}
              >
                {level}
              </text>
            </g>
          );
        })}
    </svg>
  );
}
