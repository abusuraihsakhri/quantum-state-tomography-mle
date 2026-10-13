import test from 'node:test';
import assert from 'node:assert/strict';

class MockElement {
  constructor(value = '') {
    this._value = String(value);
    this.textContent = '';
    this.style = {};
    this.listeners = {};
    this.parentElement = {setAttribute() {}};
    this.hidden = true;
    this.disabled = true;
  }
  get value() { return this._value; }
  set value(v) { this._value = String(v); }
  addEventListener(name, cb) { this.listeners[name] = cb; }
  setAttribute() {}
  click() { if (this.listeners.click) this.listeners.click(); }
}

const elements = new Map();
const getElementById = id => {
  if (!elements.has(id)) elements.set(id, new MockElement());
  return elements.get(id);
};
for (const axis of ['x', 'y', 'z']) {
  for (const outcome of ['plus', 'minus']) getElementById(axis + '-' + outcome).value = '50';
}
getElementById('x-plus').value = '90';
getElementById('x-minus').value = '10';
globalThis.document = {getElementById, createElement: () => ({click() {}, download: ''})};
let downloaded = false;
globalThis.URL = {
  createObjectURL: () => {downloaded = true; return 'blob:dummy';},
  revokeObjectURL() {}
};
await import('./app.mjs');

test('browser app initializes a physical estimate', () => {
  assert.equal(getElementById('purity').textContent, '0.820000');
  assert.equal(getElementById('results').hidden, false);
  assert.equal(getElementById('download-json').disabled, false);
});
test('example selector updates the estimate', () => {
  const example = getElementById('example');
  example.value = 'pure';
  example.listeners.change({target: example});
  assert.equal(getElementById('purity').textContent, '1.000000');
});
test('invalid measurement input displays an error', () => {
  for (const axis of ['x', 'y', 'z']) {
    for (const outcome of ['plus', 'minus']) getElementById(axis + '-' + outcome).value = '0';
  }
  getElementById('tomography-form').listeners.submit({preventDefault() {}});
  assert.equal(getElementById('results').hidden, true);
  assert.match(getElementById('status').textContent, /at least one valid/i);
});
test('JSON export is offered for a valid result', () => {
  const example = getElementById('example');
  example.value = 'mixed';
  example.listeners.change({target: example});
  getElementById('download-json').click();
  assert.equal(downloaded, true);
});
