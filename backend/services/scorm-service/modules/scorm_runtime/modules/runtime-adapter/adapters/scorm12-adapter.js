const { BaseScormAdapter } = require('./base-adapter');
const { RUNTIME_METHODS, SUPPORTED_VERSIONS } = require('../types');

class Scorm12Adapter extends BaseScormAdapter {
  constructor({ store }) {
    super({ store, version: SUPPORTED_VERSIONS.SCORM_12 });
    this.methodMap = {
      [RUNTIME_METHODS.LMS_INITIALIZE]: this.initialize.bind(this),
      [RUNTIME_METHODS.LMS_FINISH]: this.terminate.bind(this),
      [RUNTIME_METHODS.LMS_GET_VALUE]: this.getValue.bind(this),
      [RUNTIME_METHODS.LMS_SET_VALUE]: this.setValue.bind(this),
      [RUNTIME_METHODS.LMS_COMMIT]: this.commit.bind(this),
      [RUNTIME_METHODS.LMS_GET_LAST_ERROR]: this.getLastError.bind(this),
      [RUNTIME_METHODS.LMS_GET_ERROR_STRING]: this.getErrorString.bind(this),
      [RUNTIME_METHODS.LMS_GET_DIAGNOSTIC]: this.getDiagnostic.bind(this)
    };
  }

  getSupportedMethods() {
    return Object.keys(this.methodMap);
  }

  invoke(session, method, ...args) {
    const handler = this.methodMap[method];
    if (!handler) {
      session.lastError = '401';
      session.diagnostics = `Unsupported SCORM 1.2 method: ${method}`;
      return 'false';
    }
    return handler(session, ...args);
  }
}

module.exports = { Scorm12Adapter };
