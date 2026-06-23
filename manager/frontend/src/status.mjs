const STATUS_LABEL_KEYS = {
  ok: "status.ok",
  stage: "status.stage",
  dockerApiUrl: "status.dockerApiUrl",
  managerConfigPath: "status.managerConfigPath",
  managerSecretsPath: "status.managerSecretsPath",
  generatedConfigDir: "status.generatedConfigDir"
};

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export async function loadStatus({ document, t }) {
  const status = document.querySelector("#status");

  try {
    const response = await fetch("/api/status");
    const data = await response.json();
    status.innerHTML = Object.entries(data)
      .map(([key, value]) => {
        const label = t(STATUS_LABEL_KEYS[key] || key);
        return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(String(value))}</dd></div>`;
      })
      .join("");
  } catch (_error) {
    status.innerHTML = `<div><dt>${escapeHtml(t("status.status"))}</dt><dd>${escapeHtml(
      t("status.unavailable")
    )}</dd></div>`;
  }
}
