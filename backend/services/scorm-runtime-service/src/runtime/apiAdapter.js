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

  return {
    method,
    key: payload.key,
    value: payload.value,
    requestId: payload.requestId
  };
}

export function applyRuntimeCall(session, call) {
  switch (call.method) {
    case "Initialize":
      session.lifecycleState = "initialized";
      session.lastError = "0";
      return { ok: true, value: "true" };

    case "GetValue": {
      const value = session.cmi[call.key] ?? "";
      session.lastError = "0";
      return { ok: true, value };
    }

    case "SetValue": {
      if (!call.key) {
        session.lastError = "201";
        return { ok: false, value: "false", error: "CMI key is required" };
      }

      if (call.key === "cmi.suspend_data" && String(call.value ?? "").length > 4096) {
        session.lastError = "405";
        return { ok: false, value: "false", error: "suspend_data exceeds 4KB limit" };
      }

      session.cmi[call.key] = String(call.value ?? "");
      session.lastError = "0";
      session.pendingCommit = true;
      return { ok: true, value: "true" };
    }

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
      session.lastError = "101";
      return { ok: false, value: "false", error: `Unsupported method ${call.method}` };
  }
}
