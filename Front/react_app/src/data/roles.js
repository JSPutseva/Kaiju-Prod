export const ROLES = {
  QC: { label: "Quarter Coordinator", avatar: "/ava-qc.svg" },
  LC: { label: "Logistics Coordinator", avatar: "/ava-lc.svg" },
  CD: { label: "City Director", avatar: "/ava-cd.svg" },
};

export const getRole = (code) => ROLES[code];
