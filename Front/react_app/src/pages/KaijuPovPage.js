import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useQuarters } from "../context/QuartersContext";
import { useDisasterLevel } from "../context/DisasterLevelContext";
import { useTheme } from "../context/ThemeContext";
import { DISTRICTS, getDistrictTextColor } from "../data/districts";
import CityMap from "../components/CityMap";
import LevelSwitcher from "../components/LevelSwitcher";
import { api } from "../api/client";

export default function KaijuPovPage() {
  const navigate = useNavigate();
  const { roleCode } = useCurrentUser();
  const { byCode: quarterByCode, status: quartersStatus } = useQuarters();
  const { setLevel } = useDisasterLevel();
  const { theme } = useTheme();

  const [targets, setTargets] = useState([]);
  const [punchLevel, setPunchLevel] = useState(3);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [lastResult, setLastResult] = useState(null);

  const canPunch = roleCode === "CD";

  const toggleTarget = (code) => {
    setTargets((prev) =>
      prev.includes(code) ? prev.filter((c) => c !== code) : [...prev, code]
    );
  };

  const levelsByCode = Object.fromEntries(
    Object.entries(quarterByCode).map(([code, q]) => [code, q.disaster_level])
  );

  const handleUnleash = async () => {
    if (targets.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      const quarterIds = targets.map((code) => quarterByCode[code]?.id).filter(Boolean);
      await api.setDisasterLevel(quarterIds, punchLevel);
      setLevel(punchLevel);
      setLastResult({ targets: [...targets], level: punchLevel });
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="relative flex h-screen flex-col overflow-hidden bg-gray-50 dark:bg-gray-900">
      <div
        className="pointer-events-none absolute inset-0 bg-repeat-space opacity-10"
        style={{ backgroundImage: "url(/jaws_fone.png)", backgroundSize: "120px auto" }}
        aria-hidden="true"
      />
      <div className="relative flex h-full flex-col px-6 py-4">
        <div className="flex shrink-0 items-center justify-between">
          <h1 className="font-display text-4xl text-gray-900 dark:text-gray-100">Kaiju POV</h1>
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm font-semibold text-gray-600 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Back to dashboard
          </button>
        </div>

        {!canPunch && (
          <p className="mt-3 shrink-0 rounded-md border border-[#FBD98A] bg-[#fff9ea] px-4 py-2 text-center text-sm text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300">
            Only a City Director can trigger a disaster level change — you can still see each zone's current level below.
          </p>
        )}

        <p className="mt-3 shrink-0 text-center text-2xl font-bold  text-[#c97900] dark:text-gray-300">
          Annoyed by stupid people? Punish them!
        </p>

        <div className="flex min-h-0 flex-1 items-center justify-center py-2">
          {quartersStatus === "ready" && (
            <CityMap
              className="h-full w-auto max-w-full"
              selected={targets}
              onSelect={(id) => canPunch && toggleTarget(id)}
              levels={levelsByCode}
            />
          )}
        </div>

        <div className="flex shrink-0 flex-col items-center gap-2 pb-2">
          <div className="flex min-h-[1.5rem] flex-wrap justify-center gap-3">
            {targets.length === 0 ? (
              <span className="text-sm text-gray-400 dark:text-gray-500">No zones targeted</span>
            ) : (
              targets.map((code) => (
                <span
                  key={code}
                  className="font-bold"
                  style={{ color: getDistrictTextColor(code, theme) }}
                >
                  {DISTRICTS.find((d) => d.id === code)?.name}
                </span>
              ))
            )}
          </div>

          <div>
            <p className="mb-1 text-center text-sm font-bold uppercase tracking-wide text-gray-500 dark:text-gray-400">
              Power of punch
            </p>
            <LevelSwitcher value={punchLevel} onChange={setPunchLevel} />
          </div>

          {error && <p className="text-sm text-[#dc2626] dark:text-red-400">{error}</p>}
          {lastResult && !error && (
            <p className="text-sm text-green-700 dark:text-green-400">
              Hit {lastResult.targets.length} zone(s) with level {lastResult.level}.
            </p>
          )}

          <button
            type="button"
            disabled={!canPunch || busy || targets.length === 0}
            onClick={handleUnleash}
            className="rounded-full bg-[#dc2626] px-6 py-2.5 text-lg font-bold text-white shadow-lg hover:bg-[#b91c1c] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Unleashing…" : "Unleash Kaiju"}
          </button>
        </div>
      </div>
    </div>
  );
}
