// Run: node --experimental-vm-modules scripts/test-dotnet-performance.mjs
// Exercise the shipped k6 script with mock transport; not a k6 load test.
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import vm from 'node:vm';

const source = await readFile(new URL('../plugins/dotnet/skills/dotnet-scaffold/assets/performance/smoke.js', import.meta.url), 'utf8');

async function load(env = {}, status = 200) {
  const calls = [];
  const context = vm.createContext({ __ENV: env });
  const http = {
    expectedStatuses: (value) => ({ expected: value }),
    get: (url, options) => { calls.push({ url, options }); return { status }; },
  };
  const modules = {
    'k6/http': new vm.SyntheticModule(['default'], function () { this.setExport('default', http); }, { context }),
    k6: new vm.SyntheticModule(['check', 'sleep'], function () {
      this.setExport('check', (response, checks) => { calls.push({ checks: Object.values(checks).map((fn) => fn(response)) }); });
      this.setExport('sleep', (seconds) => calls.push({ sleep: seconds }));
    }, { context }),
  };
  const module = new vm.SourceTextModule(source, { context });
  await module.link((name) => { assert.ok(modules[name], `Unexpected import ${name}`); return modules[name]; });
  await module.evaluate();
  return { api: module.namespace, calls };
}

const baseline = await load();
assert.equal(baseline.api.options.vus, 2);
assert.equal(baseline.api.options.duration, '10s');
assert.equal(Object.keys(baseline.api.options.thresholds).length, 0);
baseline.api.default();
assert.equal(baseline.calls[0].url, 'http://127.0.0.1:5080/health');
assert.equal(baseline.calls[0].options.redirects, 0);
assert.equal(baseline.calls[0].options.timeout, '10s');
assert.deepEqual(baseline.calls[1].checks, [true]);
assert.equal(baseline.calls[2].sleep, 1);

const configured = await load({ BASE_URL: 'http://localhost:9000/', TARGET_PATH: '/ready', VUS: '3', EXPECTED_STATUS: '204', P95_MS: '100', MAX_ERROR_RATE: '0' }, 204);
configured.api.default();
assert.equal(configured.calls[0].url, 'http://localhost:9000/ready');
assert.equal(configured.calls[0].options.responseCallback.expected, 204);
assert.equal(configured.api.options.thresholds.http_req_duration[0], 'p(95)<100');
assert.equal(configured.api.options.thresholds.http_req_failed[0], 'rate<=0');
assert.deepEqual(configured.calls[1].checks, [true]);
const failure = await load({}, 500);
failure.api.default();
assert.deepEqual(failure.calls[1].checks, [false]);
for (const invalid of [{ VUS: '0' }, { VUS: '1.5' }, { P95_MS: 'NaN' }, { P95_MS: '-1' }, { MAX_ERROR_RATE: '2' }, { MAX_ERROR_RATE: '-1' }, { TARGET_PATH: '//other.test' }, { BASE_URL: 'file:///tmp/data' }, { EXPECTED_STATUS: '999' }]) {
  await assert.rejects(() => load(invalid));
}
console.log('PASS: k6 script defaults, configured thresholds, HTTP contract, failure checks and invalid inputs (mock transport)');
