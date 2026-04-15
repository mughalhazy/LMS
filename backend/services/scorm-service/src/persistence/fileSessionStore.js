import { promises as fs } from "node:fs";
import path from "node:path";

export class FileSessionStore {
  constructor(filePath) {
    this.filePath = filePath;
    this.writeQueue = Promise.resolve();
  }

  async init() {
    await fs.mkdir(path.dirname(this.filePath), { recursive: true });
    try {
      await fs.access(this.filePath);
    } catch {
      await fs.writeFile(this.filePath, JSON.stringify({ sessions: [], completions: [] }, null, 2));
    }
  }

  async read() {
    return JSON.parse(await fs.readFile(this.filePath, "utf8"));
  }

  async getById(sessionId) {
    const data = await this.read();
    return data.sessions.find((s) => s.sessionId === sessionId) ?? null;
  }

  async saveSession(session) {
    this.writeQueue = this.writeQueue.then(async () => {
      const data = await this.read();
      const index = data.sessions.findIndex((s) => s.sessionId === session.sessionId);
      if (index >= 0) data.sessions[index] = session;
      else data.sessions.push(session);
      await fs.writeFile(this.filePath, JSON.stringify(data, null, 2));
    });
    await this.writeQueue;
    return session;
  }

  async recordCompletion(completion) {
    this.writeQueue = this.writeQueue.then(async () => {
      const data = await this.read();
      data.completions.push(completion);
      await fs.writeFile(this.filePath, JSON.stringify(data, null, 2));
    });
    await this.writeQueue;
    return completion;
  }

  async listCompletions(tenantId, registrationId) {
    const data = await this.read();
    return data.completions.filter(
      (c) => c.tenantId === tenantId && (!registrationId || c.registrationId === registrationId)
    );
  }
}
