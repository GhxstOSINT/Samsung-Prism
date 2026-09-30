const form = document.querySelector('#troubleshootForm');
const query = document.querySelector('#query');
const siis = document.querySelector('#siis');
const runButton = document.querySelector('#runButton');
const formStatus = document.querySelector('#formStatus');
const result = document.querySelector('#result');
const emptyState = document.querySelector('#emptyState');
const copyButton = document.querySelector('#copyButton');
let latestPayload = null;

function setStage(index) {
  document.querySelectorAll('.stage').forEach((stage, i) => {
    stage.classList.toggle('active', i === index);
    stage.classList.toggle('complete', i < index);
    if (i === index) stage.setAttribute('aria-current', 'step');
    else stage.removeAttribute('aria-current');
  });
}

const pause = (ms) => new Promise(resolve => setTimeout(resolve, ms));

function escapeText(value) {
  const node = document.createElement('span');
  node.textContent = value ?? '';
  return node.innerHTML;
}

function render(payload) {
  latestPayload = payload;
  const context = payload.response.contexts[0];
  emptyState.hidden = true;
  result.hidden = false;
  copyButton.disabled = false;
  document.querySelector('#resultTitle').textContent = context?.title ?? payload.meta.fallback ?? 'No validated match';
  document.querySelector('#resultScore').textContent = context ? `${Math.round(context.score * 100)}%` : '-';
  const paths = {
    validated_cache: 'Validated cache',
    two_stage_llm_validated: 'Two-stage model',
    deterministic_grounded_fallback: 'Grounded fallback'
  };
  document.querySelector('#resultPath').textContent = paths[payload.meta.mode] || payload.meta.mode;
  document.querySelector('#resultLatency').textContent = `${payload.meta.latency_ms.toFixed(2)} ms`;

  const actions = document.querySelector('#actionList');
  actions.innerHTML = context ? payload.response.contexts.map((plan, planIndex) => {
    const heading = payload.response.contexts.length > 1 ? `<li class="context-divider"><span>Issue ${planIndex + 1}</span><strong>${escapeText(plan.title)}</strong></li>` : '';
    return heading + plan.actions.map(action => {
      const group = action.stepGroups[0];
      const deeplink = group.actionableDeeplink;
      return `<li class="action-item"><div><div class="action-title"><h3>${escapeText(action.actionName)}</h3><span class="category ${escapeText(action.category)}">${escapeText(action.category)}</span></div><p>${escapeText(action.description)}</p><ul>${group.steps.map(step => `<li>${escapeText(step)}</li>`).join('')}</ul>${deeplink ? `<div class="deeplink"><b>Verified deeplink</b><span>${escapeText(deeplink.deeplink)}</span></div>` : ''}</div></li>`;
    }).join('');
  }).join('') : '<li class="action-item"><div><div class="action-title"><h3>No safe match</h3></div><p>The engine did not find enough grounded evidence to produce a plan.</p></div></li>';

  document.querySelector('#traceList').innerHTML = payload.meta.trace.map(item => `<li><span>${escapeText(item.stage)}</span><span>${escapeText(item.detail)}</span><span>${item.duration_ms.toFixed(2)} ms</span></li>`).join('');
  document.querySelector('#jsonOutput').textContent = JSON.stringify(payload, null, 2);
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  runButton.disabled = true;
  runButton.classList.add('loading');
  formStatus.className = 'form-status';
  formStatus.textContent = 'Enriching and validating the complaint';
  setStage(0);
  try {
    const response = await fetch('/v1/troubleshoot', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query: query.value, siis_response: siis.value || null, debug: true})
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || payload.error || 'Request failed');
    for (let index = 1; index <= 3; index += 1) {
      await pause(window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 110);
      setStage(index);
    }
    render(payload);
    formStatus.textContent = payload.meta.cache_hit ? 'Served from the validated fast path.' : 'Plan passed all deterministic checks.';
    setStage(3);
  } catch (error) {
    formStatus.className = 'form-status error';
    formStatus.textContent = `Could not build a plan: ${error.message}`;
  } finally {
    runButton.disabled = false;
    runButton.classList.remove('loading');
  }
});

document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => {
  query.value = button.dataset.query;
  query.focus();
}));

copyButton.addEventListener('click', async () => {
  if (!latestPayload) return;
  await navigator.clipboard.writeText(JSON.stringify(latestPayload, null, 2));
  copyButton.textContent = 'Copied';
  setTimeout(() => copyButton.textContent = 'Copy JSON', 1200);
});

fetch('/health').then(response => response.json()).then(payload => {
  const runtime = payload.llm_available ? `model ${payload.model_id}` : 'deterministic fallback';
  document.querySelector('#healthLabel').textContent = `${payload.catalog_entries} deeplinks, ${payload.knowledge_records} plans, ${runtime}`;
  document.querySelector('#dataLabel').textContent = payload.data_source === 'official' ? `Official assets · ${payload.catalog_version}` : 'Synthetic demonstration data';
  document.querySelector('.state-dot').classList.add('ok');
}).catch(() => {
  document.querySelector('#healthLabel').textContent = 'Service unavailable';
});
