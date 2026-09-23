import { useState } from "react";
import { useDisasterLevel } from "../context/DisasterLevelContext";
import Header from "../components/Header";
import NotificationsPanel from "../components/NotificationsPanel";
import Navigation from "../components/Navigation";
import CityMap from "../components/CityMap";
import ZoneModal from "../components/ZoneModal";
import ZoneActionMenu from "../components/ZoneActionMenu";
import TransferFlowModal from "../components/TransferFlowModal";
import ReserveModal from "../components/ReserveModal";
import ManageRolesModal from "../components/ManageRolesModal";

export default function Dashboard() {
  const { level, levelName, setLevel } = useDisasterLevel();
  const [menu, setMenu] = useState(null); // { districtId, anchor: { x, top, bottom } }
  const [activeFlow, setActiveFlow] = useState(null); // { type, districtId }
  const [manageRolesOpen, setManageRolesOpen] = useState(false);

  const openMenuFor = (districtId, event) => {
    const rect = event.currentTarget.getBoundingClientRect();
    setMenu({
      districtId,
      anchor: { x: rect.left + rect.width / 2, top: rect.top, bottom: rect.bottom },
    });
  };

  const handleSelectAction = (actionId) => {
    setActiveFlow({ type: actionId, districtId: menu.districtId });
    setMenu(null);
  };

  const viewZone = (districtId) => setActiveFlow({ type: "view", districtId });

  const closeFlow = () => setActiveFlow(null);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <main className="grid grid-cols-1 gap-6 px-6 pb-6 md:grid-cols-[360px_1fr_320px]">
        <NotificationsPanel />

        <section className="relative text-center">
          <span
            className={`absolute left-1/2 top-0 z-10 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap rounded-full border-2 border-white px-4 py-1.5 text-sm font-bold text-white shadow bg-level-${levelName.toLowerCase()}`}
          >
            current level: {levelName}
          </span>
          <CityMap
            selected={menu?.districtId ?? activeFlow?.districtId ?? null}
            onSelect={openMenuFor}
          />
        </section>

        <Navigation onSelectZone={viewZone} onManageRoles={() => setManageRolesOpen(true)} />
      </main>

      {menu && (
        <ZoneActionMenu
          districtId={menu.districtId}
          anchor={menu.anchor}
          onSelectAction={handleSelectAction}
          onClose={() => setMenu(null)}
        />
      )}

      {activeFlow?.type === "view" && (
        <ZoneModal districtId={activeFlow.districtId} onClose={closeFlow} />
      )}
      {activeFlow?.type === "reserve" && (
        <ReserveModal districtId={activeFlow.districtId} onClose={closeFlow} />
      )}
      {(activeFlow?.type === "send" || activeFlow?.type === "get") && (
        <TransferFlowModal
          originId={activeFlow.districtId}
          direction={activeFlow.type === "get" ? "from" : "to"}
          onClose={closeFlow}
        />
      )}
      {activeFlow?.type === "maritime" && (
        <TransferFlowModal
          originId={activeFlow.districtId}
          direction="to"
          seaOnly
          onClose={closeFlow}
        />
      )}
      {manageRolesOpen && (
        <ManageRolesModal onClose={() => setManageRolesOpen(false)} />
      )}

      {/* Prototype-only control: real level state will come from the
          teammate's disaster-level system. */}
      <div className="fixed bottom-3 right-3 flex items-center gap-3 rounded-md bg-white/90 px-2 py-1 text-sm text-gray-500 shadow dark:bg-gray-800/90 dark:text-gray-400">
        <label className="flex items-center gap-1">
          dev level
          <select
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
            className="rounded border border-gray-300 bg-white text-sm dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
          >
            {[1, 2, 3, 4, 5].map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
