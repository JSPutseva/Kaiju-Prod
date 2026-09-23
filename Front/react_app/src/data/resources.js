import { COLORS } from "./colors";

const RETENTION_RATIO = 0.3;

function retentionMin(initialQuantity) {
  return Math.ceil(initialQuantity * RETENTION_RATIO);
}

export const STATUS = {
  normal: { label: "Normal", text: COLORS.greenText, dot: COLORS.green, bold: false },
  belowNormal: { label: "Smaller than normal", text: COLORS.amberText, dot: COLORS.amber, bold: true },
  insufficient: { label: "Insuffisant", text: COLORS.redText, dot: COLORS.red, bold: true },
};

// 3-tier status vs. the retention floor
export function resourceStatus({ quantity, initialQuantity }) {
  const min = retentionMin(initialQuantity);
  if (quantity <= min) return "insufficient";
  if (quantity <= min * 1.5) return "belowNormal";
  return "normal";
}
