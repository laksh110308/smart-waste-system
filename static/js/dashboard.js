/* ============================================================
   Smart Waste Collection System - Shared Dashboard JS
   API helper functions used across all pages.
   ============================================================ */

const API = {
  get: (url) => fetch(url).then(r => r.json()),
  post: (url, body) => fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined
  }).then(async (r) => {
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Request failed");
    return data;
  })
};

function showToast(message, isError = false) {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = "toast show" + (isError ? " error" : "");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => toast.classList.remove("show"), 3200);
}

function fillColor(fillLevel, threshold) {
  if (fillLevel >= threshold) return "var(--color-danger)";
  if (fillLevel >= threshold * 0.7) return "var(--color-warning)";
  return "var(--color-secondary)";
}

function statusBadge(status) {
  const cls = status === "Collection Required" ? "badge-required" : "badge-normal";
  return `<span class="badge ${cls}">${status}</span>`;
}

function collectionStatusBadge(status) {
  const map = { "Pending": "badge-normal", "Assigned": "badge-assigned", "Collected": "badge-collected" };
  return `<span class="badge ${map[status] || "badge-normal"}">${status}</span>`;
}

function routeStatusBadge(status) {
  const map = { "Planned": "badge-planned", "In Progress": "badge-inprogress", "Completed": "badge-completed" };
  return `<span class="badge ${map[status] || "badge-normal"}">${status}</span>`;
}

// Highlights the current page's nav link
document.addEventListener("DOMContentLoaded", () => {
  const path = window.location.pathname;
  document.querySelectorAll(".navbar-links a").forEach(link => {
    if (link.getAttribute("href") === path) link.classList.add("active");
  });
});
