const BASE_URL = "http://localhost:9876";

// ── Definición de campos configurables (deducido de .env-example) ─────────────
const FIELD_DEFS = [
  {
    key:     "TARGET_BASE_PATH",
    label:   "Base path del BFF",
    type:    "select",
    options: ["pocket-bff", "web-bff"],
  },
  {
    key:     "COUPONS_LIST_SUFFIX",
    label:   "Cupones de lealtad",
    type:    "select",
    options: ["empty", "full"],
  },
  {
    key:     "COUPONS_REDEEMED_SUFFIX",
    label:   "Cupones canjeados",
    type:    "select",
    options: ["empty", "full"],
  },
  {
    key:     "CHECKOUT_COUPONS_SUFFIX",
    label:   "Cupones de checkout",
    type:    "select",
    options: ["cart", "no_cart_error"],
  },
  {
    key:   "LOYALTY_MEMBER_ID",
    label: "Loyalty Member ID",
    type:  "text",
  },
  {
    key:   "USER_ID",
    label: "User ID",
    type:  "number",
  },
];

// ── Labels ────────────────────────────────────────────────────────────────────
const STATUS_LABEL = {
  enrolled:    "Enrolado",
  notEnrolled: "No enrolado",
  unenrolled:  "Desenrolado",
  declined:    "Rechazado",
};
const ACTION_LABEL = {
  none:                "Ninguna",
  displayWelcomeModal: "Mostrar bienvenida",
  displayEnrollModal:  "Mostrar enrolamiento",
};
const GENDER_LABEL = { male: "Masculino", female: "Femenino", M: "Masculino", F: "Femenino" };

// ── Estado local ──────────────────────────────────────────────────────────────
let config = null;   // último config recibido del servidor
let panelOpen = false;

// ── Render helpers ────────────────────────────────────────────────────────────
function field(label, value, cls = "") {
  const display = value != null && value !== "" ? value : "—";
  return `
    <div class="field ${cls}">
      <div class="field-label">${label}</div>
      <div class="field-value ${display === "—" ? "empty" : ""}">${display}</div>
    </div>`;
}

function statusBadge(status) {
  const label = STATUS_LABEL[status] ?? status ?? "Desconocido";
  const raw   = status ? ` <span style="opacity:.75;font-weight:500">(${status})</span>` : "";
  return `<span class="status-badge ${status ?? ""}">${label}${raw}</span>`;
}

function actionBadge(action) {
  const label = ACTION_LABEL[action] ?? action ?? "—";
  const raw   = action && ACTION_LABEL[action] ? ` <span style="opacity:.75;font-weight:500">(${action})</span>` : "";
  return `<span class="action-badge">${label}${raw}</span>`;
}

// ── Header ────────────────────────────────────────────────────────────────────
function renderHeader(data) {
  const l = data?.loyaltyData ?? {};
  document.getElementById("header-summary").innerHTML = `
    ${statusBadge(l.status)}
    ${actionBadge(l.action)}
    <span class="header-field">Miembro desde: <span>${l.memberSince ?? "—"}</span></span>
    <span class="header-field">Usuario: <span>${[data?.firstName, data?.lastName].filter(Boolean).join(" ") || "—"}</span></span>
  `;
}

function renderHeaderError(msg) {
  document.getElementById("header-summary").innerHTML =
    `<span id="header-error">⚠️ ${msg}</span>`;
}

// ── Cards de estado / usuario ─────────────────────────────────────────────────
function renderLoyaltyCard(data) {
  const l = data?.loyaltyData ?? {};
  document.getElementById("loyalty-fields").innerHTML =
    field("Estado",        statusBadge(l.status) + "<div style='margin-top:4px;'>" + actionBadge(l.action) + "</div>", "col-2") +
    field("Acción",        ACTION_LABEL[l.action] ?? l.action) +
    field("Miembro desde", l.memberSince);
}

function renderUserCard(data) {
  document.getElementById("user-fields").innerHTML =
    field("Nombre",           data?.firstName) +
    field("Apellido paterno", data?.lastName) +
    field("Apellido materno", data?.maternalName) +
    field("Género",           GENDER_LABEL[data?.gender] ? `${GENDER_LABEL[data.gender]} (${data.gender})` : data?.gender) +
    field("Email",            data?.email) +
    field("Fecha nacimiento", data?.dateOfBirth) +
    field("ID Repositorio",   data?.repositoryId) +
    field("Núm. Monedero",    data?.monederoAccNumber);
}

// ── Dirty state ───────────────────────────────────────────────────────────────
function checkDirty() {
  if (!config) return;
  let dirtyCount = 0;
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    const formVal = def.type === "number" ? Number(el.value) : el.value;
    const isDirty = String(formVal) !== String(config[def.key] ?? "");
    el.classList.toggle("dirty", isDirty);
    if (isDirty) dirtyCount++;
  }
  const notice = document.getElementById("pending-notice");
  if (dirtyCount > 0) {
    const s = dirtyCount > 1 ? "s" : "";
    notice.textContent = `● ${dirtyCount} cambio${s} pendiente${s} de aplicar`;
    notice.classList.add("visible");
  } else {
    notice.textContent = "";
    notice.classList.remove("visible");
  }
}

function attachFormListeners() {
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    el.addEventListener("change", checkDirty);
    if (def.type !== "select") el.addEventListener("input", checkDirty);
  }
}

// ── Config panel ──────────────────────────────────────────────────────────────
function renderConfigPanel(cfg) {
  // Servidor (solo lectura)
  document.getElementById("panel-server").innerHTML = [
    ["Versión", cfg.version],
    ["Puerto",  cfg.PORT],
  ].map(([k, v]) => `
    <div class="info-row">
      <span class="info-key">${k}</span>
      <span class="info-val">${v ?? "—"}</span>
    </div>`).join("");

  // Formulario de variables editables
  const form = document.getElementById("panel-form");
  form.innerHTML = FIELD_DEFS.map(def => {
    const current = cfg[def.key] ?? "";
    if (def.type === "select") {
      const opts = def.options.map(o =>
        `<option value="${o}" ${o == current ? "selected" : ""}>${o}</option>`
      ).join("");
      return `
        <div class="form-field">
          <label class="form-label" for="cfg-${def.key}">${def.label}</label>
          <select class="form-control" id="cfg-${def.key}">${opts}</select>
        </div>`;
    }
    return `
      <div class="form-field">
        <label class="form-label" for="cfg-${def.key}">${def.label}</label>
        <input class="form-control" id="cfg-${def.key}" type="${def.type}" value="${current}" />
      </div>`;
  }).join("");

  attachFormListeners();
  checkDirty();

  // Paths activos (solo lectura)
  const paths = cfg.paths ?? {};
  document.getElementById("panel-paths").innerHTML = Object.entries(paths)
    .map(([k, v]) => `
      <div class="path-row">
        <span class="path-key">${k}</span>
        <span class="path-val">${v}</span>
      </div>`).join("");
}

// ── Toggle panel ──────────────────────────────────────────────────────────────
function togglePanel() {
  panelOpen = !panelOpen;
  document.getElementById("config-panel").classList.toggle("open", panelOpen);
  document.getElementById("panel-backdrop").classList.toggle("visible", panelOpen);
  document.getElementById("btn-config").classList.toggle("active", panelOpen);
}

// ── Aplicar configuración ─────────────────────────────────────────────────────
async function applyConfig() {
  const btn      = document.getElementById("btn-apply");
  const feedback = document.getElementById("apply-feedback");
  btn.disabled   = true;
  feedback.textContent = "";
  feedback.className   = "";

  const body = {};
  for (const def of FIELD_DEFS) {
    const el = document.getElementById(`cfg-${def.key}`);
    if (!el) continue;
    body[def.key] = def.type === "number" ? Number(el.value) : el.value;
  }

  try {
    const res  = await fetch(`${BASE_URL}/configuration`, {
      method:  "PUT",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    config = data.configuration;
    renderConfigPanel(config);
    await fetchStatus();
    feedback.textContent = "✓ Configuración aplicada";
    feedback.className   = "ok";
  } catch (err) {
    feedback.textContent = `⚠️ ${err.message}`;
    feedback.className   = "err";
  } finally {
    btn.disabled = false;
    setTimeout(() => { feedback.textContent = ""; feedback.className = ""; }, 3000);
  }
}

// ── Fetch status ──────────────────────────────────────────────────────────────
async function fetchStatus() {
  const btn = document.getElementById("btn-refresh");
  btn.classList.add("loading");
  btn.disabled = true;

  try {
    const statusPath = config?.paths?.status;
    if (!statusPath) throw new Error("Configuración no cargada");
    const res  = await fetch(`${BASE_URL}${statusPath}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    renderHeader(data);
    renderLoyaltyCard(data);
    renderUserCard(data);
  } catch (err) {
    renderHeaderError(`No se pudo conectar con el servidor (${err.message})`);
  } finally {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

function refreshStatus() { fetchStatus(); }

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const res = await fetch(`${BASE_URL}/configuration`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    config = await res.json();
    renderConfigPanel(config);
  } catch (err) {
    renderHeaderError(`No se pudo cargar la configuración (${err.message})`);
    return;
  }
  await fetchStatus();
}

init();
