export const DISTRICTS = [
  { id: "A", name: "Apex", color: "district-a", sea: false, adjacent: ["E", "W", "X"] },
  { id: "E", name: "Echo", color: "district-e", sea: true, adjacent: ["A", "X"] },
  { id: "W", name: "Warden", color: "district-w", sea: false, adjacent: ["A", "X", "Z"] },
  { id: "X", name: "Xeno", color: "district-x", sea: true, adjacent: ["A", "E", "W", "Z"] },
  { id: "Z", name: "Zion", color: "district-z", sea: true, adjacent: ["W", "X"] },
];

export const getDistrict = (id) => DISTRICTS.find((d) => d.id === id);

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
