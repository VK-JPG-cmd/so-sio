/**
 * main.js
 * Master Animation Controller & Studio Interface for So-cio.
 * Drives both DOM/SVG-filtered elements and Canvas synchronization.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const stage = document.getElementById('cinemaStage');
  const screenContainer = document.getElementById('screenContainer');
  const effectsCanvas = document.getElementById('effectsCanvas');
  const viewportBgCanvas = document.getElementById('viewportBgCanvas');
  const viewportBgCtx = viewportBgCanvas ? viewportBgCanvas.getContext('2d') : null;
  const logoWrapper = document.getElementById('logoWrapper');
  const brandText = document.getElementById('brandText');
  const partSo = document.getElementById('partSo');
  const partHyphen = document.getElementById('partHyphen');
  const partCio = document.getElementById('partCio');
  const lightBloom = document.getElementById('lightBloom');
  const horizontalFlare = document.getElementById('horizontalFlare');
  const verticalStreak = document.getElementById('verticalStreak');
  const impactHalo = document.getElementById('impactHalo');
  const shockwaveRing = document.getElementById('shockwaveRing');

  // Handshake + chrome logo elements
  const handshakeCanvas = document.getElementById('handshakeCanvas');
  const handshakeCtx = handshakeCanvas ? handshakeCanvas.getContext('2d') : null;
  const chromeLogoOverlay = document.getElementById('chromeLogoOverlay');

  // SVG Blur Kernels
  const blurKernelLeft = document.getElementById('blurKernelLeft');
  const blurKernelRight = document.getElementById('blurKernelRight');

  // UI Controls
  const studioHeader = document.getElementById('studioHeader');
  const btnPlayPause = document.getElementById('btnPlayPause');
  const btnReplay = document.getElementById('btnReplay');
  const btnSoundToggle = document.getElementById('btnSoundToggle');
  const btnSettingsToggle = document.getElementById('btnSettingsToggle');
  const btnCloseDrawer = document.getElementById('btnCloseDrawer');
  const settingsDrawer = document.getElementById('settingsDrawer');
  const btnExportVideo = document.getElementById('btnExportVideo');
  const btnFullscreen = document.getElementById('btnFullscreen');
  const btnCaptureFrame = document.getElementById('btnCaptureFrame');
  const timelineScrubber = document.getElementById('timelineScrubber');
  const scrubberFill = document.getElementById('scrubberFill');
  const timecodeDisplay = document.getElementById('timecodeDisplay');
  const toastNotification = document.getElementById('toastNotification');

  // Export Modal Elements
  const exportModalBackdrop = document.getElementById('exportModalBackdrop');
  const exportProgressFill = document.getElementById('exportProgressFill');
  const exportStatusLabel = document.getElementById('exportStatusLabel');
  const btnCancelExport = document.getElementById('btnCancelExport');

  // Customization Inputs
  const flareIntensitySlider = document.getElementById('flareIntensitySlider');
  const motionBlurSlider = document.getElementById('motionBlurSlider');
  const fontSizeSlider = document.getElementById('fontSizeSlider');
  const fontSizeValue = document.getElementById('fontSizeValue');

  // Animation State Variables (Cinematic 6-Scene Sequence: 8.8s total)
  const DURATION         = 8.8;  // Total duration: 8.8 seconds
  const OPENING_END      = 0.5;  // Scene 1: Dark opening (0.0s - 0.5s)
  const MEET_TIME        = 2.2;  // Scene 2 & 3: Light trails + "So" & "cio" meet at 2.2s
  const HANDSHAKE_START  = 2.2;  // Scene 4: Light hands emerge & reach
  const CLASP_TIME       = 2.95; // Scene 4: Handshake clasp impact + pulse
  const DISSOLVE_START   = 3.8;  // Scene 5: Hands & text dissolve into swirling particles
  const ASSEMBLE_START   = 4.4;  // Scene 5: Swirling particles assemble into logo
  const LOGO_REVEAL_TIME = 5.3;  // Scene 5: Solidification into chrome S logo
  const REVEAL_HOLD_END  = 8.8;  // Scene 6: Final chrome logo held for 3.5s

  let currentTime = 0;
  let isPlaying = false;
  let playbackSpeed = 1.0;
  let lastFrameTimestamp = null;
  let hasTriggeredSoundThisCycle = false;
  let maxMotionBlur = 24;
  let flareIntensity = 1.0;
  let currentFont = 'Transcity';

  // Initialize Canvas 2D Handshake & Particle Swirl Engine
  const handshakeEngine = (typeof window !== 'undefined' && window.CinematicHandshakeEngine && handshakeCanvas)
    ? new window.CinematicHandshakeEngine(handshakeCanvas)
    : null;

  // Pre-load and register custom Transcity typeface into document.fonts
  try {
    const transcityFace = new FontFace('Transcity', 'url(fonts/Transcity.otf)');
    transcityFace.load().then(loadedFace => {
      document.fonts.add(loadedFace);
      applyTimelineState(currentTime);
    }).catch(e => console.warn('Transcity FontFace load fallback to CSS:', e));
  } catch (err) {
    console.warn(err);
  }

  // Mouse idle UI auto-hide
  let mouseIdleTimeout = null;

  // Current Background Atmosphere Mode: 'lightspeed' (default), 'fusion', or 'silk'
  let currentBgMode = 'lightspeed';

  // Initialize Lightspeed Hyperspace Engine (React Bits Pro)
  const lightspeedEngine = (typeof window !== 'undefined' && window.LightspeedEngine)
    ? new window.LightspeedEngine({
        streakCount: 128,
        speed: 1.15,
        stretchFactor: 0.052,
        intensity: 1.25,
        fadePower: 1.85
      })
    : null;

  // Initialize Luxury Background Engine (Silk Caustics & Constellations)
  const bgEngine = (typeof window !== 'undefined' && window.LuxuryBackgroundEngine)
    ? new window.LuxuryBackgroundEngine({
        particleCount: 52,
        sparkCount: 36,
        enableCursorAura: true,
        enableShafts: true
      })
    : null;

  let mouseNormX = 0.5;
  let mouseNormY = 0.5;

  window.addEventListener('mousemove', (e) => {
    mouseNormX = e.clientX / window.innerWidth;
    mouseNormY = e.clientY / window.innerHeight;
  }, { passive: true });

  /**
   * Render real-time generative luxury background
   */
  function renderLiveBackground(t, timestamp) {
    if (!viewportBgCanvas || !viewportBgCtx) return;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth;
    const h = window.innerHeight;

    if (viewportBgCanvas.width !== Math.round(w * dpr) || viewportBgCanvas.height !== Math.round(h * dpr)) {
      viewportBgCanvas.width = Math.round(w * dpr);
      viewportBgCanvas.height = Math.round(h * dpr);
    }

    const wallClockSec = timestamp ? timestamp / 1000 : performance.now() / 1000;

    viewportBgCtx.save();
    viewportBgCtx.scale(dpr, dpr);

    // Netflix Intro Blackout:
    // Plunge cosmic background into absolute pure black as the chrome S logo solidifies
    if (t >= 5.2) {
      viewportBgCtx.fillStyle = '#000000';
      viewportBgCtx.fillRect(0, 0, w, h);
      viewportBgCtx.restore();
      return;
    }

    let bgFade = 1.0;
    if (t >= 4.7) {
      bgFade = Math.max(0, 1.0 - (t - 4.7) / 0.5);
      viewportBgCtx.globalAlpha = bgFade;
    }

    if (currentBgMode === 'lightspeed') {
      if (lightspeedEngine) {
        lightspeedEngine.renderAt(viewportBgCtx, w, h, t, mouseNormX, mouseNormY, wallClockSec);
      }
    } else if (currentBgMode === 'silk') {
      if (bgEngine) {
        bgEngine.renderAt(viewportBgCtx, w, h, t, mouseNormX, mouseNormY, wallClockSec);
      }
    } else if (currentBgMode === 'fusion') {
      if (lightspeedEngine) {
        lightspeedEngine.renderAt(viewportBgCtx, w, h, t, mouseNormX, mouseNormY, wallClockSec);
      }
      if (bgEngine) {
        viewportBgCtx.globalCompositeOperation = 'screen';
        bgEngine.renderAt(viewportBgCtx, w, h, t, mouseNormX, mouseNormY, wallClockSec);
        viewportBgCtx.globalCompositeOperation = 'source-over';
      }
    }

    if (bgFade < 1.0) {
      viewportBgCtx.fillStyle = `rgba(0, 0, 0, ${(1.0 - bgFade).toFixed(3)})`;
      viewportBgCtx.fillRect(0, 0, w, h);
    }

    viewportBgCtx.restore();
  }

  // Initialize Canvas & Video Recorder
  const recorder = new window.LogoVideoRecorder(effectsCanvas, {
    duration: DURATION,
    fps: 60,
    fontFamily: currentFont,
    motionBlurStrength: maxMotionBlur,
    flareIntensity: flareIntensity,
    bgMode: currentBgMode
  });

  // Quintic Ease-Out curve for authentic deceleration
  function easeOutQuint(x) {
    return 1 - Math.pow(1 - x, 5);
  }

  function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
  }

  /**
   * Apply animation state at time `t` (seconds) to the DOM elements and Canvas 2D
   */
  function applyTimelineState(t) {
    const w = handshakeCanvas ? handshakeCanvas.width : 1920;
    const h = handshakeCanvas ? handshakeCanvas.height : 1080;
    const cx = w / 2;
    const cy = h / 2;

    // 0. Render Canvas 2D Handshake / Light Trails / Particle Swirl Engine
    if (handshakeEngine) {
      if (handshakeCanvas) handshakeCanvas.style.opacity = '1';
      handshakeEngine.render(t, cx, cy, 1.0);
    }

    // 1. SCENE 1: Dark opening (0.0s <= t < 0.5s)
    // Deep black #111312 background with subtle charcoal-grey #434346 atmospheric swell
    if (t < OPENING_END) {
      const initOffset = 70;
      partSo.style.transform = `translateX(-${initOffset}vw)`;
      partSo.style.opacity = '0';
      partSo.style.filter = 'url(#motionBlurLeft)';
      blurKernelLeft.setAttribute('stdDeviation', '0, 0');

      partCio.style.transform = `translateX(${initOffset}vw)`;
      partCio.style.opacity = '0';
      partCio.style.filter = 'url(#motionBlurRight)';
      blurKernelRight.setAttribute('stdDeviation', '0, 0');

      partHyphen.style.opacity = '0';
      partHyphen.style.transform = 'scale(0)';

      horizontalFlare.style.opacity = '0';
      horizontalFlare.style.transform = 'scaleX(0)';
      impactHalo.style.opacity = '0';
      verticalStreak.style.opacity = '0';
      shockwaveRing.style.opacity = '0';
      lightBloom.style.opacity = `${(t / OPENING_END) * 0.08}`; // subtle charcoal/light breathing

      logoWrapper.style.opacity = '1';
      logoWrapper.style.filter = 'none';
      logoWrapper.style.transform = 'scale(1)';

      if (chromeLogoOverlay) {
        chromeLogoOverlay.style.opacity = '0';
      }
      return;
    }

    // 2. SCENE 2 & 3: "So" enters from left, "cio" from right with light trails (0.5s <= t < 2.2s)
    if (t >= OPENING_END && t < MEET_TIME) {
      const flightProg = (t - OPENING_END) / (MEET_TIME - OPENING_END);
      const ease = easeOutQuint(flightProg);
      const remainingDist = 1 - ease;

      const offsetVW = remainingDist * 65; // 65vw to 0vw
      partSo.style.transform = `translateX(-${offsetVW}vw)`;
      partCio.style.transform = `translateX(${offsetVW}vw)`;

      // Alpha ramp
      const inAlpha = Math.min(1, flightProg * 3.5);
      partSo.style.opacity = inAlpha;
      partCio.style.opacity = inAlpha;

      // Motion blur using SVG feGaussianBlur
      const currentBlur = remainingDist * maxMotionBlur;
      partSo.style.filter = currentBlur > 0.5 ? 'url(#motionBlurLeft)' : 'none';
      partCio.style.filter = currentBlur > 0.5 ? 'url(#motionBlurRight)' : 'none';
      blurKernelLeft.setAttribute('stdDeviation', `${currentBlur.toFixed(1)}, 0`);
      blurKernelRight.setAttribute('stdDeviation', `${currentBlur.toFixed(1)}, 0`);

      // Hyphen waiting
      partHyphen.style.opacity = '0';
      partHyphen.style.transform = 'scale(0)';

      // Flares idle
      horizontalFlare.style.opacity = '0';
      impactHalo.style.opacity = '0';
      verticalStreak.style.opacity = '0';
      shockwaveRing.style.opacity = '0';
      lightBloom.style.opacity = '0.08';

      logoWrapper.style.opacity = '1';
      logoWrapper.style.filter = 'none';
      logoWrapper.style.transform = 'scale(1)';

      if (chromeLogoOverlay) chromeLogoOverlay.style.opacity = '0';
      return;
    }

    // 3. SCENE 4: Light handshake at center (2.2s <= t < 3.8s)
    if (t >= MEET_TIME && t < DISSOLVE_START) {
      // Both parts aligned perfectly at center forming "So-cio"
      partSo.style.transform = 'translateX(0)';
      partSo.style.opacity = '1';
      partSo.style.filter = 'none';

      partCio.style.transform = 'translateX(0)';
      partCio.style.opacity = '1';
      partCio.style.filter = 'none';

      // Clearly visible hyphen between "So" and "cio"
      partHyphen.style.opacity = '1';
      partHyphen.style.transform = 'scale(1)';

      // Clasp impact optical flares at t >= 2.95s
      if (t >= CLASP_TIME && t < CLASP_TIME + 0.6) {
        const dt = t - CLASP_TIME;
        const flareLife = dt / 0.6;
        const flareAlpha = Math.max(0, 1 - flareLife) * flareIntensity;
        const flareScale = Math.min(1, dt / 0.12);

        horizontalFlare.style.opacity = `${flareAlpha * 0.95}`;
        horizontalFlare.style.transform = `scaleX(${flareScale})`;

        impactHalo.style.opacity = `${flareAlpha * 0.9}`;
        impactHalo.style.transform = `scale(${0.5 + flareLife * 1.5})`;

        verticalStreak.style.opacity = `${flareAlpha * 0.6}`;
        verticalStreak.style.transform = `scaleY(${flareScale})`;

        shockwaveRing.style.opacity = `${flareAlpha * 0.75}`;
        shockwaveRing.style.transform = `scale(${flareLife * 2.8})`;

        lightBloom.style.opacity = `${0.65 * flareAlpha}`;
        logoWrapper.style.filter = `drop-shadow(0 0 ${20 * flareAlpha}px rgba(251, 245, 165, 0.9))`;
      } else {
        horizontalFlare.style.opacity = '0';
        impactHalo.style.opacity = '0';
        verticalStreak.style.opacity = '0';
        shockwaveRing.style.opacity = '0';
        lightBloom.style.opacity = '0.18';
        logoWrapper.style.filter = 'drop-shadow(0 0 14px rgba(251, 245, 165, 0.35))';
      }

      // Subtle breathing scale
      const shakeNorm = (t - MEET_TIME) / (DISSOLVE_START - MEET_TIME);
      const breath = 1.0 + Math.sin(shakeNorm * Math.PI) * 0.015;
      logoWrapper.style.transform = `scale(${breath})`;
      logoWrapper.style.opacity = '1';

      if (chromeLogoOverlay) chromeLogoOverlay.style.opacity = '0';
      return;
    }

    // 4. SCENE 5: Light hands & text dissolve into swirling particles & assemble logo (3.8s <= t < 5.3s)
    if (t >= DISSOLVE_START && t < LOGO_REVEAL_TIME) {
      const dissolveProg = Math.min(1, (t - DISSOLVE_START) / 0.5); // text dissolves in 0.5s
      const textFade = Math.max(0, 1 - dissolveProg);

      partSo.style.opacity = textFade;
      partCio.style.opacity = textFade;
      partHyphen.style.opacity = textFade;
      logoWrapper.style.opacity = textFade;
      logoWrapper.style.transform = `scale(${1.0 + dissolveProg * 0.05})`;

      horizontalFlare.style.opacity = '0';
      impactHalo.style.opacity = '0';
      verticalStreak.style.opacity = '0';
      shockwaveRing.style.opacity = '0';

      // Bloom swells slightly during galactic swirl then fades to black
      if (t >= 4.7) {
        const fade = Math.max(0, 1 - (t - 4.7) / 0.5);
        lightBloom.style.opacity = `${0.25 * fade}`;
      } else {
        const swirlProg = (t - DISSOLVE_START) / (4.7 - DISSOLVE_START);
        lightBloom.style.opacity = `${0.1 + Math.sin(swirlProg * Math.PI) * 0.3}`;
      }

      // Chrome logo starts emerging slightly during final lock (t > 5.0s)
      if (chromeLogoOverlay) {
        if (t >= 5.0) {
          const preAlpha = (t - 5.0) / (LOGO_REVEAL_TIME - 5.0);
          chromeLogoOverlay.style.opacity = (preAlpha * 0.5).toFixed(2);
        } else {
          chromeLogoOverlay.style.opacity = '0';
        }
      }
      stage.style.backgroundColor = 'transparent';
      return;
    }

    // 5. SCENE 6: Final reveal & 3.5-second hold on pure black (5.3s <= t <= 8.8s)
    if (t >= LOGO_REVEAL_TIME) {
      // Pure black stage background (Netflix intro blackout)
      stage.style.backgroundColor = '#000000';

      // Text completely hidden
      partSo.style.opacity = '0';
      partCio.style.opacity = '0';
      partHyphen.style.opacity = '0';
      logoWrapper.style.opacity = '0';

      horizontalFlare.style.opacity = '0';
      impactHalo.style.opacity = '0';
      verticalStreak.style.opacity = '0';
      shockwaveRing.style.opacity = '0';
      lightBloom.style.opacity = '0'; // Pure darkness around the logo

      // Chrome S logo revealed in full majesty on pure velvet black
      if (chromeLogoOverlay) {
        const revealProg = Math.min(1, (t - LOGO_REVEAL_TIME) / 0.35);
        chromeLogoOverlay.style.opacity = `${revealProg}`;

        const chromeImg = chromeLogoOverlay.querySelector('img');
        if (chromeImg) {
          const holdTime = t - LOGO_REVEAL_TIME;
          const holdProg = Math.min(1, Math.max(0, holdTime / (DURATION - LOGO_REVEAL_TIME)));
          // Iconic cinematic slow push-in (dolly zoom 0.94 -> 1.015)
          const dollyScale = 0.94 + 0.075 * (1 - Math.pow(1 - holdProg, 2));

          const glowPulse = 0.38 + Math.sin(holdTime * 1.5) * 0.08;
          chromeImg.style.filter = [
            `drop-shadow(0 0 28px rgba(251, 245, 165, ${glowPulse.toFixed(3)}))`,
            `drop-shadow(0 0 70px rgba(251, 245, 165, ${(glowPulse * 0.35).toFixed(3)}))`,
            'brightness(1.08)',
            'contrast(1.08)'
          ].join(' ');
          chromeImg.style.transform = `scale(${dollyScale.toFixed(4)})`;
        }
      }
    } else {
      stage.style.backgroundColor = 'transparent';
    }
  }

  /**
   * Main requestAnimationFrame update loop
   */
  function animationLoop(timestamp) {
    if (!lastFrameTimestamp) lastFrameTimestamp = timestamp;
    const deltaSec = (timestamp - lastFrameTimestamp) / 1000;
    lastFrameTimestamp = timestamp;

    if (isPlaying) {
      currentTime += deltaSec * playbackSpeed;

      // Audio cue at t=0
      if (!hasTriggeredSoundThisCycle && currentTime >= 0) {
        hasTriggeredSoundThisCycle = true;
        if (window.cinematicAudio) {
          try {
            window.cinematicAudio.playSequence(0.0);
          } catch (err) {
            console.warn('Cinematic audio playback error:', err);
          }
        }
      }

      // Check auto transition to next page after chrome logo reveal
      if (currentTime >= 6.8) {
        if (!window.__hasSentIntroComplete) {
          window.__hasSentIntroComplete = true;
          try {
            window.parent.postMessage({ type: 'SOCIO_INTRO_COMPLETE' }, '*');
          } catch(e) {}
        }
      }

      // Check end condition
      if (currentTime >= DURATION) {
        currentTime = DURATION;
        isPlaying = false;
        if (studioHeader) studioHeader.classList.remove('is-playing');
      }
    }

    // Update Visuals
    applyTimelineState(currentTime);
    renderLiveBackground(currentTime, timestamp);

    // Update UI Indicators
    updateTimelineUI(currentTime);

    requestAnimationFrame(animationLoop);
  }

  function updateTimelineUI(t) {
    timelineScrubber.value = t;
    const pct = (t / DURATION) * 100;
    scrubberFill.style.width = `${pct}%`;

    const secStr = t.toFixed(2).padStart(5, '0');
    const durStr = DURATION.toFixed(2).padStart(5, '0');
    timecodeDisplay.textContent = `${secStr}s / ${durStr}s`;
  }

  /**
   * Play / Pause / Replay Commands
   */
  function play() {
    if (currentTime >= DURATION) {
      currentTime = 0;
      hasTriggeredSoundThisCycle = false;
    }
    isPlaying = true;
    lastFrameTimestamp = performance.now();
    studioHeader.classList.add('is-playing');
    resetMouseIdle();
  }

  function pause() {
    isPlaying = false;
    studioHeader.classList.remove('is-playing');
    showStudioHeader();
  }

  function togglePlayPause() {
    if (isPlaying) {
      pause();
    } else {
      play();
    }
  }

  function replay() {
    currentTime = 0;
    hasTriggeredSoundThisCycle = false;
    if (chromeLogoOverlay) chromeLogoOverlay.style.opacity = '0';
    applyTimelineState(0);
    play();
    showToast('Replaying So-cio reveal');
  }

  /**
   * UI Auto-Hide on Mouse Inactivity
   */
  function resetMouseIdle() {
    showStudioHeader();
    clearTimeout(mouseIdleTimeout);
    if (isPlaying && !settingsDrawer.classList.contains('open')) {
      mouseIdleTimeout = setTimeout(() => {
        if (isPlaying && !settingsDrawer.classList.contains('open')) {
          studioHeader.classList.add('ui-hidden');
        }
      }, 2500);
    }
  }

  function showStudioHeader() {
    studioHeader.classList.remove('ui-hidden');
  }

  document.addEventListener('mousemove', resetMouseIdle);

  /**
   * Notification Toast
   */
  let toastTimer = null;
  function showToast(msg) {
    if (!toastNotification) return;
    toastNotification.textContent = msg;
    toastNotification.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastNotification.classList.remove('show');
    }, 2400);
  }

  /**
   * Wire Event Listeners
   */
  btnPlayPause.addEventListener('click', togglePlayPause);
  btnReplay.addEventListener('click', replay);

  // Timeline scrubber input
  timelineScrubber.addEventListener('input', (e) => {
    pause();
    currentTime = parseFloat(e.target.value);
    applyTimelineState(currentTime);
    updateTimelineUI(currentTime);
  });

  // Sound toggle
  btnSoundToggle.addEventListener('click', () => {
    if (window.cinematicAudio) {
      const isMuted = window.cinematicAudio.toggleMute();
      document.body.classList.toggle('sound-muted', isMuted);
      showToast(isMuted ? 'Sound muted' : 'Cinematic sound enabled');
    }
  });

  // Settings Drawer Toggle
  btnSettingsToggle.addEventListener('click', () => {
    settingsDrawer.classList.toggle('open');
  });

  btnCloseDrawer.addEventListener('click', () => {
    settingsDrawer.classList.remove('open');
  });

  // Fullscreen toggle
  btnFullscreen.addEventListener('click', () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  });

  // Aspect Ratio Selector
  const aspectButtons = document.querySelectorAll('#aspectRatioSelector .segment-btn');
  aspectButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      aspectButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const aspect = btn.dataset.aspect;
      screenContainer.className = `screen-container aspect-${aspect}`;
      showToast(`Aspect ratio set to ${aspect.replace('-', ':')}`);
    });
  });

  // Typography Suite Catalog (20 curated typefaces featuring Transcity, romantic, couture, cinematic, and cyber styles)
  const TYPOGRAPHY_CATALOG = [
    {
      id: 'transcity',
      name: 'Transcity',
      cssClass: 'font-transcity',
      category: 'featured',
      badge: '★ Featured',
      desc: 'Exclusive luxury high-contrast display font'
    },
    {
      id: 'specimen-swash',
      name: 'Specimen Swash',
      cssClass: 'font-specimen-swash',
      category: 'romantic',
      badge: 'Art Nouveau',
      desc: 'Authentic Art Nouveau looping swash'
    },
    {
      id: 'elsie-swash',
      name: 'Elsie Swash Caps',
      cssClass: 'font-elsie-swash',
      category: 'romantic',
      badge: 'Romantic Swash',
      desc: 'Voluptuous high-contrast swash capitals'
    },
    {
      id: 'cinzel-decorative',
      name: 'Cinzel Decorative',
      cssClass: 'font-cinzel-decorative',
      category: 'romantic',
      badge: 'Roman Swash',
      desc: 'Imperial Roman monumental swashes'
    },
    {
      id: 'cinzel-pure',
      name: 'Cinzel Classic',
      cssClass: 'font-cinzel-pure',
      category: 'cinematic',
      badge: 'Imperial Roman',
      desc: 'Sharp, razor-refined classic Roman serif'
    },
    {
      id: 'bodoni',
      name: 'Bodoni Moda',
      cssClass: 'font-bodoni',
      category: 'couture',
      badge: 'Haute Couture',
      desc: 'Vogue extreme contrast editorial Didone'
    },
    {
      id: 'playfair',
      name: 'Playfair Display',
      cssClass: 'font-playfair',
      category: 'couture',
      badge: 'Editorial Italic',
      desc: 'Dramatic high-contrast italic flourish'
    },
    {
      id: 'cormorant',
      name: 'Cormorant Garamond',
      cssClass: 'font-cormorant',
      category: 'couture',
      badge: 'Renaissance',
      desc: 'Delicate ethereal Renaissance luxury'
    },
    {
      id: 'prata',
      name: 'Prata',
      cssClass: 'font-prata',
      category: 'couture',
      badge: 'Teardrop Serif',
      desc: 'Graceful teardrop Didone terminals'
    },
    {
      id: 'italiana',
      name: 'Italiana',
      cssClass: 'font-italiana',
      category: 'couture',
      badge: 'Milan Runway',
      desc: 'Sleek luxury fashion runway typography'
    },
    {
      id: 'abril',
      name: 'Abril Fatface',
      cssClass: 'font-abril',
      category: 'impact',
      badge: 'Heavy Headline',
      desc: 'Volumetric luxury display serif'
    },
    {
      id: 'rozha',
      name: 'Rozha One',
      cssClass: 'font-rozha',
      category: 'couture',
      badge: 'Expressive',
      desc: 'Ultra-high contrast ornate display serif'
    },
    {
      id: 'syncopate',
      name: 'Syncopate',
      cssClass: 'font-syncopate',
      category: 'cinematic',
      badge: 'Ultra-Wide Scope',
      desc: 'Architectural widescreen cinematic title'
    },
    {
      id: 'syne',
      name: 'Syne',
      cssClass: 'font-syne',
      category: 'cinematic',
      badge: 'Avant-Garde',
      desc: 'Cutting-edge high-fashion experimental'
    },
    {
      id: 'outfit',
      name: 'Outfit',
      cssClass: 'font-outfit',
      category: 'cinematic',
      badge: 'Geometric',
      desc: 'Ultra-clean modern geometric punch'
    },
    {
      id: 'orbitron',
      name: 'Orbitron',
      cssClass: 'font-orbitron',
      category: 'cyber',
      badge: 'Cyberpunk',
      desc: 'Geometric futuristic sci-fi title'
    },
    {
      id: 'space',
      name: 'Space Grotesk',
      cssClass: 'font-space',
      category: 'cyber',
      badge: 'Neo-Brutalist',
      desc: 'Tech-forward modernist display'
    },
    {
      id: 'bebas',
      name: 'Bebas Neue',
      cssClass: 'font-bebas',
      category: 'impact',
      badge: 'Blockbuster',
      desc: 'Towering condensed cinematic punch'
    },
    {
      id: 'righteous',
      name: 'Righteous',
      cssClass: 'font-righteous',
      category: 'cyber',
      badge: 'Deco Synth',
      desc: 'Retro-futuristic curved neon geometry'
    },
    {
      id: 'montserrat',
      name: 'Montserrat Black',
      cssClass: 'font-montserrat',
      category: 'impact',
      badge: 'Powerhouse',
      desc: 'Ultra-bold geometric powerhouse sans'
    }
  ];

  const quickFontSelect = document.getElementById('quickFontSelect');
  const fontCardsGrid = document.getElementById('fontCardsGrid');
  const fontCountPill = document.getElementById('fontCountPill');
  const fontCategoryFilters = document.querySelectorAll('#fontCategoryFilters .font-filter-pill');

  /**
   * Set active font across DOM, Canvas Recorder, Header dropdown, and Drawer cards
   */
  function selectFont(fontItemOrName, triggerReplay = false) {
    const item = typeof fontItemOrName === 'string'
      ? TYPOGRAPHY_CATALOG.find(f => f.name === fontItemOrName || f.id === fontItemOrName) || TYPOGRAPHY_CATALOG[0]
      : fontItemOrName;

    currentFont = item.name;
    recorder.config.fontFamily = item.name;

    // Apply class to brand text
    brandText.className = `brand-text ${item.cssClass}`;

    // Sync Header Dropdown
    if (quickFontSelect) {
      quickFontSelect.value = item.name;
    }

    // Sync Cards Active State
    document.querySelectorAll('.font-card').forEach(card => {
      if (card.dataset.fontName === item.name) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });

    showToast(`Typography: ${item.name} (${item.badge})`);

    if (triggerReplay) {
      replay();
    } else {
      applyTimelineState(currentTime);
    }
  }

  // Populate Header Quick Dropdown
  if (quickFontSelect) {
    quickFontSelect.innerHTML = '';
    const categories = [
      { key: 'featured', label: '★ Custom / Featured' },
      { key: 'romantic', label: 'Romantic & Swash' },
      { key: 'couture', label: 'Haute Couture' },
      { key: 'cinematic', label: 'Cinematic' },
      { key: 'cyber', label: 'Cyber / Sci-Fi' },
      { key: 'impact', label: 'Bold Impact' }
    ];

    categories.forEach(cat => {
      const group = document.createElement('optgroup');
      group.label = cat.label;
      TYPOGRAPHY_CATALOG.filter(f => f.category === cat.key).forEach(f => {
        const opt = document.createElement('option');
        opt.value = f.name;
        opt.textContent = `${f.name} — ${f.badge}`;
        group.appendChild(opt);
      });
      quickFontSelect.appendChild(group);
    });

    quickFontSelect.value = currentFont;
    quickFontSelect.addEventListener('change', (e) => {
      selectFont(e.target.value, true);
    });
  }

  // Render Typography Cards Grid in Drawer
  function renderFontCards(category = 'all') {
    if (!fontCardsGrid) return;
    fontCardsGrid.innerHTML = '';

    const list = category === 'all'
      ? TYPOGRAPHY_CATALOG
      : TYPOGRAPHY_CATALOG.filter(f => f.category === category);

    if (fontCountPill) {
      fontCountPill.textContent = `${list.length} Fonts`;
    }

    list.forEach(font => {
      const card = document.createElement('div');
      card.className = `font-card ${font.name === currentFont ? 'active' : ''}`;
      card.dataset.fontName = font.name;
      card.title = `Switch to ${font.name}`;

      // Custom live preview styling per font
      const sampleText = (font.category === 'cinematic' && (font.id === 'syncopate' || font.id === 'bebas'))
        ? 'SO-CIO'
        : 'So-cio';

      card.innerHTML = `
        <div class="font-card-top">
          <span class="font-card-name">${font.name}</span>
          <span class="font-card-badge">${font.badge}</span>
        </div>
        <div class="font-card-preview ${font.cssClass}">
          ${sampleText}
        </div>
        <div class="font-card-desc">${font.desc}</div>
      `;

      card.addEventListener('click', () => {
        selectFont(font, true);
      });

      fontCardsGrid.appendChild(card);
    });
  }

  renderFontCards('all');

  // Filter Buttons
  fontCategoryFilters.forEach(pill => {
    pill.addEventListener('click', () => {
      fontCategoryFilters.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      renderFontCards(pill.dataset.category);
    });
  });

  // Speed Selector
  const speedButtons = document.querySelectorAll('#speedSelector .segment-btn');
  speedButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      speedButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      playbackSpeed = parseFloat(btn.dataset.speed);
      showToast(`Speed: ${playbackSpeed}x`);
    });
  });

  // Background Atmosphere Engine Selector (React Bits Pro Lightspeed / Fusion / Silk)
  const bgModeButtons = document.querySelectorAll('#bgModeSelector .segment-btn');
  const lightspeedControlsGroup = document.getElementById('lightspeedControlsGroup');
  const lightspeedSpeedSlider = document.getElementById('lightspeedSpeedSlider');
  const lightspeedSpeedValue = document.getElementById('lightspeedSpeedValue');
  const lightspeedStreakSlider = document.getElementById('lightspeedStreakSlider');
  const lightspeedStreakValue = document.getElementById('lightspeedStreakValue');

  bgModeButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      bgModeButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentBgMode = btn.dataset.bg;
      recorder.config.bgMode = currentBgMode;
      if (lightspeedControlsGroup) {
        lightspeedControlsGroup.style.display = (currentBgMode === 'silk') ? 'none' : 'flex';
      }
      const label = currentBgMode === 'lightspeed' ? 'Lightspeed Hyperspace' : (currentBgMode === 'fusion' ? 'Cinematic Fusion' : 'Silk Waves');
      showToast(`Atmosphere: ${label}`);
    });
  });

  if (lightspeedSpeedSlider) {
    lightspeedSpeedSlider.addEventListener('input', (e) => {
      const spd = parseFloat(e.target.value);
      if (lightspeedSpeedValue) lightspeedSpeedValue.textContent = `${spd.toFixed(2)}x`;
      if (lightspeedEngine) lightspeedEngine.speed = spd;
    });
  }

  if (lightspeedStreakSlider) {
    lightspeedStreakSlider.addEventListener('input', (e) => {
      const count = parseInt(e.target.value, 10);
      if (lightspeedStreakValue) lightspeedStreakValue.textContent = `${count}`;
      if (lightspeedEngine) lightspeedEngine.streakCount = count;
    });
  }

  // Slider events
  flareIntensitySlider.addEventListener('input', (e) => {
    flareIntensity = parseFloat(e.target.value);
    recorder.config.flareIntensity = flareIntensity;
  });

  motionBlurSlider.addEventListener('input', (e) => {
    maxMotionBlur = parseFloat(e.target.value);
    recorder.config.motionBlurStrength = maxMotionBlur;
  });

  if (fontSizeSlider) {
    fontSizeSlider.addEventListener('input', (e) => {
      const scale = parseFloat(e.target.value);
      if (fontSizeValue) fontSizeValue.textContent = `${Math.round(scale * 100)}%`;
      document.documentElement.style.setProperty('--logo-scale', scale);
      recorder.config.fontScale = scale;
      applyTimelineState(currentTime);
    });
  }

  // Direct PNG 4K wallpaper capture
  btnCaptureFrame.addEventListener('click', () => {
    recorder.config.fontFamily = currentFont;
    recorder.config.flareIntensity = flareIntensity;
    const timeToCapture = (currentTime >= 0.5) ? currentTime : 6.2;
    recorder.capturePng(timeToCapture);
    showToast(`Downloaded 4K Frame @ ${timeToCapture.toFixed(2)}s (PNG)`);
  });

  // Video Export Handler
  btnExportVideo.addEventListener('click', async () => {
    pause();
    exportModalBackdrop.classList.add('open');
    exportProgressFill.style.width = '0%';
    exportStatusLabel.textContent = 'Initializing 60 FPS video renderer...';

    recorder.config.fontFamily = currentFont;
    recorder.config.flareIntensity = flareIntensity;
    recorder.config.motionBlurStrength = maxMotionBlur;
    recorder.config.bgMode = currentBgMode;

    try {
      await recorder.exportVideo(
        (frame, total, percent) => {
          exportProgressFill.style.width = `${percent}%`;
          exportStatusLabel.textContent = `Rendering frame ${frame} of ${total} (${percent}%)`;
        },
        (blob) => {
          exportModalBackdrop.classList.remove('open');
          showToast('1080p Video exported successfully!');
        },
        (err) => {
          exportModalBackdrop.classList.remove('open');
          console.error(err);
          showToast('Video export encountered an issue');
        }
      );
    } catch (err) {
      exportModalBackdrop.classList.remove('open');
      console.error(err);
      showToast('Error exporting video');
    }
  });

  btnCancelExport.addEventListener('click', () => {
    recorder.cancelExport();
    exportModalBackdrop.classList.remove('open');
    showToast('Export cancelled');
  });

  // Keyboard Shortcuts
  window.addEventListener('keydown', (e) => {
    // Ignore if input focused
    if (e.target.tagName === 'INPUT') return;

    if (e.code === 'Space') {
      e.preventDefault();
      togglePlayPause();
    } else if (e.code === 'KeyR') {
      e.preventDefault();
      replay();
    } else if (e.code === 'KeyT') {
      e.preventDefault();
      const currentIndex = TYPOGRAPHY_CATALOG.findIndex(f => f.name === currentFont);
      const nextIndex = (currentIndex + 1) % TYPOGRAPHY_CATALOG.length;
      selectFont(TYPOGRAPHY_CATALOG[nextIndex], true);
    } else if (e.code === 'KeyF') {
      e.preventDefault();
      btnFullscreen.click();
    } else if (e.code === 'KeyM') {
      e.preventDefault();
      btnSoundToggle.click();
    } else if (e.code === 'KeyH') {
      e.preventDefault();
      studioHeader.classList.toggle('ui-hidden');
    } else if (e.code === 'Escape') {
      if (settingsDrawer.classList.contains('open')) {
        settingsDrawer.classList.remove('open');
      }
    }
  });

  // Start animation loop
  requestAnimationFrame(animationLoop);

  // Prime audio on first user interaction
  document.addEventListener('pointerdown', () => {
    if (window.cinematicAudio) window.cinematicAudio.ensureContext();
  }, { once: true });

  // Auto-play intro on load
  setTimeout(() => {
    play();
  }, 300);

  // Click anywhere to skip/transition to main page
  document.addEventListener('click', () => {
    if (currentTime > 0.8) {
      try {
        window.parent.postMessage({ type: 'SOCIO_INTRO_SKIP' }, '*');
      } catch (err) {}
    }
  });
});
