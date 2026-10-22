/*
  ==============================================================================
  SmartHome Pro - Liquid Crystal Glass Client Logic
  Multi-screen SPA with real-time SSE telemetry, sparklines, and hardware controls
  ==============================================================================
*/

// Application State (Clean Hardware Telemetry)
let currentState = {
  temp: null,
  hum: null,
  gas: null,
  flame: null,
  pir: null,
  ldr: null,
  ir: null,
  dist: null,
  light: 0,
  light1: 0,
  light2: 0,
  light3: 0,
  light4: 0,
  door: 0,
  fan: 0,
  alarm: 0,
  mode: "AUTO",
  mqtt: "Connecting...",
  arduino: "Disconnected",
  active_port: "None",
  has_real_data: false
};

// Rolling History Buffers for 6-Bar Sparklines (Populated only with live sensor readings)
const SPARK_SAMPLES = 6;
let historyGas = [];
let historyFlame = [];
let historyTemp = [];
let historyHum = [];
let historyLdr = [];

// Audio & Alarm State
let audioCtx = null;
let alarmBeepInterval = null;
let audioAlertsEnabled = true;

// -----------------------------------------------------------------------------
// Navigation Screen Switcher
// -----------------------------------------------------------------------------
function showScreen(screenId) {
  // Hide all screens
  document.querySelectorAll('.screen-view').forEach(el => {
    el.classList.add('hidden');
  });

  // Show active screen
  const target = document.getElementById(`screen-${screenId}`);
  if (target) {
    target.classList.remove('hidden');
  }

  // Update bottom nav active state
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.remove('active');
    el.classList.add('text-on-surface-variant');
  });

  const activeBtn = document.getElementById(`nav-btn-${screenId}`);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.classList.remove('text-on-surface-variant');
  }

  // Save screen preference
  localStorage.setItem('smarthome_active_tab', screenId);
}

// -----------------------------------------------------------------------------
// Web Audio API Synthesizer
// -----------------------------------------------------------------------------
function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
  if (audioCtx && audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
}

function playTone(freq = 880, duration = 0.2, type = 'sawtooth') {
  if (!audioAlertsEnabled) return;
  try {
    initAudio();
    if (!audioCtx) return;

    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();

    osc.type = type;
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

    gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

    osc.connect(gain);
    gain.connect(audioCtx.destination);

    osc.start();
    osc.stop(audioCtx.currentTime + duration);
  } catch (e) {
    // Audio autoplay restrictions
  }
}

function startAlarmSiren() {
  if (!audioAlertsEnabled) return;
  if (!alarmBeepInterval) {
    playTone(950, 0.25, 'sawtooth');
    alarmBeepInterval = setInterval(() => {
      playTone(950, 0.25, 'sawtooth');
    }, 500);
  }
}

function stopAlarmSiren() {
  if (alarmBeepInterval) {
    clearInterval(alarmBeepInterval);
    alarmBeepInterval = null;
  }
}

function toggleAudioMute() {
  audioAlertsEnabled = !audioAlertsEnabled;
  const icon = document.getElementById('icon-audio-mute');
  if (icon) {
    icon.textContent = audioAlertsEnabled ? 'volume_up' : 'volume_off';
  }
  if (!audioAlertsEnabled) {
    stopAlarmSiren();
    showNotification('Audio alerts muted');
  } else {
    playTone(600, 0.1, 'sine');
    showNotification('Audio alerts enabled');
  }
}

// -----------------------------------------------------------------------------
// REST API Helpers
// -----------------------------------------------------------------------------
async function postAPI(endpoint, data = null) {
  try {
    const opts = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    };
    if (data !== null) {
      opts.body = JSON.stringify(data);
    }
    const res = await fetch(endpoint, opts);
    return await res.json();
  } catch (err) {
    console.warn(`Failed POST ${endpoint}:`, err);
    return null;
  }
}

// -----------------------------------------------------------------------------
// Telemetry & Sparkline Calculations
// -----------------------------------------------------------------------------
function pushSparkline(arr, val) {
  arr.push(val);
  if (arr.length > SPARK_SAMPLES) arr.shift();
  return arr;
}

function renderSparkline(containerId, values, minVal, maxVal, isAlert = false) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const bars = container.querySelectorAll('div');
  const range = (maxVal - minVal) || 1;

  if (values.length === 0) {
    bars.forEach((bar) => {
      bar.style.height = '4px';
      bar.className = 'w-3 bg-surface-variant/30 rounded-t transition-all';
    });
    return;
  }

  const offset = Math.max(0, bars.length - values.length);
  bars.forEach((bar, idx) => {
    if (idx < offset) {
      bar.style.height = '4px';
      bar.className = 'w-3 bg-surface-variant/20 rounded-t transition-all';
    } else {
      const val = values[idx - offset];
      const normalized = Math.max(0.08, Math.min(1.0, (val - minVal) / range));
      const heightPx = Math.round(normalized * 28) + 4; // 4px to 32px
      bar.style.height = `${heightPx}px`;

      if (isAlert) {
        bar.className = 'w-3 bg-error rounded-t transition-all shadow-[0_0_8px_#ffb4ab]';
      } else {
        const opacity = Math.round(((idx - offset + 1) / values.length) * 80) + 20;
        bar.className = `w-3 bg-primary-container/${opacity} rounded-t transition-all`;
      }
    }
  });
}

function updateSparklines(data) {
  const hasData = Boolean(data.has_real_data || (data.temp !== null && data.temp > 0));
  if (!hasData) return;

  if (data.gas !== null && data.gas !== undefined) {
    pushSparkline(historyGas, data.gas);
    renderSparkline('spark-gas', historyGas, 50, 600, data.gas >= 400);
  }
  if (data.flame !== null && data.flame !== undefined) {
    pushSparkline(historyFlame, data.flame);
    renderSparkline('spark-flame', historyFlame, 0, 1, data.flame === 1);
  }
  if (data.temp !== null && data.temp !== undefined) {
    pushSparkline(historyTemp, data.temp);
    renderSparkline('spark-temp', historyTemp, 15, 35);
  }
  if (data.hum !== null && data.hum !== undefined) {
    pushSparkline(historyHum, data.hum);
    renderSparkline('spark-hum', historyHum, 20, 85);
  }
  if (data.ldr !== null && data.ldr !== undefined) {
    pushSparkline(historyLdr, data.ldr);
    renderSparkline('spark-ldr', historyLdr, 100, 1023);
  }
}

// -----------------------------------------------------------------------------
// Real-Time UI Dispatcher
// -----------------------------------------------------------------------------
function updateUI(data) {
  currentState = { ...currentState, ...data };

  // 1. Dynamic Greeting based on current hour
  const hour = new Date().getHours();
  const greetingEl = document.getElementById('greeting-text');
  if (greetingEl) {
    if (hour < 12) greetingEl.textContent = 'Good morning';
    else if (hour < 18) greetingEl.textContent = 'Good afternoon';
    else greetingEl.textContent = 'Good evening';
  }

  // 2. Hardware / MQTT Status Header Indicators
  const isArduino = currentState.arduino === 'Connected';
  const isMqtt = currentState.mqtt === 'Connected';

  const sysDot = document.getElementById('system-pulse-dot');
  const sysText = document.getElementById('system-status-text');
  if (sysDot && sysText) {
    if (isArduino) {
      sysDot.className = 'w-2.5 h-2.5 rounded-full bg-primary-container shadow-[0_0_8px_#00ff66] animate-pulse';
      sysText.textContent = `My Home • Arduino Connected (${currentState.active_port || 'USB'})`;
    } else {
      sysDot.className = 'w-2.5 h-2.5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.5)] animate-pulse';
      sysText.textContent = 'Gateway • Awaiting Arduino USB';
    }
  }

  const mqttDot = document.getElementById('mqtt-status-dot');
  const mqttText = document.getElementById('mqtt-status-text');
  if (mqttDot && mqttText) {
    mqttDot.className = `w-2 h-2 rounded-full ${isMqtt ? 'bg-primary-container' : 'bg-error'}`;
    mqttText.textContent = isMqtt ? 'MQTT Active' : 'MQTT Offline';
  }

  // 3. 4 Hardware Light Relays State
  if (data.light1 !== undefined) currentState.light1 = Number(data.light1);
  if (data.light2 !== undefined) currentState.light2 = Number(data.light2);
  if (data.light3 !== undefined) currentState.light3 = Number(data.light3);
  if (data.light4 !== undefined) currentState.light4 = Number(data.light4);
  if (data.light !== undefined && data.light1 === undefined) currentState.light1 = Number(data.light);
  currentState.light = currentState.light1;

  const lights = [
    Boolean(currentState.light1),
    Boolean(currentState.light2),
    Boolean(currentState.light3),
    Boolean(currentState.light4)
  ];
  const activeCount = lights.filter(Boolean).length;

  const statLights = document.getElementById('stat-active-lights');
  if (statLights) statLights.textContent = `${activeCount}/4`;

  const badgeLights = document.getElementById('badge-lights-count');
  if (badgeLights) badgeLights.textContent = `Lights: ${activeCount}/4 Active`;

  const masterLightsDesc = document.getElementById('master-lights-desc');
  if (masterLightsDesc) {
    masterLightsDesc.textContent = activeCount === 0 
      ? 'All 4 Relay Channels Standby (OFF)' 
      : `${activeCount} of 4 Channels Energized (ON)`;
  }

  // Master switch in Rooms
  const toggleMaster = document.getElementById('toggle-master-light');
  if (toggleMaster && document.activeElement !== toggleMaster) {
    toggleMaster.checked = activeCount === 4;
  }

  // Update 4 individual light cards & toggles across screens
  for (let i = 1; i <= 4; i++) {
    const isLit = Boolean(currentState[`light${i}`]);
    const pinName = i === 1 ? 'D4' : i === 2 ? 'A2' : i === 3 ? 'A3' : 'A4';

    // Home screen toggle & card
    const toggleH = document.getElementById(`toggle-light-${i}`);
    if (toggleH && document.activeElement !== toggleH) toggleH.checked = isLit;

    const iconH = document.getElementById(`icon-light-${i}`);
    if (iconH) {
      iconH.className = `w-9 h-9 rounded-lg flex items-center justify-center transition-all ${
        isLit 
          ? 'bg-primary-container text-surface-container-lowest shadow-[0_0_12px_rgba(0,255,102,0.4)]' 
          : 'bg-surface-variant text-on-surface-variant'
      }`;
    }

    const labelH = document.getElementById(`label-light-${i}`);
    if (labelH) {
      labelH.textContent = `Pin ${pinName} • ${isLit ? 'ON' : 'OFF'}`;
      labelH.className = `text-[10px] font-mono ${isLit ? 'text-primary-container font-bold' : 'text-on-surface-variant'}`;
    }

    // Rooms screen toggle & card
    const toggleR = document.getElementById(`toggle-room-light-${i}`);
    if (toggleR && document.activeElement !== toggleR) toggleR.checked = isLit;

    const iconR = document.getElementById(`icon-room-light-${i}`);
    if (iconR) {
      iconR.className = `w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
        isLit 
          ? 'bg-primary-container text-surface-container-lowest shadow-[0_0_12px_rgba(0,255,102,0.4)]' 
          : 'bg-surface-variant text-on-surface-variant'
      }`;
    }

    const cardLabelR = document.getElementById(`card-light-${i}-label`);
    if (cardLabelR) {
      cardLabelR.textContent = isLit ? `Relay Energized • Pin ${pinName} Active` : `Relay Standby • Pin ${pinName} Open`;
      cardLabelR.className = `text-xs font-mono ${isLit ? 'text-primary-container font-bold' : 'text-primary-fixed-dim'}`;
    }
  }

  // 4. Servo Door / Garage Gate State Synchronization
  updateDoorUI(currentState.door);

  // 7. Ventilation Fan Relay (Pin D12)
  const toggleFanEl = document.getElementById('toggle-fan');
  if (toggleFanEl && document.activeElement !== toggleFanEl) {
    toggleFanEl.checked = Boolean(currentState.fan);
  }
  const cardFanLabel = document.getElementById('card-fan-label');
  if (cardFanLabel) {
    cardFanLabel.textContent = currentState.fan ? 'Exhaust Relay Active (Pin D12)' : 'Exhaust Relay Standby (Pin D12)';
  }

  // 8. Environmental Sensors (Real hardware values)
  const hasData = Boolean(currentState.has_real_data || (currentState.temp !== null && currentState.temp > 0) || currentState.arduino === 'Connected');

  // Gas (MQ-6 Pin A1)
  const gasSafe = (currentState.gas === null || currentState.gas === undefined) ? true : currentState.gas < 400;
  const quickGasStatus = document.getElementById('quick-gas-status');
  const quickGasVal = document.getElementById('quick-gas-val');
  if (quickGasStatus) quickGasStatus.textContent = !hasData ? 'Standby' : (gasSafe ? 'Safe' : 'Leak Alert!');
  if (quickGasVal) quickGasVal.textContent = !hasData ? 'Connecting...' : `${currentState.gas} ADC`;

  // Flame (Pin D5)
  const flameSafe = currentState.flame === null ? true : (currentState.flame === 0);
  const quickFlameStatus = document.getElementById('quick-flame-status');
  const quickFlameDesc = document.getElementById('quick-flame-desc');
  if (quickFlameStatus) quickFlameStatus.textContent = !hasData ? 'Standby' : (flameSafe ? 'Clear' : 'Fire Alert!');
  if (quickFlameDesc) quickFlameDesc.textContent = !hasData ? 'Awaiting Flame Pin D5' : (flameSafe ? 'No fire detected' : 'Flame detected on D5!');

  // Ambient Light LDR (Pin A0)
  const isDay = (currentState.ldr || 0) >= 450;
  const quickLdrVal = document.getElementById('quick-ldr-val');
  const quickLdrStatus = document.getElementById('quick-ldr-status');
  if (quickLdrVal) quickLdrVal.textContent = !hasData ? '--' : `${currentState.ldr}`;
  if (quickLdrStatus) quickLdrStatus.textContent = !hasData ? 'Awaiting LDR A0' : (isDay ? 'Daylight' : 'Night Ambient');

  // Motion PIR (Pin D2) & Obstacle IR (Pin D7)
  const motionActive = currentState.pir === 1 || currentState.ir === 1;
  const quickMotionStatus = document.getElementById('quick-motion-status');
  const quickMotionDesc = document.getElementById('quick-motion-desc');
  if (quickMotionStatus) quickMotionStatus.textContent = !hasData ? 'Standby' : (motionActive ? 'Active' : 'Clear');
  if (quickMotionDesc) quickMotionDesc.textContent = !hasData ? 'Awaiting PIR/IR' : (motionActive ? 'Movement / Obstacle' : 'No movement');

  // Indoor Climate DHT11 (Pin D3)
  const quickClimateVal = document.getElementById('quick-climate-val');
  if (quickClimateVal) {
    if (!hasData || currentState.temp === null || currentState.temp === undefined) {
      quickClimateVal.textContent = 'Awaiting DHT11...';
    } else {
      quickClimateVal.textContent = `${Number(currentState.temp).toFixed(1)}°C • ${Number(currentState.hum || 0).toFixed(0)}%`;
    }
  }

  // 9. Sensors Hub Screen Details
  const hubGas = document.getElementById('hub-gas-reading');
  const badgeGas = document.getElementById('badge-sensor-gas');
  if (hubGas) {
    if (!hasData || currentState.gas === null || currentState.gas === undefined) {
      hubGas.innerHTML = '-- <span class="text-xs font-sans text-primary-fixed-dim">Waiting for Sensor</span>';
    } else {
      const ppm = (currentState.gas * 0.00016).toFixed(3);
      hubGas.innerHTML = `${currentState.gas} <span class="text-xs font-sans text-primary-fixed-dim">ADC (${ppm} PPM)</span>`;
    }
  }
  if (badgeGas) {
    if (!hasData) {
      badgeGas.className = 'px-3 py-1 rounded-full bg-surface-variant text-on-surface-variant text-xs font-bold border border-white/10';
      badgeGas.textContent = 'Waiting';
    } else {
      badgeGas.className = `px-3 py-1 rounded-full ${gasSafe ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-error-container text-error border-error/50'} text-xs font-bold border flex items-center space-x-1`;
      badgeGas.innerHTML = gasSafe ? '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span><span>Normal</span>' : '<span class="w-1.5 h-1.5 rounded-full bg-error animate-ping"></span><span>Hazard Alert</span>';
    }
  }

  const hubFlame = document.getElementById('hub-flame-reading');
  const badgeFlame = document.getElementById('badge-sensor-flame');
  if (hubFlame) {
    if (!hasData || currentState.flame === null || currentState.flame === undefined) {
      hubFlame.innerHTML = 'Awaiting Sensor <span class="text-xs font-sans text-on-surface-variant">(Pin D5)</span>';
    } else {
      hubFlame.innerHTML = flameSafe ? 'No Flame <span class="text-xs font-sans text-emerald-300">Detected</span>' : '🔥 Fire <span class="text-xs font-sans text-error">RADIATION DETECTED</span>';
    }
  }
  if (badgeFlame) {
    if (!hasData) {
      badgeFlame.className = 'px-3 py-1 rounded-full bg-surface-variant text-on-surface-variant text-xs font-bold border border-white/10';
      badgeFlame.textContent = 'Waiting';
    } else {
      badgeFlame.className = `px-3 py-1 rounded-full ${flameSafe ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' : 'bg-error-container text-error border-error/50'} text-xs font-bold border flex items-center space-x-1`;
      badgeFlame.innerHTML = flameSafe ? '<span class="w-1.5 h-1.5 rounded-full bg-emerald-400"></span><span>Safe</span>' : '<span class="w-1.5 h-1.5 rounded-full bg-error animate-ping"></span><span>FIRE ALERT</span>';
    }
  }

  const hubTemp = document.getElementById('hub-temp-reading');
  if (hubTemp) {
    hubTemp.textContent = (!hasData || currentState.temp === null || currentState.temp === undefined) ? '--°C' : `${Number(currentState.temp).toFixed(1)}°C`;
  }

  const hubHum = document.getElementById('hub-hum-reading');
  if (hubHum) {
    hubHum.textContent = (!hasData || currentState.hum === null || currentState.hum === undefined) ? '--%' : `${Number(currentState.hum).toFixed(1)}%`;
  }

  const hubLdr = document.getElementById('hub-ldr-reading');
  const badgeLdr = document.getElementById('badge-sensor-ldr');
  if (hubLdr) {
    if (!hasData || currentState.ldr === null || currentState.ldr === undefined) {
      hubLdr.innerHTML = '-- <span class="text-xs font-sans text-primary-fixed-dim">Waiting for Sensor</span>';
    } else {
      const lux = Math.round(currentState.ldr * 0.52);
      hubLdr.innerHTML = `${currentState.ldr} <span class="text-xs font-sans text-primary-fixed-dim">ADC (${lux} Lux)</span>`;
    }
  }
  if (badgeLdr) {
    badgeLdr.textContent = !hasData ? 'Standby' : (isDay ? 'Daylight' : 'Night Ambient');
  }

  const hubPir = document.getElementById('hub-pir-reading');
  const badgePir = document.getElementById('badge-sensor-pir');
  if (hubPir) hubPir.textContent = !hasData ? 'Standby' : (currentState.pir === 1 ? 'Presence Detected' : 'No Motion');
  if (badgePir) {
    badgePir.className = `px-2 py-0.5 rounded-full ${currentState.pir === 1 ? 'bg-primary-container text-on-primary font-bold shadow-[0_0_8px_#00ff66]' : 'bg-surface-variant text-on-surface-variant'} text-xs`;
    badgePir.textContent = currentState.pir === 1 ? 'Movement' : 'Clear';
  }

  const hubIr = document.getElementById('hub-ir-reading');
  const badgeIr = document.getElementById('badge-sensor-ir');
  if (hubIr) hubIr.textContent = !hasData ? 'Standby' : (currentState.ir === 1 ? 'Obstacle Detected' : 'Clear');
  if (badgeIr) {
    badgeIr.className = `px-2 py-0.5 rounded-full ${currentState.ir === 1 ? 'bg-primary-container text-on-primary font-bold shadow-[0_0_8px_#00ff66]' : 'bg-surface-variant text-on-surface-variant'} text-xs`;
    badgeIr.textContent = currentState.ir === 1 ? 'Tripped' : 'Clear';
  }

  // Ultrasonic Proximity Progress Bar (HC-SR04 Pins D8/D9)
  const hubDistVal = document.getElementById('hub-dist-val');
  const barUltrasonic = document.getElementById('bar-ultrasonic');
  const labelDistStatus = document.getElementById('label-dist-status');
  if (hubDistVal) hubDistVal.textContent = (!hasData || currentState.dist === null || currentState.dist === undefined) ? '-- cm' : `${currentState.dist} cm`;
  if (barUltrasonic && hasData && currentState.dist !== null && currentState.dist !== undefined) {
    const pct = Math.max(2, Math.min(100, (currentState.dist / 200) * 100));
    barUltrasonic.style.width = `${pct}%`;
    if (currentState.dist < 20) {
      barUltrasonic.className = 'bg-error h-full transition-all duration-300 rounded-full shadow-[0_0_10px_#ffb4ab]';
      if (labelDistStatus) labelDistStatus.textContent = 'Proximity Alert (<20cm)';
    } else {
      barUltrasonic.className = 'bg-primary-container h-full transition-all duration-300 rounded-full shadow-[0_0_8px_#00ff66]';
      if (labelDistStatus) labelDistStatus.textContent = 'Safe Proximity';
    }
  }

  // 10. Update Trend Sparklines with real data
  updateSparklines(currentState);

  // 11. Emergency Banner & Alarm Siren Handling
  const emergencyBanner = document.getElementById('emergency-banner');
  const emergencyDesc = document.getElementById('emergency-desc');
  const homeStatusTitle = document.getElementById('home-status-title');
  const badgeSystemHealth = document.getElementById('badge-system-health');

  if (hasData && (!gasSafe || !flameSafe)) {
    if (emergencyBanner) emergencyBanner.classList.remove('hidden');
    if (emergencyDesc) {
      emergencyDesc.textContent = !flameSafe
        ? 'Fire Radiation Detected on Pin D5! Siren and strobe active.'
        : `Combustible Gas Detected (${currentState.gas} ADC)! Fan active.`;
    }
    if (homeStatusTitle) homeStatusTitle.textContent = 'Hazard Alert Active';
    if (badgeSystemHealth) {
      badgeSystemHealth.className = 'px-3 py-1 rounded-full bg-error-container text-error text-xs font-bold border border-error/50 shadow-[0_0_12px_rgba(255,180,171,0.3)] animate-pulse';
      badgeSystemHealth.textContent = 'Emergency';
    }
    startAlarmSiren();
  } else {
    if (emergencyBanner) emergencyBanner.classList.add('hidden');
    if (homeStatusTitle) homeStatusTitle.textContent = 'Home Status';
    if (badgeSystemHealth) {
      badgeSystemHealth.className = 'px-3 py-1 rounded-full bg-primary-container/20 text-primary-container text-xs font-bold border border-primary-container/30 shadow-[0_0_10px_rgba(0,255,102,0.2)]';
      badgeSystemHealth.textContent = isArduino ? 'Optimal' : 'Standby';
    }
    stopAlarmSiren();
  }
}

// -----------------------------------------------------------------------------
// Interactive Hardware Action Handlers
// -----------------------------------------------------------------------------
function handleLightToggle(arg1, arg2) {
  let id = 1;
  let isOn = false;
  if (typeof arg2 === 'boolean') {
    id = Number(arg1);
    isOn = arg2;
  } else {
    isOn = Boolean(arg1);
    id = 1;
  }

  currentState[`light${id}`] = isOn ? 1 : 0;
  if (id === 1) currentState.light = isOn ? 1 : 0;

  playTone(isOn ? 880 : 440, 0.12, 'sine');
  postAPI(`/api/light/${id}/${isOn ? 'on' : 'off'}`);

  const names = {
    1: 'Living Room Light (Pin D4)',
    2: 'Bedroom Light (Pin A2)',
    3: 'Kitchen Light (Pin A3)',
    4: 'Balcony Light (Pin A4)'
  };
  showNotification(
    `${names[id] || `Light ${id}`} turned ${isOn ? 'ON' : 'OFF'}`,
    'success',
    'lightbulb',
    'Lighting Relay'
  );
  updateUI(currentState);
}

function handleMasterLightToggle(isOn) {
  currentState.light1 = isOn ? 1 : 0;
  currentState.light2 = isOn ? 1 : 0;
  currentState.light3 = isOn ? 1 : 0;
  currentState.light4 = isOn ? 1 : 0;
  currentState.light = isOn ? 1 : 0;

  playTone(isOn ? 950 : 400, 0.15, 'sine');
  postAPI(`/api/lights/all/${isOn ? 'on' : 'off'}`);
  showNotification(
    isOn ? 'All 4 Lights turned ON' : 'All 4 Lights turned OFF',
    'success',
    'lightbulb',
    'Master Lighting'
  );
  updateUI(currentState);
}

function openDoor() {
  currentState.door = 90;
  playTone(700, 0.15, 'triangle');
  postAPI('/api/door/open');
  showNotification('Opening Garage Gate (90°)', 'success', 'lock_open', 'Servo Gate (Pin D10)');
  updateDoorUI(90);
}

function closeDoor() {
  currentState.door = 0;
  playTone(450, 0.15, 'triangle');
  postAPI('/api/door/close');
  showNotification('Closing Garage Gate (0°)', 'info', 'lock', 'Servo Gate (Pin D10)');
  updateDoorUI(0);
}

function toggleDoor() {
  if (currentState.door >= 45) {
    closeDoor();
  } else {
    openDoor();
  }
}

function handleDoorSlider(angle) {
  const val = Number(angle);
  currentState.door = val;
  updateDoorUI(val);
  postAPI('/api/door/set', { angle: val });
}

function updateDoorUI(angle) {
  const val = Number(angle);
  const isUnlocked = val >= 45;

  const statDoor = document.getElementById('stat-door-angle');
  if (statDoor) statDoor.textContent = `${isUnlocked ? 'Open' : 'Closed'} (${val}°)`;

  const labelDoor = document.getElementById('label-door-status');
  if (labelDoor) labelDoor.textContent = `Pin D10 Servo • ${val}° (${isUnlocked ? 'Open' : 'Closed'})`;

  const badgeGate = document.getElementById('badge-gate-status');
  if (badgeGate) {
    badgeGate.textContent = isUnlocked ? 'OPEN (90°)' : 'CLOSED (0°)';
    badgeGate.className = isUnlocked 
      ? 'px-2.5 py-1 rounded-full bg-primary-container text-surface-container-lowest text-xs font-mono font-bold shadow-[0_0_10px_#00ff66]' 
      : 'px-2.5 py-1 rounded-full bg-surface-variant text-xs font-mono text-on-surface';
  }

  const cardServo = document.getElementById('card-servo-label');
  if (cardServo) cardServo.textContent = `PWM Deadbolt • ${val}° (${isUnlocked ? 'Open' : 'Closed'})`;

  const sliderHome = document.getElementById('slider-door');
  if (sliderHome && document.activeElement !== sliderHome) sliderHome.value = val;

  const sliderActuator = document.getElementById('slider-door-actuator');
  if (sliderActuator && document.activeElement !== sliderActuator) sliderActuator.value = val;

  const valDoor = document.getElementById('val-door-angle');
  if (valDoor) valDoor.textContent = `${val}°`;

  const valDoorActuator = document.getElementById('val-door-angle-actuator');
  if (valDoorActuator) valDoorActuator.textContent = `${val}°`;

  // Highlight active button states on Home screen
  const btnCloseH = document.getElementById('btn-gate-close-home');
  const btnOpenH = document.getElementById('btn-gate-open-home');
  if (btnCloseH && btnOpenH) {
    if (isUnlocked) {
      btnOpenH.className = 'py-3.5 px-4 rounded-xl bg-primary-container text-surface-container-lowest font-black text-sm flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,255,102,0.4)] active:scale-95 transition-all';
      btnCloseH.className = 'py-3.5 px-4 rounded-xl bg-surface-variant/80 hover:bg-surface-variant active:scale-95 text-on-surface font-bold text-sm flex items-center justify-center gap-2 border border-white/10 transition-all';
    } else {
      btnCloseH.className = 'py-3.5 px-4 rounded-xl bg-surface-container-highest text-primary-container font-black text-sm flex items-center justify-center gap-2 border border-primary-container/40 shadow-[0_0_12px_rgba(0,255,102,0.2)] active:scale-95 transition-all';
      btnOpenH.className = 'py-3.5 px-4 rounded-xl bg-surface-variant/80 hover:bg-surface-variant active:scale-95 text-on-surface font-bold text-sm flex items-center justify-center gap-2 border border-white/10 transition-all';
    }
  }

  // Highlight active button states in Rooms screen
  const btnCloseR = document.getElementById('btn-gate-close-room');
  const btnOpenR = document.getElementById('btn-gate-open-room');
  if (btnCloseR && btnOpenR) {
    if (isUnlocked) {
      btnOpenR.className = 'py-3 px-4 rounded-xl bg-primary-container text-surface-container-lowest font-black text-sm flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,255,102,0.4)] active:scale-95 transition-all';
      btnCloseR.className = 'py-3 px-4 rounded-xl bg-surface-variant/80 hover:bg-surface-variant active:scale-95 text-on-surface font-bold text-sm flex items-center justify-center gap-2 border border-white/10 transition-all';
    } else {
      btnCloseR.className = 'py-3 px-4 rounded-xl bg-surface-container-highest text-primary-container font-black text-sm flex items-center justify-center gap-2 border border-primary-container/40 shadow-[0_0_12px_rgba(0,255,102,0.2)] active:scale-95 transition-all';
      btnOpenR.className = 'py-3 px-4 rounded-xl bg-surface-variant/80 hover:bg-surface-variant active:scale-95 text-on-surface font-bold text-sm flex items-center justify-center gap-2 border border-white/10 transition-all';
    }
  }
}

function toggleFan() {
  playTone(550, 0.12, 'square');
  postAPI('/api/fan/toggle');
  showNotification('Ventilation Fan state toggled', 'success', 'mode_fan', 'Fan Relay (Pin D12)');
}

function toggleSystemMode() {
  const nextMode = currentState.mode === 'AUTO' ? 'manual' : 'auto';
  playTone(700, 0.12, 'sine');
  postAPI(`/api/mode/${nextMode}`);
  showNotification(
    `System switched to ${nextMode.toUpperCase()} mode`,
    'info',
    'settings_suggest',
    'Automation Mode'
  );
}

function applyScene(name) {
  playTone(800, 0.15, 'sine');
  if (name === 'away') {
    postAPI('/api/lights/all/off');
    postAPI('/api/door/close');
    postAPI('/api/fan/off');
    showNotification('Scene: All Hardware Off & Gate Locked', 'info', 'lock', 'Scene Preset');
  } else if (name === 'home') {
    postAPI('/api/mode/auto');
    postAPI('/api/lights/all/on');
    showNotification('Scene: Auto Ambient Mode Active', 'success', 'wb_sunny', 'Scene Preset');
  } else if (name === 'night') {
    postAPI('/api/door/close');
    postAPI('/api/lights/all/off');
    postAPI('/api/mode/auto');
    showNotification('Scene: Night Guard Armed (Auto Sensing)', 'info', 'bedtime', 'Scene Preset');
  } else if (name === 'party') {
    postAPI('/api/lights/all/on');
    postAPI('/api/door/open');
    postAPI('/api/fan/on');
    showNotification('Scene: Welcome Mode (Gate Open & Fan ON)', 'success', 'celebration', 'Scene Preset');
  }
}

function silenceAlarm() {
  stopAlarmSiren();
  postAPI('/api/alarm/silence');
  showNotification('Hazard Siren Muted', 'info', 'volume_off', 'Security Alarm');
}

// -----------------------------------------------------------------------------
// Connection Modal & Latency Testing (Cyber Green Theme, IP Only)
// -----------------------------------------------------------------------------
function openConnectModal() {
  const modal = document.getElementById('modal-connect');
  if (modal) modal.classList.remove('hidden');

  const ipInput = document.getElementById('modal-ip-address');
  if (ipInput) ipInput.value = localStorage.getItem('gateway_ip') || window.location.hostname || '127.0.0.1';
}

function closeConnectModal() {
  const modal = document.getElementById('modal-connect');
  if (modal) modal.classList.add('hidden');
}

function setPresetIp(ip) {
  const ipInput = document.getElementById('modal-ip-address');
  if (ipInput) ipInput.value = ip;
}

function detectLanIp() {
  const host = window.location.hostname || '127.0.0.1';
  setPresetIp(host);
  showNotification(`Detected Host: ${host}`, 'info', 'wifi', 'Host Discovery');
}

function handleModalConnect() {
  const ipInput = document.getElementById('modal-ip-address');
  const cleanIp = (ipInput?.value || '127.0.0.1').trim().replace(/^https?:\/\//, '').replace(/:.*$/, '');
  const cleanPort = '5000';

  localStorage.setItem('gateway_ip', cleanIp);
  localStorage.setItem('gateway_port', cleanPort);

  const headerIp = document.getElementById('header-ip-badge');
  if (headerIp) headerIp.textContent = `${cleanIp}:${cleanPort}`;

  closeConnectModal();
  showNotification(`Connecting to http://${cleanIp}:${cleanPort}...`, 'info', 'router', 'Gateway Link');

  // Re-initialize telemetry connection
  initTelemetryStream();
}

async function testConnection() {
  const resLbl = document.getElementById('test-conn-result');
  if (resLbl) {
    resLbl.textContent = 'Testing ping...';
    resLbl.className = 'text-xs font-mono text-tertiary';
  }

  const start = performance.now();
  try {
    const res = await fetch('/api/status', { cache: 'no-store' });
    const latency = Math.round(performance.now() - start);
    if (res.ok) {
      if (resLbl) {
        resLbl.textContent = `Connected (${latency}ms)`;
        resLbl.className = 'text-xs font-mono text-primary-container';
      }
      playTone(1000, 0.1, 'sine');
      showNotification(`Gateway reachable: ${latency}ms latency`);
    } else {
      throw new Error(`HTTP ${res.status}`);
    }
  } catch (err) {
    if (resLbl) {
      resLbl.textContent = 'Connection Failed';
      resLbl.className = 'text-xs font-mono text-error';
    }
    showNotification('Unable to reach Arduino Gateway');
  }
}

// -----------------------------------------------------------------------------
// Appearance Preference Toggles
// -----------------------------------------------------------------------------
function toggleBlurEffect(enabled) {
  document.querySelectorAll('.glass-card, header, nav > div').forEach(el => {
    el.style.backdropFilter = enabled ? 'blur(28px)' : 'none';
    el.style.webkitBackdropFilter = enabled ? 'blur(28px)' : 'none';
  });
  showNotification(`Blur effect ${enabled ? 'enabled' : 'disabled'}`);
}

function toggleGlowEffect(enabled) {
  document.querySelectorAll('body > div.fixed').forEach(el => {
    el.style.display = enabled ? 'block' : 'none';
  });
  showNotification(`Ambient glow ${enabled ? 'enabled' : 'disabled'}`);
}

function toggleAudioAlerts(enabled) {
  audioAlertsEnabled = enabled;
  if (!enabled) stopAlarmSiren();
  showNotification(`Audio alerts ${enabled ? 'enabled' : 'disabled'}`);
}

// -----------------------------------------------------------------------------
// Liquid Crystal Glass Attractive Toast Popup
// -----------------------------------------------------------------------------
let toastTimer = null;

function showNotification(msg, type = 'info', icon = null, title = null) {
  const toast = document.getElementById('toast-notification');
  const msgEl = document.getElementById('toast-message');
  const titleEl = document.getElementById('toast-title');
  const timeEl = document.getElementById('toast-time');
  const iconEl = document.getElementById('toast-icon');
  const iconBox = document.getElementById('toast-icon-box');

  if (!toast || !msgEl) return;

  // Infer type and icon if not specified
  const lowerMsg = String(msg).toLowerCase();
  if (!icon || type === 'info') {
    if (lowerMsg.includes('alert') || lowerMsg.includes('hazard') || lowerMsg.includes('fire') || lowerMsg.includes('leak') || lowerMsg.includes('failed') || lowerMsg.includes('error')) {
      type = 'error';
      icon = icon || 'warning';
      title = title || 'Security Alert';
    } else if (lowerMsg.includes('on') || lowerMsg.includes('optimal') || lowerMsg.includes('connected') || lowerMsg.includes('safe') || lowerMsg.includes('clear')) {
      type = 'success';
      icon = icon || 'check_circle';
      title = title || 'Hardware Action';
    } else if (lowerMsg.includes('door') || lowerMsg.includes('gate') || lowerMsg.includes('lock')) {
      type = 'success';
      icon = icon || 'garage_home';
      title = title || 'Servo Gate';
    } else if (lowerMsg.includes('fan') || lowerMsg.includes('vent')) {
      type = 'success';
      icon = icon || 'mode_fan';
      title = title || 'Ventilation Fan';
    } else if (lowerMsg.includes('light')) {
      type = 'success';
      icon = icon || 'lightbulb';
      title = title || 'Lighting Relay';
    } else if (lowerMsg.includes('scene')) {
      type = 'success';
      icon = icon || 'auto_awesome';
      title = title || 'Scene Preset';
    } else {
      type = type || 'info';
      icon = icon || 'info';
      title = title || 'System Update';
    }
  }

  // Update text elements without destroying inner markup
  msgEl.textContent = msg;
  if (titleEl) titleEl.textContent = title || 'System Update';
  if (timeEl) {
    const now = new Date();
    timeEl.textContent = now.toTimeString().split(' ')[0];
  }
  if (iconEl) iconEl.textContent = icon || 'notifications';

  // Apply liquid-crystal color palette and glowing aura
  if (iconBox) {
    if (type === 'error') {
      iconBox.className = 'w-10 h-10 rounded-xl bg-error/20 text-error border border-error/40 flex items-center justify-center shrink-0 shadow-[0_0_18px_rgba(255,180,171,0.4)] transition-all';
      if (titleEl) titleEl.className = 'text-[10px] font-mono uppercase tracking-wider font-bold text-error';
      toast.className = 'pointer-events-auto cursor-pointer transform transition-all duration-300 ease-out translate-y-0 opacity-100 scale-100 w-full rounded-2xl glass-card p-3.5 flex items-center space-x-3.5 shadow-2xl border border-error/60 bg-surface/95 backdrop-blur-3xl';
    } else if (type === 'warning') {
      iconBox.className = 'w-10 h-10 rounded-xl bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center justify-center shrink-0 shadow-[0_0_18px_rgba(245,158,11,0.3)] transition-all';
      if (titleEl) titleEl.className = 'text-[10px] font-mono uppercase tracking-wider font-bold text-amber-300';
      toast.className = 'pointer-events-auto cursor-pointer transform transition-all duration-300 ease-out translate-y-0 opacity-100 scale-100 w-full rounded-2xl glass-card p-3.5 flex items-center space-x-3.5 shadow-2xl border border-amber-500/60 bg-surface/95 backdrop-blur-3xl';
    } else {
      iconBox.className = 'w-10 h-10 rounded-xl bg-primary-container/20 text-primary-container border border-primary-container/40 flex items-center justify-center shrink-0 shadow-[0_0_18px_rgba(0,255,102,0.3)] transition-all';
      if (titleEl) titleEl.className = 'text-[10px] font-mono uppercase tracking-wider font-bold text-primary-fixed-dim';
      toast.className = 'pointer-events-auto cursor-pointer transform transition-all duration-300 ease-out translate-y-0 opacity-100 scale-100 w-full rounded-2xl glass-card p-3.5 flex items-center space-x-3.5 shadow-2xl border border-primary-container/40 bg-surface/95 backdrop-blur-3xl hover:border-primary-container/70';
    }
  }

  // Smooth slide-in transition
  toast.classList.remove('hidden');
  void toast.offsetWidth; // Force DOM reflow
  toast.classList.remove('-translate-y-12', 'opacity-0', 'scale-95');
  toast.classList.add('translate-y-0', 'opacity-100', 'scale-100');

  // Auto-dismiss after 3.2 seconds
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    dismissNotification();
  }, 3200);
}

function dismissNotification() {
  const toast = document.getElementById('toast-notification');
  if (!toast) return;

  clearTimeout(toastTimer);
  toast.classList.remove('translate-y-0', 'opacity-100', 'scale-100');
  toast.classList.add('-translate-y-12', 'opacity-0', 'scale-95');

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 300);
}

// -----------------------------------------------------------------------------
// Live Telemetry Stream (SSE with Fast Polling Fallback)
// -----------------------------------------------------------------------------
let sseSource = null;
let pollingInterval = null;

function initTelemetryStream() {
  if (sseSource) {
    sseSource.close();
    sseSource = null;
  }
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }

  // Attempt Server-Sent Events
  if (window.EventSource) {
    try {
      sseSource = new EventSource('/api/stream');

      sseSource.onmessage = function (e) {
        try {
          const data = JSON.parse(e.data);
          updateUI(data);
        } catch (err) {
          console.error('SSE parse error:', err);
        }
      };

      sseSource.onerror = function () {
        console.warn('SSE disconnected. Falling back to HTTP polling.');
        if (sseSource) {
          sseSource.close();
          sseSource = null;
        }
        startHttpPolling();
      };
      return;
    } catch (err) {
      console.warn('EventSource failed, using polling.');
    }
  }

  startHttpPolling();
}

function startHttpPolling() {
  if (pollingInterval) return;
  pollingInterval = setInterval(async () => {
    try {
      const res = await fetch('/api/status', { cache: 'no-store' });
      if (res.ok) {
        const data = await res.json();
        updateUI(data);
      }
    } catch (e) {
      // Offline
    }
  }, 1000);
}

// -----------------------------------------------------------------------------
// Lifecycle Initialization
// -----------------------------------------------------------------------------
window.addEventListener('DOMContentLoaded', () => {
  // Restore saved active tab or default to 'home'
  const savedTab = localStorage.getItem('smarthome_active_tab') || 'home';
  showScreen(savedTab);

  // Restore saved gateway IP
  const savedIp = localStorage.getItem('gateway_ip') || window.location.hostname || '127.0.0.1';
  const savedPort = localStorage.getItem('gateway_port') || window.location.port || '5000';
  const headerIp = document.getElementById('header-ip-badge');
  if (headerIp) headerIp.textContent = `${savedIp}:${savedPort}`;

  // Start real-time telemetry stream
  initTelemetryStream();

  // Register Web Audio on first user interaction
  document.body.addEventListener('click', () => {
    initAudio();
  }, { once: true });

  // Register Service Worker for PWA
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js').catch(() => {});
  }
});
