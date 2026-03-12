const { BaseScormAdapter } = require('./base-adapter');
const { RUNTIME_METHODS, SUPPORTED_VERSIONS } = require('../types');

class Scorm2004Adapter extends BaseScormAdapter {
  constructor({ store }) {
    super({ store, version: SUPPORTED_VERSIONS.SCORM_2004 });
    this.methodMap = {
      [RUNTIME_METHODS.INITIALIZE]: this.initialize.bind(this),
      [RUNTIME_METHODS.TERMINATE]: this.terminate.bind(this),
      [RUNTIME_METHODS.GET_VALUE]: this.getValue.bind(this),
      [RUNTIME_METHODS.SET_VALUE]: this.setValue.bind(this),
      [RUNTIME_METHODS.COMMIT]: this.commit.bind(this),
      [RUNTIME_METHODS.GET_LAST_ERROR]: this.getLastError.bind(this),
      [RUNTIME_METHODS.GET_ERROR_STRING]: this.getErrorString.bind(this),
      [RUNTIME_METHODS.GET_DIAGNOSTIC]: this.getDiagnostic.bind(this)
    };
  }

  getSupportedMethods() {
    return Object.keys(this.methodMap);
  }

  invoke(session, method, ...args) {
    const handler = this.methodMap[method];
    if (!handler) {
      session.lastError = '401';
      session.diagnostics = `Unsupported SCORM 2004 method: ${method}`;
      return 'false';
    }
    return handler(session, ...args);
  }
}

module.exports = { Scorm2004Adapter };
