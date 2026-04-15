import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import { promises as fs } from "node:fs";
import { FileSessionStore } from "../src/persistence/fileSessionStore.js";
import { ScormRuntimeService } from "../src/services/scormRuntimeService.js";

const manifest = `
<manifest>
  <organizations>
    <organization identifier="ORG1">
      <item identifier="SCO_1" identifierref="RES_1"><title>Intro</title></item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="RES_1" adlcp:scormType="sco" href="index.html" />
  </resources>
</manifest>`;

async function setup() {
  const file = path.join(process.cwd(), "test", `.tmp-${Date.now()}-${Math.random()}.json`);
  const store = new FileSessionStore(file);
  await store.init();
  return { file, service: new ScormRuntimeService(store) };
}

test("launch resolves SCO and creates session", async () => {
  const { file, service } = await setup();
  const launched = await service.launch({
    tenantId: "t1",
    learnerId: "u1",
    courseId: "c1",
    registrationId: "r1",
    launchMode: "normal",
    version: "2004",
    manifestXml: manifest,
    scoIdentifier: "SCO_1"
  });

  assert.equal(launched.launchUrl, "index.html");
  const session = await service.getSession("t1", launched.sessionId);
  assert.equal(session.cmi["cmi.completion_status"], "unknown");

  await fs.unlink(file);
});

test("runtime updates completion state and finish records completion tracking", async () => {
  const { file, service } = await setup();
  const launched = await service.launch({
    tenantId: "t1",
    learnerId: "u1",
    courseId: "c1",
    registrationId: "r1",
    launchMode: "normal",
    version: "2004",
    manifestXml: manifest,
    scoIdentifier: "SCO_1"
  });

  await service.runtimeCall("t1", launched.sessionId, launched.sessionToken, {
    method: "SetValue",
    key: "cmi.completion_status",
    value: "completed"
  });
  await service.runtimeCall("t1", launched.sessionId, launched.sessionToken, {
    method: "SetValue",
    key: "cmi.success_status",
    value: "passed"
  });
  await service.runtimeCall("t1", launched.sessionId, launched.sessionToken, {
    method: "SetValue",
    key: "cmi.score.raw",
    value: "91"
  });

  const completion = await service.finish("t1", launched.sessionId, launched.sessionToken);
  assert.equal(completion.status, "passed");
  assert.equal(completion.score, 91);

  const completions = await service.listCompletions("t1", "r1");
  assert.equal(completions.length, 1);

  await fs.unlink(file);
});
