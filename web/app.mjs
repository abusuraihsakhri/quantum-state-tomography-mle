import {estimatePauliMLE} from './tomography.mjs';

const el = id => document.getElementById(id);
const axes = ['x', 'y', 'z'];
let lastResult = null;

function readCounts() {
  return Object.fromEntries(axes.map(axis => {
    const pair = ['plus', 'minus'].map(outcome => {
      const input = el(axis + '-' + outcome);
      if (!input.value.trim() || !/^\d+$/.test(input.value.trim())) {
        throw new Error(axis.toUpperCase() + ' ' + outcome + ' must be a non-negative integer.');
      }
      const value = Number(input.value);
      if (!Number.isSafeInteger(value)) throw new Error('Counts exceed the supported integer range.');
      return value;
    });
    return [axis, pair];
  }));
}

function pretty(n) { return (Math.abs(n) < 5e-13 ? 0 : n).toFixed(6); }
function complex([real, imaginary]) {
  return pretty(real) + (imaginary < -5e-13 ? ' − ' : ' + ') + pretty(Math.abs(imaginary)) + 'i';
}

function render(result) {
  const {bloch_vector: vector, density_matrix: rho} = result;
  el('shots').textContent = result.shots.toLocaleString();
  el('purity').textContent = pretty(result.purity);
  el('likelihood').textContent = pretty(result.log_likelihood);
  el('matrix').textContent = '[ ' + complex(rho[0][0]) + '     ' + complex(rho[0][1]) + ' ]\n' +
    '[ ' + complex(rho[1][0]) + '     ' + complex(rho[1][1]) + ' ]';
  axes.forEach(axis => {
    const value = vector[axis];
    el(axis + '-value').textContent = pretty(value);
    const meter = el(axis + '-bar');
    meter.style.left = (50 + Math.min(0, value) * 50) + '%';
    meter.style.width = (Math.abs(value) * 50) + '%';
    meter.parentElement.setAttribute('aria-label', axis.toUpperCase() + ' component: ' + pretty(value));
  });
  el('results').hidden = false;
  el('download-json').disabled = false;
  el('download-csv').disabled = false;
  el('status').textContent = 'Reconstructed from ' + result.shots + ' measurements. The density matrix is positive semidefinite with unit trace.';
  el('status').className = 'status success';
}

function run() {
  try {
    const result = estimatePauliMLE(readCounts());
    lastResult = result;
    render(result);
  } catch (error) {
    lastResult = null;
    el('results').hidden = true;
    el('download-json').disabled = true;
    el('download-csv').disabled = true;
    el('status').textContent = error.message;
    el('status').className = 'status error';
  }
}

function download(filename, content, mime) {
  const url = URL.createObjectURL(new Blob([content], {type: mime}));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

el('tomography-form').addEventListener('submit', event => { event.preventDefault(); run(); });
el('example').addEventListener('change', event => {
  const cases = {
    mixed: [[90, 10], [50, 50], [50, 50]],
    pure: [[50, 50], [50, 50], [100, 0]],
    boundary: [[90, 10], [90, 10], [90, 10]],
  };
  const example = cases[event.target.value];
  if (!example) return;
  axes.forEach((axis, i) => {
    el(axis + '-plus').value = example[i][0];
    el(axis + '-minus').value = example[i][1];
  });
  run();
});
el('download-json').addEventListener('click', () => {
  if (lastResult) download('tomography-mle.json', JSON.stringify(lastResult, null, 2) + '\n', 'application/json');
});
el('download-csv').addEventListener('click', () => {
  if (!lastResult) return;
  const rows = ['axis,plus,minus,bloch_component', ...axes.map(axis =>
    [axis, ...lastResult.counts[axis], lastResult.bloch_vector[axis]].join(','))];
  download('tomography-mle.csv', rows.join('\n') + '\n', 'text/csv');
});
run();
