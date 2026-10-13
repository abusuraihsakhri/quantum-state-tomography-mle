import test from 'node:test';
import assert from 'node:assert/strict';
import {estimatePauliMLE} from './tomography.mjs';

test('mixed state and Hermitian density matrix', () => {
  const q = estimatePauliMLE({x:[90,10], y:[50,50], z:[50,50]});
  assert.ok(Math.abs(q.bloch_vector.x - 0.8) < 1e-12);
  assert.ok(Math.abs(q.purity - 0.82) < 1e-12);
  assert.equal(q.shots, 300);
  assert.equal(q.density_matrix[0][1][0], q.density_matrix[1][0][0]);
  assert.equal(q.density_matrix[0][1][1], -q.density_matrix[1][0][1]);
});

test('pure state preserves positivity and trace', () => {
  const q = estimatePauliMLE({z:[100,0]});
  assert.equal(q.purity, 1);
  assert.equal(q.density_matrix[0][0][0], 1);
  assert.equal(q.density_matrix[1][1][0], 0);
});

test('constrained MLE remains on Bloch sphere', () => {
  const q = estimatePauliMLE({x:[90,10],y:[18,2],z:[18,2]});
  const r = q.bloch_vector;
  assert.ok(Math.abs(r.x*r.x+r.y*r.y+r.z*r.z-1) < 1e-10);
  assert.ok(r.x > r.y && r.y > 0);
  assert.ok(Math.abs(r.y-r.z) < 1e-10);
});

test('input validation', () => {
  for (const input of [{}, {x:[0,0]}, {x:[-1,2]}, {x:[2.2,1]}, {invalid:[1,0]}, {x:[1]}, {x:[NaN,1]}]) {
    assert.throws(() => estimatePauliMLE(input));
  }
});
