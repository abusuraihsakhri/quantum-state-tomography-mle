/** Maximum-likelihood reconstruction for a single qubit from Pauli counts. */
export function estimatePauliMLE(counts) {
  const axes = ['x', 'y', 'z'];
  if (!counts || typeof counts !== 'object' || Array.isArray(counts) ||
      Object.keys(counts).some(axis => !axes.includes(axis))) {
    throw new Error('Provide counts for X, Y, and/or Z only.');
  }
  const observations = axes.map(axis => {
    const pair = counts[axis] ?? [0, 0];
    if (!Array.isArray(pair) || pair.length !== 2 ||
        !pair.every(v => Number.isSafeInteger(v) && v >= 0)) {
      throw new Error(axis.toUpperCase() + ' outcomes must be non-negative integer counts.');
    }
    return pair;
  });
  const shots = observations.reduce((sum, [plus, minus]) => sum + plus + minus, 0);
  if (!shots || !Number.isSafeInteger(shots)) throw new Error('Enter at least one valid measurement shot.');
  const empirical = observations.map(([p, m]) => p + m ? (p - m) / (p + m) : 0);
  const norm2 = r => r.reduce((sum, component) => sum + component * component, 0);
  let bloch = empirical;
  if (norm2(empirical) > 1) {
    const component = (plus, minus, penalty) => {
      let lo = -1 + 1e-15, hi = 1 - 1e-15;
      for (let i = 0; i < 64; i++) {
        const mid = (lo + hi) / 2;
        const derivative = (minus ? minus / (1 - mid) : 0) -
          (plus ? plus / (1 + mid) : 0) + 2 * penalty * mid;
        if (derivative < 0) lo = mid;
        else hi = mid;
      }
      return (lo + hi) / 2;
    };
    const atPenalty = penalty => observations.map(([p, m]) => p + m ? component(p, m, penalty) : 0);
    let lo = 0, hi = 1;
    while (norm2(atPenalty(hi)) > 1) hi *= 2;
    for (let i = 0; i < 65; i++) {
      const middle = (lo + hi) / 2;
      if (norm2(atPenalty(middle)) > 1) lo = middle;
      else hi = middle;
    }
    bloch = atPenalty(hi);
    const magnitude = Math.sqrt(norm2(bloch));
    if (magnitude > 1) bloch = bloch.map(x => x / magnitude);
  }
  const [x, y, z] = bloch;
  let logLikelihood = 0;
  observations.forEach(([plus, minus], i) => {
    if (plus) logLikelihood += plus * Math.log((1 + bloch[i]) / 2);
    if (minus) logLikelihood += minus * Math.log((1 - bloch[i]) / 2);
  });
  return {
    bloch_vector: {x, y, z},
    density_matrix: [
      [[(1 + z) / 2, 0], [x / 2, -y / 2]],
      [[x / 2, y / 2], [(1 - z) / 2, 0]]
    ],
    purity: (1 + norm2(bloch)) / 2,
    log_likelihood: logLikelihood,
    shots,
    counts: Object.fromEntries(axes.map((axis, i) => [axis, observations[i]]))
  };
}
