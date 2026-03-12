import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { promises as fs } from 'node:fs';
import { FileSessionStore } from '../src/persistence/fileSessionStore.js';
import { ScormRuntimeService } from '../src/services/scormRuntimeService.js';

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
  const file = path.join(process.cwd(), 'test', `.tmp-${Date.now()}-${Math.random()}.json`);
  const store = new FileSessionStore(file);
  await store.init();
  const service = new ScormRuntimeService(store);
  return { service, file };
}

test('launch creates tenant-scoped session with defaults', async () => {
  const { service, file } = await setup();

  const launched = await service.launch({
    tenantId: 'tenant-a',
    learnerId: 'u1',
    courseId: 'c1',
    registrationId: 'r1',
    contentId: 'ct1',
    version: '1.2',
    launchMode: 'normal',
    scoIdentifier: 'SCO_1',
    manifestXml: manifest
  });

  assert.equal(launched.runtimeVersion, '1.2');
  assert.equal(launched.launchUrl, 'index.html');

  const session = await service.getSession('tenant-a', launched.sessionId);
  assert.equal(session.tenantId, 'tenant-a');
  assert.equal(session.cmi['cmi.core.lesson_status'], 'not attempted');

  await fs.unlink(file);
});

test('runtime SetValue and Commit persist updates', async () => {
  const { service, file } = await setup();
  const launched = await service.launch({
    tenantId: 'tenant-a', learnerId: 'u1', courseId: 'c1', registrationId: 'r1', contentId: 'ct1',
    version: '2004', launchMode: 'normal', scoIdentifier: 'SCO_1', manifestXml: manifest
  });

  await service.runtimeCall('tenant-a', launched.sessionId, launched.sessionToken, {
    method: 'SetValue',
    key: 'cmi.completion_status',
    value: 'completed'
  });

  const commitResult = await service.commit('tenant-a', launched.sessionId, launched.sessionToken);
  assert.equal(commitResult.result.value, 'true');

  const session = await service.getSession('tenant-a', launched.sessionId);
  assert.equal(session.cmi['cmi.completion_status'], 'completed');
  assert.equal(session.progressPercentage, 100);

  await fs.unlink(file);
});

test('tenant isolation blocks cross-tenant access', async () => {
  const { service, file } = await setup();
  const launched = await service.launch({
    tenantId: 'tenant-a', learnerId: 'u1', courseId: 'c1', registrationId: 'r1', contentId: 'ct1',
    version: '2004', launchMode: 'normal', scoIdentifier: 'SCO_1', manifestXml: manifest
  });

  await assert.rejects(
    service.getSession('tenant-b', launched.sessionId),
    /not found for tenant/
  );

  await fs.unlink(file);
});
