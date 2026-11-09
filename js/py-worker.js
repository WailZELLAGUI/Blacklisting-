/* Runs our Python code (simulator, features, grades) in a background thread with Pyodide. */
const VERSIONS = ['v0.29.4', 'v0.29.3', 'v0.28.3', 'v0.27.7'];
const FILES = ['sim.py', 'features.py', 'detectors.py', 'detectors2.py', 'detectors3.py', 'configs.py', 'webapi.py',
  'rules.json', 'realdata/out/blte_params.json'];
const ALLOWED = new Set(['new_world', 'grade', 'fraud_graph', 'sample_rows']);
let py = null;

async function init() {
  let version = null;
  for (const v of VERSIONS) {
    try { importScripts(`https://cdn.jsdelivr.net/pyodide/${v}/full/pyodide.js`); version = v; break; } catch (e) { /* try the next one */ }
  }
  if (!version) throw new Error('Python (Pyodide) could not be loaded from cdn.jsdelivr.net');
  postMessage({ type: 'progress', step: 'python', version });
  py = await loadPyodide({ indexURL: `https://cdn.jsdelivr.net/pyodide/${version}/full/` });
  postMessage({ type: 'progress', step: 'packages' });
  await py.loadPackage(['numpy', 'pandas']);
  postMessage({ type: 'progress', step: 'code' });
  py.FS.mkdirTree('/app/realdata/out');
  for (const f of FILES) {
    const r = await fetch(new URL('../py/' + f, self.location.href));
    if (!r.ok) throw new Error('missing file py/' + f);
    py.FS.writeFile('/app/' + f, await r.text());
  }
  py.runPython("import sys\nsys.path.insert(0, '/app')\nimport webapi");
  return version;
}

const ready = init().then(
  v => { postMessage({ type: 'ready', version: v }); return true; },
  e => { postMessage({ type: 'failed', error: String(e && e.message || e) }); return false; });

onmessage = async (ev) => {
  const { id, fn, arg } = ev.data;
  const ok = await ready;
  if (!ok) { postMessage({ id, ok: false, error: 'Python is not available' }); return; }
  if (!ALLOWED.has(fn)) { postMessage({ id, ok: false, error: 'unknown function ' + fn }); return; }
  try {
    py.globals.set('ARG', arg === undefined ? null : arg);
    const t0 = performance.now();
    const res = py.runPython(`webapi.${fn}(ARG) if ARG is not None else webapi.${fn}()`);
    postMessage({ id, ok: true, result: res, ms: performance.now() - t0 });
  } catch (e) {
    postMessage({ id, ok: false, error: String(e && e.message || e).slice(-800) });
  }
};
