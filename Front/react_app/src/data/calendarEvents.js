import { COLORS } from "./colors";

// event type metadata for the operational calendar's legend/colors — the
// events themselves come from the backend (requests, reservations, and
// live disaster-level alerts over the WebSocket)
export const EVENT_TYPES = {
  transfer: { label: "Transfer", text: COLORS.primary, dot: COLORS.primary },
  reservation: { label: "Reservation", text: COLORS.grayText, dot: COLORS.gray },
  requisition: { label: "Requisition", text: COLORS.greenText, dot: COLORS.green },
  levelChange: { label: "Level change", text: COLORS.red, dot: COLORS.red },
};
