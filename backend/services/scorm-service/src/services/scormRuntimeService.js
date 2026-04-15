import { randomUUID } from "node:crypto";
import { defaultsForVersion } from "../runtime/cmiDefaults.js";
import { resolveLaunchUrl } from "../runtime/manifestParser.js";
import { normalizeRuntimeCall, applyRuntimeCall } from "../runtime/apiAdapter.js";

function parseRawScore(value) {
  if (value === "" || value == null) return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function progressFromCmi(version, cmi) {
  if (version === "1.2") {
    const status = cmi["cmi.core.lesson_status"] ?? "not attempted";
    if (["completed", "passed"].includes(status)) return 100;
    if (["incomplete", "failed"].includes(status)) return 60;
    return 0;
  }

  const completion = cmi["cmi.completion_status"] ?? "unknown";
  if (completion === "completed") return 100;
  if (completion === "incomplete") return 60;
  return 0;
}

function finalOutcome(version, cmi) {
  if (version === "1.2") {
    const status = cmi["cmi.core.lesson_status"] ?? "incomplete";
    return ["completed", "passed", "failed", "incomplete"].includes(status)
      ? status
      : "incomplete";
  }

  const completion = cmi["cmi.completion_status"] ?? "incomplete";
  const success = cmi["cmi.success_status"] ?? "unknown";
  if (completion !== "completed") return "incomplete";
  if (success === "passed") return "passed";
  if (success === "failed") return "failed";
  return "completed";
}

export class ScormRuntimeService {
  constructor(store) {
    this.store = store;
  }

  async launch(payload) {
    const launchMeta = resolveLaunchUrl(payload.manifestXml, payload.scoIdentifier);
    const version = payload.version === "1.2" ? "1.2" : "2004";
    const now = new Date().toISOString();
    const session = {
      sessionId: randomUUID(),
      sessionToken: randomUUID(),
      tenantId: payload.tenantId,
      learnerId: payload.learnerId,
      courseId: payload.courseId,
      registrationId: payload.registrationId,
      launchMode: payload.launchMode,
      version,
      launchUrl: launchMeta.href,
      resourceIdentifier: launchMeta.resourceIdentifier,
      cmi: defaultsForVersion(version),
      lifecycleState: "launched",
      progressPercentage: 0,
      attemptStatus: "incomplete",
      pendingCommit: false,
      startedAt: now,
      updatedAt: now,
      endedAt: null,
      lastCommitAt: null,
      lastError: "0"
    };

    await this.store.saveSession(session);
    return {
      sessionId: session.sessionId,
      sessionToken: session.sessionToken,
      launchUrl: session.launchUrl,
      cmi: session.cmi,
      runtimeVersion: version
    };
  }

  async getSession(tenantId, sessionId) {
    const session = await this.store.getById(sessionId);
    if (!session || session.tenantId !== tenantId) throw new Error("SCORM session not found for tenant");
    return session;
  }

  async runtimeCall(tenantId, sessionId, token, rawCall) {
    const session = await this.getSession(tenantId, sessionId);
    if (session.sessionToken !== token) throw new Error("Invalid SCORM session token");

    const call = normalizeRuntimeCall(rawCall);
    const result = applyRuntimeCall(session, call);
    session.progressPercentage = progressFromCmi(session.version, session.cmi);
    session.attemptStatus = finalOutcome(session.version, session.cmi);
    session.updatedAt = new Date().toISOString();
    await this.store.saveSession(session);

    return { method: call.method, result, progressPercentage: session.progressPercentage, attemptStatus: session.attemptStatus };
  }

  async commit(tenantId, sessionId, token) {
    return this.runtimeCall(tenantId, sessionId, token, { method: "Commit" });
  }

  async finish(tenantId, sessionId, token) {
    await this.runtimeCall(tenantId, sessionId, token, { method: "Terminate" });
    const session = await this.getSession(tenantId, sessionId);
    const score = parseRawScore(session.version === "1.2" ? session.cmi["cmi.core.score.raw"] : session.cmi["cmi.score.raw"]);
    const totalTime = session.version === "1.2" ? session.cmi["cmi.core.total_time"] : session.cmi["cmi.total_time"];
    const completion = {
      completionId: randomUUID(),
      tenantId,
      learnerId: session.learnerId,
      courseId: session.courseId,
      registrationId: session.registrationId,
      sessionId,
      status: session.attemptStatus,
      score,
      totalTime,
      completedAt: session.endedAt
    };
    await this.store.recordCompletion(completion);
    return completion;
  }

  async listCompletions(tenantId, registrationId) {
    return this.store.listCompletions(tenantId, registrationId);
  }
}
