// hex matches tailwind.config.js's district.* colors (used for dots/backgrounds);
// textHex is a darkened variant for use as text color on light backgrounds,
// where the raw (bright/pastel) hex reads poorly
export const DISTRICTS = [
  { id: "A", name: "Apex", color: "district-a", hex: "#E63946", textHex: "#D40413", sea: false, adjacent: ["E", "W", "X"] },
  { id: "E", name: "Echo", color: "district-e", hex: "#4CAF3C", textHex: "#14A100", sea: true, adjacent: ["A", "X"] },
  { id: "W", name: "Warden", color: "district-w", hex: "#FFA055", textHex: "#FFA055", sea: false, adjacent: ["A", "X", "Z"] },
  { id: "X", name: "Xeno", color: "district-x", hex: "#F4E03A", textHex: "#B9A000", sea: true, adjacent: ["A", "E", "W", "Z"] },
  { id: "Z", name: "Zion", color: "district-z", hex: "#6EC6E8", textHex: "#3AA9D4", sea: true, adjacent: ["W", "X"] },
];

export const getDistrict = (id) => DISTRICTS.find((d) => d.id === id);

// text-safe color for a district name: darkened on light backgrounds, the
// original (already light/bright) hex on dark backgrounds
export const getDistrictTextColor = (id, theme) => {
  const d = getDistrict(id);
  if (!d) return undefined;
  return theme === "dark" ? d.hex : d.textHex;
};

export const isAdjacent = (originId, targetId) =>
  getDistrict(originId)?.adjacent.includes(targetId) ?? false;

export const canGoBySea = (originId, targetId) =>
  Boolean(getDistrict(originId)?.sea && getDistrict(targetId)?.sea);

// valid transit quarters: adjacent to both origin and target
export const transitOptions = (originId, targetId) => {
  const origin = getDistrict(originId);
  const target = getDistrict(targetId);
  if (!origin || !target) return [];
  return origin.adjacent.filter(
    (id) => id !== targetId && target.adjacent.includes(id)
  );
};
