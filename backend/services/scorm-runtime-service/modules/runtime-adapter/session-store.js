const { randomUUID } = require('node:crypto');

/**
 * In-memory persistence layer used by adapters to synchronize runtime state.
 */
class RuntimeSessionStore {
  constructor() {
    this.sessions = new Map();
    this.attemptHistory = new Map();
  }

  createSession(context, initialCmi = {}) {
    const sessionToken = randomUUID();
    const session = {
      sessionToken,
      context,
      createdAt: new Date().toISOString(),
      initialized: false,
      terminated: false,
      cmi: { ...initialCmi },
      lastError: '0',
      diagnostics: '',
      pendingChanges: {},
      commits: 0
    };

    this.sessions.set(sessionToken, session);
    this.attemptHistory.set(sessionToken, []);
    return session;
  }

  getSession(sessionToken) {
    return this.sessions.get(sessionToken) || null;
  }

  saveValue(sessionToken, key, value) {
    const session = this.getSession(sessionToken);
    if (!session) {
      return null;
    }

    session.cmi[key] = value;
    session.pendingChanges[key] = value;
    return session;
  }

  commit(sessionToken) {
    const session = this.getSession(sessionToken);
    if (!session) {
      return null;
    }

    const history = this.attemptHistory.get(sessionToken);
    history.push({
      committedAt: new Date().toISOString(),
      delta: { ...session.pendingChanges },
      snapshot: { ...session.cmi }
    });
    session.pendingChanges = {};
    session.commits += 1;
    return history[history.length - 1];
  }

  terminateSession(sessionToken) {
    const session = this.getSession(sessionToken);
    if (!session) {
      return null;
    }
    session.terminated = true;
    session.terminatedAt = new Date().toISOString();
    return session;
  }

  listCommits(sessionToken) {
    return this.attemptHistory.get(sessionToken) || [];
  }
}

module.exports = { RuntimeSessionStore };
