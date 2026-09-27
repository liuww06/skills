import http from 'k6/http';
import { check, sleep } from 'k6';

const baseUrl = (__ENV.BASE_URL || 'http://127.0.0.1:5080').replace(/\/$/, '');
const targetPath = __ENV.TARGET_PATH || '/health';
const vus = Number(__ENV.VUS || '2');
const expectedStatus = Number(__ENV.EXPECTED_STATUS || '200');
if (!/^https?:\/\//.test(baseUrl) || !targetPath.startsWith('/') || targetPath.startsWith('//')) {
  throw new Error('BASE_URL must be HTTP(S); TARGET_PATH must start with a single slash.');
}
if (!Number.isInteger(vus) || vus < 1 || !Number.isInteger(expectedStatus) || expectedStatus < 100 || expectedStatus > 599) {
  throw new Error('VUS must be a positive integer; EXPECTED_STATUS must be an HTTP status code.');
}

const thresholds = {};
if (__ENV.P95_MS !== undefined) {
  const p95 = Number(__ENV.P95_MS);
  if (!Number.isFinite(p95) || p95 <= 0) throw new Error('P95_MS must be positive.');
  thresholds.http_req_duration = [`p(95)<${p95}`];
}
if (__ENV.MAX_ERROR_RATE !== undefined) {
  const errorRate = Number(__ENV.MAX_ERROR_RATE);
  if (!Number.isFinite(errorRate) || errorRate < 0 || errorRate > 1) {
    throw new Error('MAX_ERROR_RATE must be between 0 and 1.');
  }
  thresholds.http_req_failed = [`rate<=${errorRate}`];
}

export const options = {
  vus,
  duration: __ENV.DURATION || '10s',
  thresholds,
  summaryTrendStats: ['avg', 'min', 'med', 'max', 'p(95)', 'p(99)'],
};

export default function () {
  const response = http.get(`${baseUrl}${targetPath}`, {
    timeout: '10s',
    redirects: 0,
    responseCallback: http.expectedStatuses(expectedStatus),
  });
  check(response, { 'expected status': (result) => result.status === expectedStatus });
  sleep(1);
}
