/**
 * luxury-background.js
 * High-performance 60 FPS generative luxury background engine for So-cio.
 * Strictly constrained to the signature luxury palette:
 *   - Deep black: #111312
 *   - Charcoal grey: #434346
 *   - Pale butter yellow: #FBF5A5
 * 
 * Synchronized with the master timeline (0.0s -> 5.8s) for live playback
 * and 60 FPS canvas video recording.
 */

(function(global) {
  'use strict';

  const PALETTE = {
    black: '#111312',
    blackRgba: (a) => `rgba(17, 19, 18, ${Math.max(0, Math.min(1, a))})`,
    charcoal: '#434346',
    charcoalRgba: (a) => `rgba(67, 67, 70, ${Math.max(0, Math.min(1, a))})`,
    paleYellow: '#FBF5A5',
    paleYellowRgba: (a) => `rgba(251, 245, 165, ${Math.max(0, Math.min(1, a))})`
  };

  class LuxuryBackgroundEngine {
    constructor(options = {}) {
      this.options = Object.assign({
        particleCount: 52,
        sparkCount: 36,
        enableCursorAura: true,
        enableShafts: true,
        breatheSpeed: 0.6
      }, options);

      // 5 Layered Silk Waves with dual-frequency harmonic curves & individual depth factors
      this.waves = [
        {
          baseYRatio: 0.30,
          amplitude: 48,
          freq: 0.0011,
          speed: 0.0006,
          phase: 0.2,
          opacity: 0.24,
          crestAlpha: 0.38,
          wavelength: 1.15,
          depthFactor: 0.4
        },
        {
          baseYRatio: 0.44,
          amplitude: 68,
          freq: 0.0015,
          speed: 0.0008,
          phase: 1.5,
          opacity: 0.28,
          crestAlpha: 0.48,
          wavelength: 1.30,
          depthFactor: 0.6
        },
        {
          baseYRatio: 0.58,
          amplitude: 88,
          freq: 0.0010,
          speed: 0.0005,
          phase: 2.9,
          opacity: 0.32,
          crestAlpha: 0.58,
          wavelength: 0.95,
          depthFactor: 0.8
        },
        {
          baseYRatio: 0.72,
          amplitude: 110,
          freq: 0.0013,
          speed: 0.0009,
          phase: 4.2,
          opacity: 0.26,
          crestAlpha: 0.42,
          wavelength: 1.25,
          depthFactor: 1.0
        },
        {
          baseYRatio: 0.86,
          amplitude: 125,
          freq: 0.0009,
          speed: 0.0006,
          phase: 5.4,
          opacity: 0.22,
          crestAlpha: 0.32,
          wavelength: 1.10,
          depthFactor: 1.2
        }
      ];

      // Pre-generated persistent floating micro-particles
      this.particles = [];
      for (let i = 0; i < this.options.particleCount; i++) {
        this.particles.push({
          xRatio: Math.random(),
          yRatio: Math.random(),
          radius: Math.random() * 1.8 + 0.6,
          speedY: Math.random() * 0.035 + 0.012,
          driftSpeed: Math.random() * 0.6 + 0.3,
          driftAmp: Math.random() * 0.02 + 0.005,
          seed: Math.random() * Math.PI * 2,
          isYellow: Math.random() > 0.35, // 65% pale-yellow, 35% charcoal
          maxAlpha: Math.random() * 0.45 + 0.22
        });
      }

      // Dynamic impact sparks spawned on 2.0s meeting
      this.sparks = [];
      for (let i = 0; i < this.options.sparkCount; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 340 + 90;
        this.sparks.push({
          angle: angle,
          speed: speed,
          decay: Math.random() * 0.8 + 0.6,
          size: Math.random() * 2.2 + 0.8,
          seed: Math.random() * Math.PI
        });
      }

      // Light shafts / god rays definitions
      this.shafts = [
        { xOffsetRatio: 0.15, widthRatio: 0.22, angleDeg: 34, speed: 0.0003, alpha: 0.045 },
        { xOffsetRatio: 0.48, widthRatio: 0.28, angleDeg: 32, speed: 0.0004, alpha: 0.055 },
        { xOffsetRatio: 0.82, widthRatio: 0.25, angleDeg: 35, speed: 0.00025, alpha: 0.040 }
      ];
    }

    /**
     * Easing curve: Quintic ease-out for smooth deceleration
     */
    easeOutQuint(t) {
      return 1 - Math.pow(1 - t, 5);
    }

    easeOutCubic(t) {
      return 1 - Math.pow(1 - t, 3);
    }

    /**
     * Render the complete luxury background at time `t` (seconds)
     * @param {CanvasRenderingContext2D} ctx Target 2D canvas context
     * @param {number} W Width in pixels
     * @param {number} H Height in pixels
     * @param {number} t Animation time in seconds
     * @param {number} mouseX Normalized cursor X (0..1)
     * @param {number} mouseY Normalized cursor Y (0..1)
     */
    renderAt(ctx, W, H, t, mouseX = 0.5, mouseY = 0.5, wallClockSec = null) {
      const animClock = wallClockSec !== null ? wallClockSec : t;
      const centerX = W * 0.5;
      const centerY = H * 0.5;

      // 1. Clear Screen with Deep Black (#111312)
      ctx.fillStyle = PALETTE.black;
      ctx.fillRect(0, 0, W, H);

      // Global atmosphere envelope:
      // Base luxury ambiance is always present (0.45) with breathing waves,
      // swelling to 1.0 during flight, impact, and hold
      let globalAtmosphereAlpha = 0.45;
      if (t >= 0.3 && t < 2.0) {
        globalAtmosphereAlpha = 0.45 + 0.55 * ((t - 0.3) / 1.7);
      } else if (t >= 2.0 && t <= 4.0) {
        globalAtmosphereAlpha = 1.0;
      } else if (t > 4.0) {
        globalAtmosphereAlpha = 0.45 + 0.55 * Math.max(0, 1.0 - (t - 4.0) / 1.8);
      }

      ctx.save();

      // 2. Render Volumetric Light Shafts (angled atmospheric depth)
      if (this.options.enableShafts) {
        this.renderVolumetricLightShafts(ctx, W, H, animClock, globalAtmosphereAlpha);
      }

      // 3. Render Layered Silk Caustic Waves with Parallax
      this.renderSilkWaves(ctx, W, H, animClock, globalAtmosphereAlpha, mouseX, mouseY);

      // 4. Render Floating Micro-Embers & Constellation Tech Hairlines
      this.renderParticles(ctx, W, H, animClock, globalAtmosphereAlpha);

      // 5. Render Pale-Yellow Inbound Light Streaks (0.4s -> 2.0s)
      this.renderLightStreaks(ctx, W, H, t, centerX, centerY);

      // 6. Render Center Meeting Celestial Bloom & Shockwave (t >= 1.95s)
      if (t >= 1.95) {
        this.renderCenterBloom(ctx, W, H, t, centerX, centerY);
      }

      // 7. Center Optical Sanctuary Mask:
      // Keeps the core clean, velvety dark, and serene so the So-cio logo commands focus
      const sanctuaryRadius = Math.min(W, H) * 0.44;
      const sanctuaryGrad = ctx.createRadialGradient(
        centerX, centerY, 0,
        centerX, centerY, sanctuaryRadius
      );
      sanctuaryGrad.addColorStop(0, PALETTE.blackRgba(0.68));
      sanctuaryGrad.addColorStop(0.38, PALETTE.blackRgba(0.48));
      sanctuaryGrad.addColorStop(0.72, PALETTE.blackRgba(0.18));
      sanctuaryGrad.addColorStop(1, PALETTE.blackRgba(0));

      ctx.fillStyle = sanctuaryGrad;
      ctx.beginPath();
      ctx.arc(centerX, centerY, sanctuaryRadius, 0, Math.PI * 2);
      ctx.fill();

      // 8. Interactive Ambient Cursor Glow Aura
      if (this.options.enableCursorAura && mouseX !== undefined && mouseY !== undefined) {
        const curX = mouseX * W;
        const curY = mouseY * H;
        const curRadius = Math.min(W, H) * 0.35;
        const curGrad = ctx.createRadialGradient(curX, curY, 2, curX, curY, curRadius);
        curGrad.addColorStop(0, PALETTE.paleYellowRgba(0.045 * globalAtmosphereAlpha));
        curGrad.addColorStop(0.45, PALETTE.charcoalRgba(0.02 * globalAtmosphereAlpha));
        curGrad.addColorStop(1, PALETTE.blackRgba(0));

        ctx.fillStyle = curGrad;
        ctx.beginPath();
        ctx.arc(curX, curY, curRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      // 9. Subtle Outer Vignette Depth Framing
      const outerVignette = ctx.createRadialGradient(
        centerX, centerY, Math.min(W, H) * 0.32,
        centerX, centerY, Math.max(W, H) * 0.78
      );
      outerVignette.addColorStop(0, PALETTE.blackRgba(0));
      outerVignette.addColorStop(0.6, PALETTE.blackRgba(0.32));
      outerVignette.addColorStop(1, PALETTE.blackRgba(0.92));

      ctx.fillStyle = outerVignette;
      ctx.fillRect(0, 0, W, H);

      ctx.restore();
    }

    /**
     * Render angled volumetric light shafts (soft divine lighting)
     */
    renderVolumetricLightShafts(ctx, W, H, t, globalAlpha) {
      const timeMs = t * 1000;
      ctx.save();

      for (let i = 0; i < this.shafts.length; i++) {
        const shaft = this.shafts[i];
        const breath = Math.sin(timeMs * shaft.speed + i) * 0.25 + 0.75;
        const shaftAlpha = shaft.alpha * breath * globalAlpha;

        const startX = W * shaft.xOffsetRatio + Math.sin(t * 0.2 + i) * 35;
        const shaftWidth = W * shaft.widthRatio;

        const rad = (shaft.angleDeg * Math.PI) / 180;
        const endX = startX + Math.tan(rad) * H;

        const grad = ctx.createLinearGradient(startX, 0, endX, H);
        grad.addColorStop(0, PALETTE.paleYellowRgba(shaftAlpha * 0.8));
        grad.addColorStop(0.4, PALETTE.paleYellowRgba(shaftAlpha * 0.5));
        grad.addColorStop(0.8, PALETTE.charcoalRgba(shaftAlpha * 0.2));
        grad.addColorStop(1, PALETTE.blackRgba(0));

        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.moveTo(startX - shaftWidth * 0.5, 0);
        ctx.lineTo(startX + shaftWidth * 0.5, 0);
        ctx.lineTo(endX + shaftWidth * 0.7, H);
        ctx.lineTo(endX - shaftWidth * 0.7, H);
        ctx.closePath();
        ctx.fill();
      }

      ctx.restore();
    }

    /**
     * Render the 5 layers of flowing silk waves with parallax
     */
    renderSilkWaves(ctx, W, H, t, globalAlpha, mouseX = 0.5, mouseY = 0.5) {
      const timeMs = t * 1000;
      const pOffsetX = (mouseX - 0.5);
      const pOffsetY = (mouseY - 0.5);

      for (let i = 0; i < this.waves.length; i++) {
        const w = this.waves[i];
        const parallaxY = pOffsetY * (w.depthFactor * 24);
        const parallaxX = pOffsetX * (w.depthFactor * 32);

        const baseY = H * w.baseYRatio + Math.sin(t * 0.5 + w.phase) * 18 + parallaxY;
        const waveAlpha = w.opacity * globalAlpha;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(0, H);

        const segments = 32;
        const step = W / segments;

        const points = [];

        for (let s = 0; s <= segments; s++) {
          const x = s * step;
          const sine1 = Math.sin((x + parallaxX) * w.freq * w.wavelength + timeMs * w.speed + w.phase);
          const sine2 = Math.cos((x + parallaxX) * w.freq * 0.65 - timeMs * w.speed * 0.8 + w.phase);
          const y = baseY + (sine1 * w.amplitude * 0.72 + sine2 * w.amplitude * 0.28);
          points.push({ x, y });

          if (s === 0) {
            ctx.lineTo(x, y);
          } else {
            const prev = points[s - 1];
            const midX = (prev.x + x) * 0.5;
            const midY = (prev.y + y) * 0.5;
            ctx.quadraticCurveTo(prev.x, prev.y, midX, midY);
          }
        }

        ctx.lineTo(W, H);
        ctx.closePath();

        // Multi-stop Charcoal body gradient (#434346 to #111312)
        const waveGrad = ctx.createLinearGradient(0, baseY - w.amplitude, 0, H);
        waveGrad.addColorStop(0, PALETTE.charcoalRgba(waveAlpha * 1.25));
        waveGrad.addColorStop(0.35, PALETTE.charcoalRgba(waveAlpha * 0.7));
        waveGrad.addColorStop(0.7, PALETTE.charcoalRgba(waveAlpha * 0.22));
        waveGrad.addColorStop(1, PALETTE.blackRgba(waveAlpha * 0.05));

        ctx.fillStyle = waveGrad;
        ctx.fill();

        // Shimmering golden-butter crest line highlight (#FBF5A5)
        ctx.lineWidth = 1.6;
        ctx.strokeStyle = PALETTE.paleYellowRgba(w.crestAlpha * 0.55 * globalAlpha);
        ctx.stroke();

        ctx.restore();
      }
    }

    /**
     * Render floating micro-particles / celestial dust with tech connections
     */
    renderParticles(ctx, W, H, t, globalAlpha) {
      const activeCoords = [];

      for (let i = 0; i < this.particles.length; i++) {
        const p = this.particles[i];

        // Animate upward drift
        const currentYRatio = (p.yRatio - t * p.speedY) % 1.0;
        const currentY = (currentYRatio < 0 ? currentYRatio + 1.0 : currentYRatio) * H;

        // Sinusoidal horizontal drift
        const currentX = (p.xRatio * W) + Math.sin(t * p.driftSpeed + p.seed) * (W * p.driftAmp);

        // Twinkling alpha
        const twinkle = Math.sin(t * 1.4 + p.seed) * 0.5 + 0.5;
        const alpha = p.maxAlpha * twinkle * globalAlpha;

        if (alpha > 0.01) {
          activeCoords.push({ x: currentX, y: currentY, alpha: alpha, isYellow: p.isYellow });

          ctx.beginPath();
          ctx.arc(currentX, currentY, p.radius, 0, Math.PI * 2);

          if (p.isYellow) {
            ctx.fillStyle = PALETTE.paleYellowRgba(alpha);
          } else {
            ctx.fillStyle = PALETTE.charcoalRgba(alpha * 0.85);
          }
          ctx.fill();
        }
      }

      // Constellation hairlines connecting nearby particles
      const maxConnectDist = 75;
      for (let i = 0; i < activeCoords.length; i++) {
        for (let j = i + 1; j < activeCoords.length; j++) {
          const dx = activeCoords[i].x - activeCoords[j].x;
          const dy = activeCoords[i].y - activeCoords[j].y;
          const d2 = dx * dx + dy * dy;

          if (d2 < maxConnectDist * maxConnectDist) {
            const dist = Math.sqrt(d2);
            const lineAlpha = (1 - dist / maxConnectDist) * 0.08 * globalAlpha;
            ctx.beginPath();
            ctx.moveTo(activeCoords[i].x, activeCoords[i].y);
            ctx.lineTo(activeCoords[j].x, activeCoords[j].y);
            ctx.strokeStyle = PALETTE.paleYellowRgba(lineAlpha);
            ctx.lineWidth = 0.75;
            ctx.stroke();
          }
        }
      }
    }

    /**
     * Render the two converging light streaks (matching "So" and "cio" flight)
     */
    renderLightStreaks(ctx, W, H, t, centerX, centerY) {
      const flightStart = 0.4;
      const meetTime = 2.0;

      if (t < flightStart || t > 2.8) return;

      const rawProgress = Math.min(1.0, Math.max(0.0, (t - flightStart) / (meetTime - flightStart)));
      const eased = this.easeOutQuint(rawProgress);

      // Head positions moving toward center
      const leftHeadX = eased * centerX;
      const leftHeadY = centerY + Math.sin(rawProgress * Math.PI) * (H * 0.05);

      const rightHeadX = W - eased * centerX;
      const rightHeadY = centerY - Math.sin(rawProgress * Math.PI) * (H * 0.05);

      // Fade out smoothly after meet
      let streakAlpha = Math.min(1.0, rawProgress * 3.0);
      if (t >= meetTime) {
        streakAlpha = Math.max(0.0, 1.0 - (t - meetTime) / 0.8);
      }

      // Left Inbound Streak (leading "So")
      this.drawCurvedStreak(ctx, 0, centerY - 25, leftHeadX, leftHeadY, streakAlpha, true);

      // Right Inbound Streak (leading "cio")
      this.drawCurvedStreak(ctx, W, centerY + 25, rightHeadX, rightHeadY, streakAlpha, false);
    }

    /**
     * Draw curved light streak with luminous head and tapered tail
     */
    drawCurvedStreak(ctx, startX, startY, headX, headY, alpha, isLeft) {
      if (alpha <= 0.01) return;

      ctx.save();
      const dist = Math.abs(headX - startX);
      if (dist < 4) {
        ctx.restore();
        return;
      }

      // Tapered luminous gradient using #FBF5A5
      const grad = ctx.createLinearGradient(startX, startY, headX, headY);
      grad.addColorStop(0, PALETTE.paleYellowRgba(0));
      grad.addColorStop(0.6, PALETTE.paleYellowRgba(alpha * 0.28));
      grad.addColorStop(0.9, PALETTE.paleYellowRgba(alpha * 0.75));
      grad.addColorStop(1, PALETTE.paleYellowRgba(alpha * 0.98));

      ctx.strokeStyle = grad;
      ctx.lineWidth = 2.8;
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(startX, startY);
      const ctrlX = startX + (headX - startX) * 0.5;
      const ctrlY = startY + (isLeft ? 38 : -38);
      ctx.quadraticCurveTo(ctrlX, ctrlY, headX, headY);
      ctx.stroke();

      // Radiant glow aura on streak head
      const glowR = 26;
      const headGlow = ctx.createRadialGradient(headX, headY, 1, headX, headY, glowR);
      headGlow.addColorStop(0, PALETTE.paleYellowRgba(alpha * 0.95));
      headGlow.addColorStop(0.35, PALETTE.paleYellowRgba(alpha * 0.7));
      headGlow.addColorStop(0.7, PALETTE.paleYellowRgba(alpha * 0.25));
      headGlow.addColorStop(1, PALETTE.paleYellowRgba(0));

      ctx.fillStyle = headGlow;
      ctx.beginPath();
      ctx.arc(headX, headY, glowR, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }

    /**
     * Render the center collision bloom, shockwave, and golden spark embers
     */
    renderCenterBloom(ctx, W, H, t, centerX, centerY) {
      const meetTime = 2.0;
      const delta = t - meetTime;

      // Flash & shockwave expansion in first 0.65s (2.0s -> 2.65s)
      if (delta >= 0 && delta <= 0.65) {
        const flashProgress = delta / 0.65;
        const flashAlpha = Math.max(0, 1.0 - flashProgress);

        // 1. Horizontal Anamorphic Flare Beam
        const beamW = (W * 0.62) * (0.3 + flashProgress * 0.7);
        const beamGrad = ctx.createLinearGradient(centerX - beamW, centerY, centerX + beamW, centerY);
        beamGrad.addColorStop(0, PALETTE.paleYellowRgba(0));
        beamGrad.addColorStop(0.25, PALETTE.paleYellowRgba(flashAlpha * 0.45));
        beamGrad.addColorStop(0.48, PALETTE.paleYellowRgba(flashAlpha * 0.92));
        beamGrad.addColorStop(0.5, PALETTE.paleYellowRgba(flashAlpha * 1.0));
        beamGrad.addColorStop(0.52, PALETTE.paleYellowRgba(flashAlpha * 0.92));
        beamGrad.addColorStop(0.75, PALETTE.paleYellowRgba(flashAlpha * 0.45));
        beamGrad.addColorStop(1, PALETTE.paleYellowRgba(0));

        ctx.fillStyle = beamGrad;
        ctx.fillRect(centerX - beamW, centerY - 2.5, beamW * 2, 5);

        // 2. Expanding Shockwave Rings
        const ringRadius = delta * 490;
        ctx.beginPath();
        ctx.arc(centerX, centerY, ringRadius, 0, Math.PI * 2);
        ctx.strokeStyle = PALETTE.paleYellowRgba(flashAlpha * 0.55);
        ctx.lineWidth = Math.max(1, (1.0 - flashProgress) * 3);
        ctx.stroke();

        // Secondary inner shockwave ring
        if (delta > 0.05) {
          const innerRingR = (delta - 0.05) * 320;
          ctx.beginPath();
          ctx.arc(centerX, centerY, innerRingR, 0, Math.PI * 2);
          ctx.strokeStyle = PALETTE.paleYellowRgba(flashAlpha * 0.28);
          ctx.lineWidth = 1;
          ctx.stroke();
        }

        // 3. Central Collision Core Bloom
        const coreRadius = Math.min(W, H) * 0.24;
        const coreGrad = ctx.createRadialGradient(centerX, centerY, 2, centerX, centerY, coreRadius);
        coreGrad.addColorStop(0, PALETTE.paleYellowRgba(flashAlpha * 0.75));
        coreGrad.addColorStop(0.2, PALETTE.paleYellowRgba(flashAlpha * 0.55));
        coreGrad.addColorStop(0.5, PALETTE.paleYellowRgba(flashAlpha * 0.18));
        coreGrad.addColorStop(1, PALETTE.paleYellowRgba(0));

        ctx.fillStyle = coreGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, coreRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Ambient Breathing Bloom during hold & beyond (2.0s+)
      if (delta >= 0) {
        const holdBreathe = Math.sin(delta * 0.8) * 0.15 + 0.85;
        const holdRadius = Math.min(W, H) * 0.34 * holdBreathe;

        // Hold alpha fades gently near fade end (4.0s -> 5.8s)
        let holdAlpha = 0.24;
        if (t > 4.0) {
          holdAlpha = Math.max(0.08, 0.24 * (1.0 - (t - 4.0) / 1.8));
        }

        const holdGrad = ctx.createRadialGradient(
          centerX, centerY, 4,
          centerX, centerY, holdRadius
        );
        holdGrad.addColorStop(0, PALETTE.paleYellowRgba(holdAlpha * 0.55));
        holdGrad.addColorStop(0.4, PALETTE.paleYellowRgba(holdAlpha * 0.22));
        holdGrad.addColorStop(0.75, PALETTE.charcoalRgba(holdAlpha * 0.08));
        holdGrad.addColorStop(1, PALETTE.blackRgba(0));

        ctx.fillStyle = holdGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, holdRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      // Dynamic Spark Burst (2.0s -> 3.2s)
      if (delta >= 0 && delta <= 1.2) {
        const sparkAlpha = Math.max(0, 1.0 - (delta / 1.2));
        for (let i = 0; i < this.sparks.length; i++) {
          const s = this.sparks[i];
          const dist = s.speed * this.easeOutCubic(delta / 1.2);
          const sx = centerX + Math.cos(s.angle) * dist;
          const sy = centerY + Math.sin(s.angle) * dist * 0.68; // subtle anamorphic oval

          ctx.beginPath();
          ctx.arc(sx, sy, s.size * (1 - delta / 1.2), 0, Math.PI * 2);
          ctx.fillStyle = PALETTE.paleYellowRgba(sparkAlpha * 0.75);
          ctx.fill();
        }
      }
    }
  }

  // Export to global scope
  global.LuxuryBackgroundEngine = LuxuryBackgroundEngine;
  global.SO_CIO_PALETTE = PALETTE;

})(typeof window !== 'undefined' ? window : this);
