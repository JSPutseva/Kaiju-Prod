import { useDisasterLevel } from "../context/DisasterLevelContext";

// red glow at the viewport edges, shown only at level 5
export default function DisasterFrame() {
  const { isMaxLevel } = useDisasterLevel();

  return (
    <div
      aria-hidden="true"
      className={`pointer-events-none fixed inset-0 z-50 transition-opacity duration-500 ${
        isMaxLevel ? "opacity-100" : "opacity-0"
      }`}
      style={{
        background: [
          "linear-gradient(to bottom, rgba(220,38,38,0.85), rgba(220,38,38,0) 6%)",
          "linear-gradient(to top, rgba(220,38,38,0.85), rgba(220,38,38,0) 6%)",
          "linear-gradient(to right, rgba(220,38,38,0.85), rgba(220,38,38,0) 3.5%)",
          "linear-gradient(to left, rgba(220,38,38,0.85), rgba(220,38,38,0) 3.5%)",
        ].join(", "),
      }}
    />
  );
}
