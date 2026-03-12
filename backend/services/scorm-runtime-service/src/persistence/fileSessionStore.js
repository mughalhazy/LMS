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
      await fs.writeFile(this.filePath, JSON.stringify({ sessions: [] }, null, 2));
    }
  }

  async list() {
    const raw = await fs.readFile(this.filePath, "utf8");
    const data = JSON.parse(raw);
    return data.sessions ?? [];
  }

  async getById(sessionId) {
    const sessions = await this.list();
    return sessions.find((s) => s.sessionId === sessionId) ?? null;
  }

  async save(session) {
    this.writeQueue = this.writeQueue.then(async () => {
      const sessions = await this.list();
      const index = sessions.findIndex((s) => s.sessionId === session.sessionId);
      if (index >= 0) sessions[index] = session;
      else sessions.push(session);
      await fs.writeFile(this.filePath, JSON.stringify({ sessions }, null, 2));
    });

    await this.writeQueue;
    return session;
  }
}
