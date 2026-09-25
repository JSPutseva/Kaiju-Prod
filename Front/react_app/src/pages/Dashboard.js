import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { LEVELS } from "../context/DisasterLevelContext";
import { useCurrentUser } from "../context/CurrentUserContext";
import { useQuarters } from "../context/QuartersContext";
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
  const navigate = useNavigate();
  const { roleCode } = useCurrentUser();
  const { byCode: quarterByCode, status: quartersStatus } = useQuarters();
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

  const levelsByCode = Object.fromEntries(
    Object.entries(quarterByCode).map(([code, q]) => [code, q.disaster_level])
  );
  // city status badge shows the worst-hit zone's level, since each zone now
  // has its own real level (see the Kaiju POV page)
  const worstLevel =
    quartersStatus === "ready"
      ? Math.max(1, ...Object.values(levelsByCode))
      : 1;
  const worstLevelName = LEVELS.find((l) => l.level === worstLevel)?.name ?? "Watch";

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <main className="grid grid-cols-1 gap-6 px-6 pb-6 md:grid-cols-[360px_1fr_320px]">
        <NotificationsPanel />

        <section className="relative text-center">
          <span
            className={`absolute left-1/2 top-0 z-10 -translate-x-1/2 -translate-y-1/2 whitespace-nowrap rounded-full border-2 border-white px-4 py-1.5 text-sm font-bold text-white shadow bg-level-${worstLevelName.toLowerCase()}`}
          >
            current level: {worstLevelName}
          </span>
          <CityMap
            selected={menu?.districtId ?? activeFlow?.districtId ?? null}
            onSelect={openMenuFor}
            levels={levelsByCode}
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

      {roleCode === "CD" && (
        <button
          type="button"
          onClick={() => navigate("/kaiju-pov")}
          className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-full bg-[#F47E00] dark:bg-[#F8A201] px-4 py-2 text-sm font-bold text-white shadow-lg hover:bg-[#D98C00]"
        >
          Kaiju POV
        </button>
      )}
    </div>
  );
}
