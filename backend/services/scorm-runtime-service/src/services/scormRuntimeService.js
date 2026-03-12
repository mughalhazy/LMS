import { randomUUID } from "node:crypto";
import { defaultsForVersion } from "../runtime/cmiDefaults.js";
import { resolveLaunchUrl } from "../runtime/manifestParser.js";
import { normalizeRuntimeCall, applyRuntimeCall } from "../runtime/apiAdapter.js";

function progressFromCmi(version, cmi) {
  if (version === "1.2") {
    const status = cmi["cmi.core.lesson_status"] ?? "not attempted";
    if (["completed", "passed"].includes(status)) return 100;
    if (status === "incomplete") return 60;
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
    return ["passed", "failed", "completed", "incomplete"].includes(status) ? status : "incomplete";
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
    const sessionId = randomUUID();
    const token = randomUUID();
    const now = new Date().toISOString();

    const session = {
      sessionId,
      sessionToken: token,
      tenantId: payload.tenantId,
      learnerId: payload.learnerId,
      courseId: payload.courseId,
      registrationId: payload.registrationId,
      contentId: payload.contentId,
      launchMode: payload.launchMode,
      version,
      launchUrl: launchMeta.href,
      resourceIdentifier: launchMeta.resourceIdentifier,
      scormType: launchMeta.scormType,
      cmi: defaultsForVersion(version),
      lifecycleState: "launched",
      pendingCommit: false,
      progressPercentage: 0,
      attemptStatus: "incomplete",
      startedAt: now,
      updatedAt: now,
      endedAt: null,
      lastCommitAt: null,
      lastError: "0"
    };

    await this.store.save(session);
    return {
      sessionId,
      sessionToken: token,
      launchUrl: launchMeta.href,
      launchMode: payload.launchMode,
      scoIdentifier: payload.scoIdentifier,
      cmi: session.cmi,
      runtimeVersion: version
    };
  }

  async getSession(tenantId, sessionId) {
    const session = await this.store.getById(sessionId);
    if (!session || session.tenantId !== tenantId) {
      throw new Error("SCORM session not found for tenant");
    }
    return session;
  }

  async runtimeCall(tenantId, sessionId, token, rawCall) {
    const session = await this.getSession(tenantId, sessionId);
    if (session.sessionToken !== token) {
      throw new Error("Invalid SCORM session token");
    }

    const call = normalizeRuntimeCall(rawCall);
    const result = applyRuntimeCall(session, call);
    session.progressPercentage = progressFromCmi(session.version, session.cmi);
    session.attemptStatus = finalOutcome(session.version, session.cmi);
    session.updatedAt = new Date().toISOString();
    await this.store.save(session);

    return {
      method: call.method,
      result,
      progressPercentage: session.progressPercentage,
      attemptStatus: session.attemptStatus,
      lastError: session.lastError
    };
  }

  async commit(tenantId, sessionId, token) {
    return this.runtimeCall(tenantId, sessionId, token, { method: "Commit" });
  }

  async finish(tenantId, sessionId, token) {
    const outcome = await this.runtimeCall(tenantId, sessionId, token, { method: "Terminate" });
    const session = await this.getSession(tenantId, sessionId);
    return {
      ...outcome,
      completion: {
        learnerId: session.learnerId,
        courseId: session.courseId,
        registrationId: session.registrationId,
        finalStatus: session.attemptStatus,
        score: session.version === "1.2" ? session.cmi["cmi.core.score.raw"] : session.cmi["cmi.score.raw"],
        completedAt: session.endedAt,
        totalTime: session.version === "1.2" ? session.cmi["cmi.core.total_time"] : session.cmi["cmi.total_time"]
      }
    };
  }
}
