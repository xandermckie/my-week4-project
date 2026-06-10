/* Pomodoro focus timer — persists across page navigation via localStorage. */

(function () {
  var PHASES = {
    work:      { label: 'Focus',       seconds: 25 * 60, next: 'break' },
    break:     { label: 'Short Break', seconds: 5 * 60,  next: 'work'  },
    longbreak: { label: 'Long Break',  seconds: 15 * 60, next: 'work'  },
  };
  var WORK_CYCLES_BEFORE_LONG = 4;
  var STORAGE_KEY = 'ratio_pomodoro';

  var state = loadState();
  var ticker = null;

  // ── DOM build (no innerHTML — all elements created safely) ─────────────────

  function el(tag, attrs, text) {
    var node = document.createElement(tag);
    if (attrs) {
      Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  var widget   = el('div', { id: 'pomodoro', class: 'pomodoro' + (state.minimized ? ' pomodoro--minimized' : '') });

  // Pill (collapsed view)
  var pill     = el('div', { class: 'pomodoro__pill', id: 'pomPill' });
  var pillTime = el('span', { class: 'pomodoro__pill-time', id: 'pomPillTime' }, '25:00');
  var btnExpand = el('button', { class: 'pomodoro__pill-toggle', id: 'pomExpand', 'aria-label': 'Expand timer' });
  btnExpand.textContent = '▲';
  pill.appendChild(pillTime);
  pill.appendChild(btnExpand);

  // Body (expanded view)
  var body     = el('div', { class: 'pomodoro__body', id: 'pomBody' });
  var header   = el('div', { class: 'pomodoro__header' });
  var phaseEl  = el('span', { class: 'pomodoro__phase', id: 'pomPhase' }, 'Focus');
  var btnCollapse = el('button', { class: 'pomodoro__close', id: 'pomCollapse', 'aria-label': 'Collapse timer' });
  btnCollapse.textContent = '▼';
  header.appendChild(phaseEl);
  header.appendChild(btnCollapse);

  var timeEl   = el('div',  { class: 'pomodoro__time',     id: 'pomTime' },  '25:00');
  var dotsEl   = el('div',  { class: 'pomodoro__dots',     id: 'pomDots' });
  var controls = el('div',  { class: 'pomodoro__controls' });
  var btnPlay  = el('button', { class: 'pomodoro__btn pomodoro__btn--play', id: 'pomPlay', 'aria-label': 'Start' });
  btnPlay.textContent = '▶';
  var btnReset = el('button', { class: 'pomodoro__btn', id: 'pomReset', 'aria-label': 'Reset' });
  btnReset.textContent = '↻';
  controls.appendChild(btnPlay);
  controls.appendChild(btnReset);

  body.appendChild(header);
  body.appendChild(timeEl);
  body.appendChild(dotsEl);
  body.appendChild(controls);

  widget.appendChild(pill);
  widget.appendChild(body);
  document.body.appendChild(widget);

  // ── State helpers ──────────────────────────────────────────────────────────

  function loadState() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return {
      phase: 'work',
      secondsLeft: PHASES.work.seconds,
      cyclesCompleted: 0,
      running: false,
      minimized: true,
      lastTick: null,
    };
  }

  function saveState() {
    try { localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); } catch (e) {}
  }

  function fmt(seconds) {
    var m = Math.floor(seconds / 60);
    var s = seconds % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  function render() {
    var timeStr = fmt(state.secondsLeft);
    timeEl.textContent = timeStr;
    pillTime.textContent = timeStr;
    phaseEl.textContent = PHASES[state.phase].label;
    btnPlay.textContent = state.running ? '❚❚' : '▶';
    btnPlay.setAttribute('aria-label', state.running ? 'Pause' : 'Start');

    // Cycle dots — filled for completed work cycles in current set.
    while (dotsEl.firstChild) dotsEl.removeChild(dotsEl.firstChild);
    for (var i = 0; i < WORK_CYCLES_BEFORE_LONG; i++) {
      var dot = el('span', {
        class: 'pomodoro__dot' + (i < state.cyclesCompleted % WORK_CYCLES_BEFORE_LONG ? ' pomodoro__dot--done' : ''),
      });
      dotsEl.appendChild(dot);
    }

    widget.className = 'pomodoro' + (state.minimized ? ' pomodoro--minimized' : '');

    if (state.running && document.hidden) {
      document.title = timeStr + ' | Ratio';
    }
  }

  // ── Tick ───────────────────────────────────────────────────────────────────

  function tick() {
    if (!state.running) return;
    if (state.lastTick) {
      var elapsed = Math.round((Date.now() - state.lastTick) / 1000);
      state.secondsLeft = Math.max(0, state.secondsLeft - elapsed);
    } else {
      state.secondsLeft = Math.max(0, state.secondsLeft - 1);
    }
    state.lastTick = Date.now();
    if (state.secondsLeft <= 0) advance();
    saveState();
    render();
  }

  function advance() {
    var finished = state.phase;
    if (finished === 'work') {
      state.cyclesCompleted += 1;
      state.phase = (state.cyclesCompleted % WORK_CYCLES_BEFORE_LONG === 0) ? 'longbreak' : 'break';
    } else {
      state.phase = 'work';
    }
    state.secondsLeft = PHASES[state.phase].seconds;
    state.running = true;
    state.lastTick = Date.now();
    notify(PHASES[state.phase].label);
    beep();
  }

  // ── Controls ───────────────────────────────────────────────────────────────

  function startStop() {
    if (state.running) {
      state.running = false;
      state.lastTick = null;
      clearInterval(ticker);
      ticker = null;
    } else {
      state.running = true;
      state.lastTick = Date.now();
      requestNotifPermission();
      ticker = setInterval(tick, 1000);
    }
    saveState();
    render();
  }

  function reset() {
    clearInterval(ticker);
    ticker = null;
    state.running = false;
    state.phase = 'work';
    state.secondsLeft = PHASES.work.seconds;
    state.lastTick = null;
    saveState();
    render();
  }

  // ── Notifications ──────────────────────────────────────────────────────────

  function requestNotifPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }

  function notify(phaseLabel) {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification('Ratio Timer', { body: 'Time for: ' + phaseLabel });
    }
  }

  // ── Audio alert (Web Audio API) ────────────────────────────────────────────

  function beep() {
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.8);
    } catch (e) {}
  }

  // ── Event wiring ───────────────────────────────────────────────────────────

  btnPlay.addEventListener('click', startStop);
  btnReset.addEventListener('click', reset);
  btnExpand.addEventListener('click', function () {
    state.minimized = false; saveState(); render();
  });
  btnCollapse.addEventListener('click', function () {
    state.minimized = true; saveState(); render();
  });

  // Resume timer after page navigation.
  if (state.running) {
    if (state.lastTick) {
      var missed = Math.round((Date.now() - state.lastTick) / 1000);
      state.secondsLeft = Math.max(0, state.secondsLeft - missed);
      if (state.secondsLeft === 0) advance();
    }
    state.lastTick = Date.now();
    ticker = setInterval(tick, 1000);
  }

  render();
})();
