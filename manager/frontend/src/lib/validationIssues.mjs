const AGENT_FIELD_MAP = {
  "matrix.external_peers": "external_peers",
  "model.model": "llm_profile",
  "model.api_key": "llm_profile",
  "matrix.homeserver": "matrix_profile",
  "matrix.user_id": "matrix_profile",
  matrix: "matrix_profile",
  "mcp.url": "mcp_profile",
  workspace: "",
  "proactive.quiet_hours": "proactive_quiet_hours",
  "proactive.random_min_minutes": "proactive_random_min_minutes",
  "proactive.random_max_minutes": "proactive_random_max_minutes",
  "proactive.poll_seconds": "proactive_poll_seconds",
  "proactive.agent_url": "proactive_agent_url",
  "proactive.target": "proactive_target"
};

const COLLECTION_ROUTES = {
  agents: "agents",
  skill_bundles: "skills",
  prompt_templates: "prompts"
};

export function normalizeIssue(issue, level = "error") {
  return {
    level,
    code: String(issue?.code || ""),
    field: String(issue?.field || ""),
    message: String(issue?.message || issue?.code || "Validation issue."),
    details: issue?.details || {}
  };
}

export function validationIssuesFromResult(result) {
  return [
    ...(result?.errors || []).map((issue) => normalizeIssue(issue, "error")),
    ...(result?.warnings || []).map((issue) => normalizeIssue(issue, "warning"))
  ];
}

export function validationIssuesFromError(error) {
  return validationIssuesFromResult(error?.details || {});
}

export function mapIssuesToAgentForm(issues, agentId) {
  const prefix = `agents.${agentId}.`;
  const errors = {};
  const global = [];
  for (const issue of issues) {
    if (issue.level === "warning") {
      global.push(issue);
      continue;
    }
    const field = issue.field || "";
    if (field === "agents" || field === "host_port") {
      global.push(issue);
      continue;
    }
    if (!field.startsWith(prefix)) continue;
    const localPath = stripListIndex(field.slice(prefix.length));
    const formKey = AGENT_FIELD_MAP[localPath] || AGENT_FIELD_MAP[localPath.replace(/\[\d+\]$/, "")] || localPath.replaceAll(".", "_").replace(/\[\d+\]/g, "");
    if (formKey) {
      errors[formKey] = mergeMessage(errors[formKey], issue.message);
    } else {
      global.push(issue);
    }
  }
  return { errors, global };
}

export function mapIssuesToProfileForm(issues, kind, selectedId, profiles) {
  const profileRows = profiles?.[kind] || [];
  const errors = {};
  const global = [];
  for (const issue of issues) {
    if (issue.level === "warning") {
      global.push(issue);
      continue;
    }
    const match = issue.field.match(/^profiles\.([A-Za-z_]+)\[(\d+)\](?:\.(.+))?$/);
    if (!match || match[1] !== kind) continue;
    const index = Number(match[2]);
    const profile = profileRows[index];
    if (itemId(profile) !== selectedId) continue;
    const localPath = stripListIndex(match[3] || "id");
    if (localPath) {
      errors[localPath.replaceAll(".", "_")] = mergeMessage(errors[localPath.replaceAll(".", "_")], issue.message);
    } else {
      global.push(issue);
    }
  }
  return { errors, global };
}

export function issueTarget(issue, config) {
  const field = String(issue?.field || "");
  const agent = field.match(/^agents\.([^.[]+)/);
  if (agent) return { label: agent[1], to: `/agents?agent=${encodeURIComponent(agent[1])}` };

  const profile = field.match(/^profiles\.([A-Za-z_]+)\[(\d+)\]/);
  if (profile) {
    const kind = profile[1];
    const row = config?.profiles?.[kind]?.[Number(profile[2])];
    const id = itemId(row);
    return { label: id || kind, to: `/profiles/${kind}${id ? `?id=${encodeURIComponent(id)}` : ""}` };
  }

  const collection = field.match(/^([A-Za-z_]+)\[(\d+)\]/);
  if (collection && COLLECTION_ROUTES[collection[1]]) {
    return { label: collection[1], to: `/${COLLECTION_ROUTES[collection[1]]}` };
  }

  return null;
}

export function issueSummary(issues) {
  const errors = issues.filter((issue) => issue.level === "error").length;
  const warnings = issues.filter((issue) => issue.level === "warning").length;
  return { errors, warnings, valid: errors === 0 };
}

export function issueMessages(issues) {
  return issues.map((issue) => issue.message).filter(Boolean);
}

function stripListIndex(value) {
  return String(value || "").replace(/\[(\d+)\]/g, "");
}

function mergeMessage(current, next) {
  if (!current) return next;
  if (!next || current.includes(next)) return current;
  return `${current} ${next}`;
}

function itemId(item) {
  return item?.id || item?.alias || item?.server_name || "";
}
