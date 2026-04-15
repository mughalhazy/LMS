const METHOD_ALIAS = {
  LMSInitialize: "Initialize",
  LMSFinish: "Terminate",
  LMSGetValue: "GetValue",
  LMSSetValue: "SetValue",
  LMSCommit: "Commit"
};

const SUPPORTED_METHODS = new Set(["Initialize", "Terminate", "GetValue", "SetValue", "Commit"]);

export function normalizeRuntimeCall(payload) {
  const method = METHOD_ALIAS[payload.method] ?? payload.method;
  if (!SUPPORTED_METHODS.has(method)) {
    throw new Error(`Unsupported SCORM runtime method '${payload.method}'`);
  }
  return { method, key: payload.key, value: payload.value };
}

export function applyRuntimeCall(session, call) {
  switch (call.method) {
    case "Initialize":
      session.lifecycleState = "initialized";
      session.lastError = "0";
      return { ok: true, value: "true" };
    case "GetValue":
      session.lastError = "0";
      return { ok: true, value: session.cmi[call.key] ?? "" };
    case "SetValue":
      if (!call.key) {
        session.lastError = "201";
        return { ok: false, value: "false", error: "CMI key is required" };
      }
      session.cmi[call.key] = String(call.value ?? "");
      session.pendingCommit = true;
      session.lastError = "0";
      return { ok: true, value: "true" };
    case "Commit":
      session.pendingCommit = false;
      session.lastCommitAt = new Date().toISOString();
      session.lastError = "0";
      return { ok: true, value: "true" };
    case "Terminate":
      session.lifecycleState = "terminated";
      session.endedAt = new Date().toISOString();
      session.lastError = "0";
      return { ok: true, value: "true" };
    default:
      return { ok: false, value: "false" };
  }
}
