const { ERROR_CODES } = require('../types');

class BaseScormAdapter {
  constructor({ store, version }) {
    this.store = store;
    this.version = version;
    this.readOnlyKeys = new Set(['_version']);
  }

  launchSession(context, initialCmi = {}) {
    const seeded = {
      ...initialCmi,
      _version: this.version,
      'session.start_time': new Date().toISOString()
    };
    return this.store.createSession(context, seeded);
  }

  getLastError(session) {
    return session?.lastError || ERROR_CODES.GENERAL;
  }

  getErrorString(code) {
    const map = {
      [ERROR_CODES.NO_ERROR]: 'No error',
      [ERROR_CODES.GENERAL]: 'General exception',
      [ERROR_CODES.INVALID_ARGUMENT]: 'Invalid argument error',
      [ERROR_CODES.NOT_INITIALIZED]: 'Session not initialized',
      [ERROR_CODES.ALREADY_INITIALIZED]: 'Already initialized',
      [ERROR_CODES.TERMINATED]: 'Termination after termination',
      [ERROR_CODES.NOT_IMPLEMENTED]: 'Not implemented',
      [ERROR_CODES.READ_ONLY]: 'Element is read only',
      [ERROR_CODES.WRITE_ONLY]: 'Element is write only',
      [ERROR_CODES.TYPE_MISMATCH]: 'Type mismatch'
    };
    return map[code] || 'Unknown error';
  }

  getDiagnostic(session) {
    return session?.diagnostics || '';
  }

  initialize(session) {
    if (session.terminated) {
      return this.#asError(session, ERROR_CODES.TERMINATED, 'Cannot initialize terminated session.');
    }
    if (session.initialized) {
      return this.#asError(session, ERROR_CODES.ALREADY_INITIALIZED, 'Session already initialized.');
    }
    session.initialized = true;
    session.lastError = ERROR_CODES.NO_ERROR;
    return 'true';
  }

  terminate(session) {
    if (!session.initialized) {
      return this.#asError(session, ERROR_CODES.NOT_INITIALIZED, 'Session not initialized.');
    }
    this.store.commit(session.sessionToken);
    this.store.terminateSession(session.sessionToken);
    session.lastError = ERROR_CODES.NO_ERROR;
    return 'true';
  }

  getValue(session, key) {
    if (!session.initialized) {
      return this.#asError(session, ERROR_CODES.NOT_INITIALIZED, 'Session not initialized.');
    }
    if (!(key in session.cmi)) {
      session.lastError = ERROR_CODES.NO_ERROR;
      return '';
    }
    session.lastError = ERROR_CODES.NO_ERROR;
    return String(session.cmi[key]);
  }

  setValue(session, key, value) {
    if (!session.initialized) {
      return this.#asError(session, ERROR_CODES.NOT_INITIALIZED, 'Session not initialized.');
    }
    if (this.readOnlyKeys.has(key)) {
      return this.#asError(session, ERROR_CODES.READ_ONLY, `Cannot set read-only key: ${key}`);
    }

    this.store.saveValue(session.sessionToken, key, value);
    this.#refreshProgress(session);
    session.lastError = ERROR_CODES.NO_ERROR;
    return 'true';
  }

  commit(session) {
    if (!session.initialized) {
      return this.#asError(session, ERROR_CODES.NOT_INITIALIZED, 'Session not initialized.');
    }
    this.store.commit(session.sessionToken);
    session.lastError = ERROR_CODES.NO_ERROR;
    return 'true';
  }

  #asError(session, code, diagnostics) {
    if (session) {
      session.lastError = code;
      session.diagnostics = diagnostics;
    }
    return 'false';
  }

  #refreshProgress(session) {
    const score = Number(session.cmi['cmi.core.score.raw'] ?? session.cmi['cmi.score.raw'] ?? 0);
    const completionStatus = session.cmi['cmi.completion_status'] || session.cmi['cmi.core.lesson_status'] || 'incomplete';

    session.cmi['lms.progress_percent'] = Number.isNaN(score) ? 0 : Math.max(0, Math.min(score, 100));
    session.cmi['lms.completion_status'] = completionStatus;
  }
}

module.exports = { BaseScormAdapter };
