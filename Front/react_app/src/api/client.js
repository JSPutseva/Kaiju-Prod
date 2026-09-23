const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const token = localStorage.getItem("kaiju_token");

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let detail = res.statusText;

    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // body wasn't JSON
    }

    if (Array.isArray(detail)) {
      // FastAPI validation errors: [{ loc: [...], msg: "..." }, ...]
      detail = detail
        .map((e) => e.msg || JSON.stringify(e))
        .join(" ");
    }

    let code = null;
    let message = detail;
    if (detail && typeof detail === "object") {
      // business-rule rejections: { code, message }
      code = detail.code ?? null;
      message = detail.message ?? res.statusText;
    }

    const err = new Error(typeof message === "string" ? message : res.statusText);
    err.code = code;
    throw err;
  }

  if (res.status === 204) {
    return null;
  }

  return res.json();
}

export const api = {
  login: (payload) =>
    request("/auth/login", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  register: (payload) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getCurrentUser: () => request("/auth/me"),

  listUsers: () => request("/users"),

  assignRole: (userId, payload) =>
    request(`/users/${userId}/role`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  deleteUser: (userId) => request(`/users/${userId}`, { method: "DELETE" }),

  getQuarters: () => request("/quarters"),

  getQuarterResources: (quarterId) =>
    request(`/quarters/${quarterId}/resources`),

  routeTransfer: (payload) =>
    request("/transfers/route", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  createRequest: (payload) =>
    request("/requests", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  createReservation: (payload) =>
    request("/reservations", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
