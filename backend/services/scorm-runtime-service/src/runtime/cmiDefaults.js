export const SCORM_12_DEFAULTS = {
  "cmi.core.lesson_location": "",
  "cmi.core.lesson_status": "not attempted",
  "cmi.core.score.raw": "",
  "cmi.core.session_time": "0000:00:00.00",
  "cmi.core.total_time": "0000:00:00.00",
  "cmi.suspend_data": ""
};

export const SCORM_2004_DEFAULTS = {
  "cmi.location": "",
  "cmi.completion_status": "unknown",
  "cmi.success_status": "unknown",
  "cmi.score.raw": "",
  "cmi.session_time": "PT0S",
  "cmi.total_time": "PT0S",
  "cmi.suspend_data": ""
};

export function defaultsForVersion(version) {
  return version === "1.2" ? { ...SCORM_12_DEFAULTS } : { ...SCORM_2004_DEFAULTS };
}
