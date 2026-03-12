/**
 * Shared runtime constants for SCORM adapters.
 */
const SUPPORTED_VERSIONS = Object.freeze({
  SCORM_12: '1.2',
  SCORM_2004: '2004'
});

const RUNTIME_METHODS = Object.freeze({
  INITIALIZE: 'Initialize',
  TERMINATE: 'Terminate',
  GET_VALUE: 'GetValue',
  SET_VALUE: 'SetValue',
  COMMIT: 'Commit',
  GET_LAST_ERROR: 'GetLastError',
  GET_ERROR_STRING: 'GetErrorString',
  GET_DIAGNOSTIC: 'GetDiagnostic',
  LMS_INITIALIZE: 'LMSInitialize',
  LMS_FINISH: 'LMSFinish',
  LMS_GET_VALUE: 'LMSGetValue',
  LMS_SET_VALUE: 'LMSSetValue',
  LMS_COMMIT: 'LMSCommit',
  LMS_GET_LAST_ERROR: 'LMSGetLastError',
  LMS_GET_ERROR_STRING: 'LMSGetErrorString',
  LMS_GET_DIAGNOSTIC: 'LMSGetDiagnostic'
});

const ERROR_CODES = Object.freeze({
  NO_ERROR: '0',
  GENERAL: '101',
  NOT_INITIALIZED: '301',
  ALREADY_INITIALIZED: '103',
  TERMINATED: '112',
  NOT_IMPLEMENTED: '401',
  INVALID_ARGUMENT: '201',
  READ_ONLY: '404',
  WRITE_ONLY: '405',
  TYPE_MISMATCH: '406'
});

module.exports = {
  SUPPORTED_VERSIONS,
  RUNTIME_METHODS,
  ERROR_CODES
};
