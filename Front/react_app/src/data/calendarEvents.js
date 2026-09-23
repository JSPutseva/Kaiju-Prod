import { COLORS } from "./colors";

// mock timeline, will come from the backend later
export const EVENT_TYPES = {
  transfer: { label: "Transfer", text: COLORS.primary, dot: COLORS.primary },
  reservation: { label: "Reservation", text: COLORS.grayText, dot: COLORS.gray },
  requisition: { label: "Requisition", text: COLORS.greenText, dot: COLORS.green },
  levelChange: { label: "Level change", text: COLORS.red, dot: COLORS.red },
};

// Labels reference the real resource_types from the rules doc / database seed.
export const CALENDAR_EVENTS = [
  { id: 1, date: "2026-09-10", type: "levelChange", label: "Watch → Alert" },
  { id: 2, date: "2026-09-11", type: "reservation", label: "Apex: Medical personnel" },
  { id: 3, date: "2026-09-12", type: "transfer", label: "Apex → Echo: Food & water supplies" },
  { id: 4, date: "2026-09-12", type: "transfer", label: "Warden → Xeno: Power generators" },
  { id: 5, date: "2026-09-13", type: "levelChange", label: "Alert → Emergency" },
  { id: 6, date: "2026-09-13", type: "reservation", label: "Zion: Rescue teams" },
  { id: 7, date: "2026-09-14", type: "transfer", label: "Echo → Xeno: Hazmat equipment" },
  { id: 8, date: "2026-09-15", type: "requisition", label: "CD: Power generators (city-wide)" },
  { id: 9, date: "2026-09-15", type: "transfer", label: "Xeno → Zion: Transport vehicles" },
  { id: 10, date: "2026-09-16", type: "levelChange", label: "Emergency → Critical" },
];
