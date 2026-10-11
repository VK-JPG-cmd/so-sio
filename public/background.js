/**
 * background.js
 * High-performance 60 FPS generative luxury background engine for So-cio.
 * Strictly constrained to:
 *   - Deep black: #111312
 *   - Charcoal grey: #434346
 *   - Pale butter yellow: #FBF5A5
 */

(() => {
  'use strict';

  // Strict Color Constants
  const PALETTE = {
    black: '#111312',
    blackRgba: (a) => `rgba(17, 19, 18, ${a})`,
    charcoal: '#434346',
    charcoalRgba: (a) => `rgba(67, 67, 70, ${a})`,
    paleYellow: '#FBF5A5',
    paleYellowRgba: (a) => `rgba(251, 245, 165, ${a})`
  };

  const canvas = document.getElementById('bgCanvas');
  const ctx = canvas.getContext('2d', { alpha: false });
  const blackCurtain = document.getElementById('blackCurtain');
  const ambientRadiance = document.getElementById('ambientRadiance');

  let width = 0;
  let height = 0;
  let dpr = 1;

  // Animation Timeline States
  let startTime = null;
  let elapsedTime = 0;
  let isMeetingTriggered = false;
  let centerBloomIntensity = 0;

  // Mouse Interaction (Subtle, Organic Ambient Reflection)
  let mouse = { x: 0.5, y: 0.5, targetX: 0.5, targetY: 0.5 };

  /**
   * Resize Canvas to Exact Window Dimensions with DPR Support
   */
  function handleResize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;

    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);

    ctx.scale(dpr, dpr);
  }

  window.addEventListener('resize', handleResize, { passive: true });
  handleResize();

  /**
   * Floating Micro-Particles Class
   * Tiny celestial dust drifting organically with gentle breathing opacity
   */
  class AmbientParticle {
    constructor() {
      this.reset(true);
    }

    reset(initial = false) {
      this.x = Math.random() * width;
      this.y = initial ? Math.random() * height : height + 15;
      this.radius = Math.random() * 1.6 + 0.6;
      this.baseSpeedY = Math.random() * 0.22 + 0.08;
      this.speedX = (Math.random() - 0.5) * 0.18;
      this.oscillationSpeed = Math.random() * 0.02 + 0.01;
      this.oscillationAmp = Math.random() * 14 + 6;
      this.seed = Math.random() * Math.PI * 2;
      this.isYellow = Math.random() > 0.45; // 55% pale yellow, 45% charcoal grey
      this.maxAlpha = this.isYellow
        ? Math.random() * 0.35 + 0.15
        : Math.random() * 0.28 + 0.12;
    }

    update(time, stageAlpha) {
      this.y -= this.baseSpeedY;
      this.x += Math.sin(time * this.oscillationSpeed + this.seed) * 0.25 + this.speedX;

      // Wrap around screen boundaries
      if (this.y < -20 || this.x < -30 || this.x > width + 30) {
        this.reset(false);
      }

      this.currentAlpha = Math.sin(time * 0.8 + this.seed) * 0.5 + 0.5;
      this.currentAlpha = this.currentAlpha * this.maxAlpha * stageAlpha;
    }

    draw(context) {
      if (this.currentAlpha <= 0.01) return;

      context.beginPath();
      context.arc(this.x, this.y, this.radius, 0, Math.PI * 2);

      if (this.isYellow) {
        context.fillStyle = PALETTE.paleYellowRgba(this.currentAlpha);
      } else {
        context.fillStyle = PALETTE.charcoalRgba(this.currentAlpha);
      }
      context.fill();
    }
  }

  // Instantiate 55 Floating Micro-Particles
  const particles = Array.from({ length: 55 }, () => new AmbientParticle());

  /**
   * Silk Wave Layer Definitions
   * Mathematical layered Bézier curves simulating luxury haute-couture silk cloth
   */
  const silkWaves = [
    {
      baseYRatio: 0.38,
      amplitude: 55,
      frequency: 0.0012,
      speed: 0.0006,
      phase: 0,
      opacity: 0.18,
      wavelength: 1.1
    },
    {
      baseYRatio: 0.52,
      amplitude: 75,
      frequency: 0.0016,
      speed: 0.00075,
      phase: Math.PI * 0.5,
      opacity: 0.22,
      wavelength: 1.35
    },
    {
      baseYRatio: 0.65,
      amplitude: 95,
      frequency: 0.0011,
      speed: 0.00045,
      phase: Math.PI * 1.1,
      opacity: 0.25,
      wavelength: 0.95
    },
    {
      baseYRatio: 0.78,
      amplitude: 110,
      frequency: 0.0014,
      speed: 0.00085,
      phase: Math.PI * 1.6,
      opacity: 0.19,
      wavelength: 1.2
    }
  ];

  /**
   * Render Flowing Silk Waves
   */
  function renderSilkWaves(time, waveGlobalAlpha) {
    if (waveGlobalAlpha <= 0.005) return;

    for (let i = 0; i < silkWaves.length; i++) {
      const w = silkWaves[i];
      const baseY = height * w.baseYRatio + Math.sin(time * 0.0003 + w.phase) * 25;
      const alpha = w.opacity * waveGlobalAlpha;

      ctx.save();
      ctx.beginPath();
      ctx.moveTo(0, height);

      const segments = 24;
      const step = width / segments;

      for (let s = 0; s <= segments; s++) {
        const x = s * step;
        const sine1 = Math.sin(x * w.frequency * w.wavelength + time * w.speed + w.phase);
        const sine2 = Math.cos(x * w.frequency * 0.6 - time * w.speed * 0.8 + w.phase);
        const y = baseY + (sine1 * w.amplitude * 0.7 + sine2 * w.amplitude * 0.3);

        if (s === 0) {
          ctx.lineTo(x, y);
        } else {
          const prevX = (s - 1) * step;
          const prevSine1 = Math.sin(prevX * w.frequency * w.wavelength + time * w.speed + w.phase);
          const prevSine2 = Math.cos(prevX * w.frequency * 0.6 - time * w.speed * 0.8 + w.phase);
          const prevY = baseY + (prevSine1 * w.amplitude * 0.7 + prevSine2 * w.amplitude * 0.3);

          const midX = (prevX + x) * 0.5;
          const midY = (prevY + y) * 0.5;
          ctx.quadraticCurveTo(prevX, prevY, midX, midY);
        }
      }

      ctx.lineTo(width, height);
      ctx.closePath();

      // Multi-stop flowing gradient using strict palette (#434346 to #111312)
      const grad = ctx.createLinearGradient(0, baseY - w.amplitude, 0, height);
      grad.addColorStop(0, PALETTE.charcoalRgba(alpha * 1.1));
      grad.addColorStop(0.35, PALETTE.charcoalRgba(alpha * 0.65));
      grad.addColorStop(0.7, PALETTE.charcoalRgba(alpha * 0.2));
      grad.addColorStop(1, PALETTE.blackRgba(alpha * 0.05));

      ctx.fillStyle = grad;
      ctx.fill();

      // Delicate luxury crest line highlight on the wave rim
      ctx.lineWidth = 1.2;
      ctx.strokeStyle = PALETTE.charcoalRgba(alpha * 0.85);
      ctx.stroke();

      ctx.restore();
    }
  }

  /**
   * Pale-Yellow Light Streaks Engine
   * Travels from left & right, meets softly at the center, then holds subtle luminous breath
   */
  function renderLightStreaks(timeSec) {
    // Streak Progression Timings
    const streakStart = 2.4;
    const streakMeet = 4.8;

    if (timeSec < streakStart) return;

    // Calculate flight progression (0.0 to 1.0)
    const progressRaw = Math.min(1.0, (timeSec - streakStart) / (streakMeet - streakStart));
    // Smooth quintic ease-out deceleration
    const progress = 1 - Math.pow(1 - progressRaw, 4);

    const centerX = width * 0.5;
    const centerY = height * 0.5;

    // Head Coordinates
    const leftHeadX = progress * (centerX + 15);
    const leftHeadY = centerY + Math.sin(progressRaw * Math.PI * 1.5) * (height * 0.08);

    const rightHeadX = width - progress * (centerX + 15);
    const rightHeadY = centerY - Math.sin(progressRaw * Math.PI * 1.5) * (height * 0.08);

    // Alpha envelopes
    const streakAlpha = Math.min(1.0, (timeSec - streakStart) * 0.9) * 0.85;

    ctx.save();

    // 1. Left Light Streak
    drawLuminousStreak(0, centerY - 40, leftHeadX, leftHeadY, streakAlpha, true);

    // 2. Right Light Streak
    drawLuminousStreak(width, centerY + 40, rightHeadX, rightHeadY, streakAlpha, false);

    // 3. Meeting point milestone at center (4.8s+)
    if (timeSec >= streakMeet) {
      if (!isMeetingTriggered) {
        isMeetingTriggered = true;
        if (ambientRadiance) ambientRadiance.classList.add('active');
      }

      const postMeetDuration = timeSec - streakMeet;
      centerBloomIntensity = Math.min(1.0, postMeetDuration * 0.8);

      // Soft center meeting diffusion
      const breathe = Math.sin(postMeetDuration * 0.7) * 0.15 + 0.85;
      const bloomRadius = Math.min(width, height) * 0.28 * breathe;

      const bloomGrad = ctx.createRadialGradient(
        centerX, centerY, 4,
        centerX, centerY, bloomRadius
      );
      bloomGrad.addColorStop(0, PALETTE.paleYellowRgba(0.18 * centerBloomIntensity));
      bloomGrad.addColorStop(0.35, PALETTE.paleYellowRgba(0.08 * centerBloomIntensity));
      bloomGrad.addColorStop(0.7, PALETTE.charcoalRgba(0.04 * centerBloomIntensity));
      bloomGrad.addColorStop(1, PALETTE.blackRgba(0));

      ctx.fillStyle = bloomGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, bloomRadius, 0, Math.PI * 2);
      ctx.fill();

      // Gentle central horizontal beam highlight
      const beamW = width * 0.42 * breathe;
      const beamGrad = ctx.createLinearGradient(centerX - beamW, centerY, centerX + beamW, centerY);
      beamGrad.addColorStop(0, PALETTE.paleYellowRgba(0));
      beamGrad.addColorStop(0.5, PALETTE.paleYellowRgba(0.14 * centerBloomIntensity));
      beamGrad.addColorStop(1, PALETTE.paleYellowRgba(0));

      ctx.fillStyle = beamGrad;
      ctx.fillRect(centerX - beamW, centerY - 1.5, beamW * 2, 3);
    }

    ctx.restore();
  }

  /**
   * Draw tapered, curved luminous light trail
   */
  function drawLuminousStreak(startX, startY, headX, headY, alpha, isLeft) {
    if (alpha <= 0.01) return;

    ctx.save();

    const dx = headX - startX;
    const dy = headY - startY;
    const trailLength = Math.sqrt(dx * dx + dy * dy);
    if (trailLength < 4) {
      ctx.restore();
      return;
    }

    // Luminous beam gradient using #FBF5A5
    const streakGrad = ctx.createLinearGradient(startX, startY, headX, headY);
    streakGrad.addColorStop(0, PALETTE.paleYellowRgba(0));
    streakGrad.addColorStop(0.65, PALETTE.paleYellowRgba(alpha * 0.25));
    streakGrad.addColorStop(0.92, PALETTE.paleYellowRgba(alpha * 0.7));
    streakGrad.addColorStop(1, PALETTE.paleYellowRgba(alpha * 0.95));

    ctx.strokeStyle = streakGrad;
    ctx.lineWidth = 2.4;
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(startX, startY);

    const ctrlX = startX + (headX - startX) * 0.5;
    const ctrlY = startY + (isLeft ? 45 : -45);
    ctx.quadraticCurveTo(ctrlX, ctrlY, headX, headY);
    ctx.stroke();

    // Soft radiant aura around head
    const glowRadius = 26;
    const glowGrad = ctx.createRadialGradient(headX, headY, 1, headX, headY, glowRadius);
    glowGrad.addColorStop(0, PALETTE.paleYellowRgba(alpha * 0.65));
    glowGrad.addColorStop(0.35, PALETTE.paleYellowRgba(alpha * 0.22));
    glowGrad.addColorStop(1, PALETTE.paleYellowRgba(0));

    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(headX, headY, glowRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  /**
   * Main 60 FPS Render Loop
   */
  function render(timestamp) {
    if (!startTime) startTime = timestamp;
    elapsedTime = (timestamp - startTime) / 1000;

    // Smooth mouse interpolation
    mouse.x += (mouse.targetX - mouse.x) * 0.04;
    mouse.y += (mouse.targetY - mouse.y) * 0.04;

    // Clear Screen with Deep Black (#111312)
    ctx.fillStyle = PALETTE.black;
    ctx.fillRect(0, 0, width, height);

    // Sequence Stages:
    // Stage 1 (0.0s - 1.0s): Pure black silence
    // Stage 2 (1.0s - 3.2s): Slowly reveal charcoal-grey flowing waves
    // Stage 3 (2.4s - 4.8s): Pale-yellow light streaks flow in
    // Stage 4 (4.8s+): Light streaks meet softly at center & hold minimal glowing background

    let waveAlpha = 0;
    if (elapsedTime > 1.0) {
      waveAlpha = Math.min(1.0, (elapsedTime - 1.0) / 2.2);
    }

    let particleAlpha = 0;
    if (elapsedTime > 1.6) {
      particleAlpha = Math.min(1.0, (elapsedTime - 1.6) / 2.0);
    }

    // 1. Draw Flowing Charcoal-Grey Waves (#434346)
    renderSilkWaves(timestamp, waveAlpha);

    // 2. Draw Floating Micro-Particles
    if (particleAlpha > 0) {
      for (let i = 0; i < particles.length; i++) {
        particles[i].update(elapsedTime, particleAlpha);
        particles[i].draw(ctx);
      }
    }

    // 3. Draw Pale-Yellow Glowing Light Streaks (#FBF5A5)
    renderLightStreaks(elapsedTime);

    // 4. Subtle Ambient Cursor Light Refraction
    if (waveAlpha > 0.5) {
      const curX = mouse.x * width;
      const curY = mouse.y * height;
      const auraRadius = Math.min(width, height) * 0.32;
      const cursorGrad = ctx.createRadialGradient(curX, curY, 2, curX, curY, auraRadius);
      cursorGrad.addColorStop(0, PALETTE.paleYellowRgba(0.035 * waveAlpha));
      cursorGrad.addColorStop(0.5, PALETTE.charcoalRgba(0.018 * waveAlpha));
      cursorGrad.addColorStop(1, PALETTE.blackRgba(0));

      ctx.fillStyle = cursorGrad;
      ctx.beginPath();
      ctx.arc(curX, curY, auraRadius, 0, Math.PI * 2);
      ctx.fill();
    }

    requestAnimationFrame(render);
  }

  // Interactive Mouse Move Handling
  window.addEventListener('pointermove', (e) => {
    mouse.targetX = e.clientX / width;
    mouse.targetY = e.clientY / height;
  }, { passive: true });

  // Replay Sequence Support (<kbd>Space</kbd> or <kbd>R</kbd> or Click)
  function restartSequence() {
    startTime = null;
    elapsedTime = 0;
    isMeetingTriggered = false;
    centerBloomIntensity = 0;

    if (ambientRadiance) ambientRadiance.classList.remove('active');
    if (blackCurtain) {
      blackCurtain.classList.remove('reveal');
      setTimeout(() => {
        blackCurtain.classList.add('reveal');
      }, 50);
    }
  }

  window.addEventListener('keydown', (e) => {
    if (e.code === 'KeyR' || e.code === 'Space') {
      e.preventDefault();
      restartSequence();
    } else if (e.code === 'KeyF') {
      e.preventDefault();
      if (!document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {});
      } else {
        document.exitFullscreen().catch(() => {});
      }
    }
  });

  // Start Sequence: Lift Black Curtain at 0.4s
  setTimeout(() => {
    if (blackCurtain) blackCurtain.classList.add('reveal');
  }, 400);

  // Kick off Animation Loop
  requestAnimationFrame(render);
})();
