const { Scorm12Adapter } = require('./adapters/scorm12-adapter');
const { Scorm2004Adapter } = require('./adapters/scorm2004-adapter');
const { RuntimeSessionStore } = require('./session-store');
const { SUPPORTED_VERSIONS } = require('./types');

class RuntimeAdapterService {
  constructor({ store } = {}) {
    this.store = store || new RuntimeSessionStore();
    this.adapters = {
      [SUPPORTED_VERSIONS.SCORM_12]: new Scorm12Adapter({ store: this.store }),
      [SUPPORTED_VERSIONS.SCORM_2004]: new Scorm2004Adapter({ store: this.store })
    };
  }

  createLaunchContext({ version, learnerId, courseId, registrationId, scoId, launchMode, initialCmi = {} }) {
    const adapter = this.adapters[version];
    if (!adapter) {
      throw new Error(`Unsupported SCORM version: ${version}`);
    }

    const session = adapter.launchSession(
      { learnerId, courseId, registrationId, scoId, launchMode },
      initialCmi
    );

    return {
      sessionToken: session.sessionToken,
      version,
      launchContext: session.context,
      initialCmi: session.cmi
    };
  }

  handleRuntimeMethod({ version, sessionToken, method, args = [] }) {
    const adapter = this.adapters[version];
    if (!adapter) {
      return { result: 'false', error: `Unsupported SCORM version: ${version}` };
    }

    const session = this.store.getSession(sessionToken);
    if (!session) {
      return { result: 'false', error: `Unknown session token: ${sessionToken}` };
    }

    const result = adapter.invoke(session, method, ...args);

    return {
      result,
      errorCode: session.lastError,
      diagnostics: session.diagnostics,
      synchronizedState: {
        completionStatus: session.cmi['lms.completion_status'] || null,
        progressPercent: session.cmi['lms.progress_percent'] || 0,
        commits: this.store.listCommits(sessionToken).length
      }
    };
  }

  getSupportedVersions() {
    return Object.keys(this.adapters);
  }

  getRuntimeMethods(version) {
    const adapter = this.adapters[version];
    if (!adapter) {
      return [];
    }
    return adapter.getSupportedMethods();
  }
}

module.exports = { RuntimeAdapterService };
