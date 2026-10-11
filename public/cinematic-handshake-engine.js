/**
 * cinematic-handshake-engine.js
 * High-performance Canvas 2D engine driving:
 * 1. Scene 2 & 3: Pale-yellow (#FBF5A5) light trails & particle comets revealing "So" & "cio"
 * 2. Scene 4: Two futuristic glowing light hands emerging from trails, performing a realistic handshake & pulse
 * 3. Scene 5: Hands & text dissolving into ~1,000 glowing particles, swirling in a vortex and assembling into the exact chrome S logo
 * 4. Scene 6: Specular light aura settling on final logo
 *
 * Color Palette: Deep black #111312, Charcoal grey #434346, Pale yellow #FBF5A5
 */

class CinematicHandshakeEngine {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas ? canvas.getContext('2d') : null;
    
    // Exact color tokens
    this.COLOR_BG = '#111312';
    this.COLOR_CHARCOAL = '#434346';
    this.COLOR_PALE_YELLOW = '#FBF5A5';
    this.COLOR_GLOW_LIGHT = 'rgba(251, 245, 165, 0.85)';
    this.COLOR_GLOW_SOFT = 'rgba(251, 245, 165, 0.22)';
    this.COLOR_CHARCOAL_ACCENT = 'rgba(67, 67, 70, 0.6)';

    // Logo image & target pixel cloud
    this.logoImage = null;
    this.logoLoaded = false;
    this.targetPoints = []; // [{ x, y, brightness, alpha }]
    this.particles = [];    // Array of active transition particles
    this.numParticles = 900;
    
    // Trail spark particles
    this.trailParticlesLeft = [];
    this.trailParticlesRight = [];

    // Clasp ripple waves
    this.shockwaves = [];

    this.initLogoSampling('socio-logo.png');
  }

  /**
   * Pre-sample the transparent PNG logo to get target particle coordinates
   */
  initLogoSampling(src) {
    this.logoImage = new Image();
    this.logoImage.crossOrigin = 'anonymous';
    this.logoImage.src = src;
    this.logoImage.onload = () => {
      this.logoLoaded = true;
      this.extractLogoPoints();
    };
  }

  extractLogoPoints() {
    if (!this.logoImage) return;
    const offCanvas = document.createElement('canvas');
    const sampleSize = 160;
    offCanvas.width = sampleSize;
    offCanvas.height = sampleSize;
    const offCtx = offCanvas.getContext('2d');
    offCtx.drawImage(this.logoImage, 0, 0, sampleSize, sampleSize);
    
    const imgData = offCtx.getImageData(0, 0, sampleSize, sampleSize).data;
    const validPoints = [];

    for (let y = 0; y < sampleSize; y += 2) {
      for (let x = 0; x < sampleSize; x += 2) {
        const idx = (y * sampleSize + x) * 4;
        const a = imgData[idx + 3];
        const r = imgData[idx];
        const g = imgData[idx + 1];
        const b = imgData[idx + 2];
        const brightness = (r + g + b) / (3 * 255);

        if (a > 50 && brightness > 0.08) {
          validPoints.push({
            normX: (x - sampleSize / 2) / (sampleSize / 2), // -1 to +1
            normY: (y - sampleSize / 2) / (sampleSize / 2), // -1 to +1
            brightness: brightness,
            alpha: a / 255
          });
        }
      }
    }

    // Shuffle and pick target points
    this.targetPoints = [];
    if (validPoints.length > 0) {
      for (let i = 0; i < this.numParticles; i++) {
        const randPt = validPoints[Math.floor(Math.random() * validPoints.length)];
        this.targetPoints.push(randPt);
      }
    }

    this.initParticles();
  }

  initParticles() {
    this.particles = [];
    for (let i = 0; i < this.numParticles; i++) {
      const target = this.targetPoints[i] || { normX: 0, normY: 0, brightness: 1, alpha: 1 };
      // Random starting angle and radius around center
      const angle = Math.random() * Math.PI * 2;
      const dist = 30 + Math.random() * 220;
      this.particles.push({
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        vx: (Math.random() - 0.5) * 6,
        vy: (Math.random() - 0.5) * 6,
        normX: target.normX,
        normY: target.normY,
        brightness: target.brightness,
        size: 1.2 + Math.random() * 2.2,
        phase: Math.random() * Math.PI * 2,
        speedFactor: 0.8 + Math.random() * 0.4
      });
    }
  }

  /**
   * Main render call for the current animation time (0.0s - 8.8s)
   */
  render(t, cx, cy, scale = 1.0) {
    if (!this.ctx || !this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.width;
    const h = this.canvas.height;
    if (!cx) cx = w / 2;
    if (!cy) cy = h / 2;

    ctx.clearRect(0, 0, w, h);

    // =========================================================================
    // SCENE 2 & 3: Light Trails for "So" and "cio" (0.5s <= t < 2.2s)
    // =========================================================================
    if (t >= 0.5 && t < 2.2) {
      this.renderLightTrails(t, cx, cy, scale);
    }

    // =========================================================================
    // SCENE 4: Minimalist Radiant Light Dot Touching (2.15s <= t < 3.85s)
    // =========================================================================
    if (t >= 2.15 && t < 3.85) {
      this.renderLightDotTouching(t, cx, cy, scale);
    }

    // =========================================================================
    // SCENE 5: Swirling Particle Vortex & Logo Assembly (3.8s <= t < 5.6s)
    // =========================================================================
    if (t >= 3.75 && t < 5.65) {
      this.renderParticleSwirlAndAssembly(t, cx, cy, scale);
    }

    // =========================================================================
    // SCENE 6: Ambient Specular Glow on Final Logo (5.5s <= t <= 9.0s)
    // =========================================================================
    if (t >= 5.5) {
      this.renderFinalLogoGlow(t, cx, cy, scale);
    }
  }

  // ===========================================================================
  // SCENE 2 & 3: Inbound Light Trails
  // ===========================================================================
  renderLightTrails(t, cx, cy, scale) {
    const ctx = this.ctx;
    const progress = Math.min(1, Math.max(0, (t - 0.5) / 1.7));
    const ease = 1 - Math.pow(1 - progress, 5); // easeOutQuint
    
    // Head positions moving toward center
    const leftHeadX = cx - (1 - ease) * (cx * 1.1);
    const rightHeadX = cx + (1 - ease) * (cx * 1.1);
    const headY = cy;

    ctx.save();
    
    // Draw left comet trail (#FBF5A5)
    this.drawCometRibbon(ctx, leftHeadX, headY, -1, ease * scale);
    // Draw right comet trail (#FBF5A5)
    this.drawCometRibbon(ctx, rightHeadX, headY, 1, ease * scale);

    ctx.restore();
  }

  drawCometRibbon(ctx, headX, headY, direction, intensity) {
    const trailLen = 320 * intensity;
    const tailX = headX - direction * trailLen;

    // Glowing comet tail gradient
    const grad = ctx.createLinearGradient(tailX, headY, headX, headY);
    grad.addColorStop(0, 'rgba(251, 245, 165, 0)');
    grad.addColorStop(0.6, 'rgba(67, 67, 70, 0.35)'); // charcoal depth
    grad.addColorStop(0.85, 'rgba(251, 245, 165, 0.7)');
    grad.addColorStop(1, '#FBF5A5');

    ctx.strokeStyle = grad;
    ctx.lineWidth = 4 * intensity;
    ctx.lineCap = 'round';

    ctx.beginPath();
    ctx.moveTo(tailX, headY);
    // Subtle wavy stream
    ctx.quadraticCurveTo(headX - direction * 60, headY + direction * 4, headX, headY);
    ctx.stroke();

    // Outer glow aura around comet head
    const glowRadius = 24 * intensity;
    const headGrad = ctx.createRadialGradient(headX, headY, 0, headX, headY, glowRadius);
    headGrad.addColorStop(0, 'rgba(251, 245, 165, 0.95)');
    headGrad.addColorStop(0.4, 'rgba(251, 245, 165, 0.45)');
    headGrad.addColorStop(1, 'rgba(251, 245, 165, 0)');

    ctx.fillStyle = headGrad;
    ctx.beginPath();
    ctx.arc(headX, headY, glowRadius, 0, Math.PI * 2);
    ctx.fill();

    // Spark particles behind comet
    for (let i = 0; i < 4; i++) {
      const sparkDist = Math.random() * trailLen * 0.7;
      const sx = headX - direction * sparkDist;
      const sy = headY + (Math.random() - 0.5) * 16;
      ctx.fillStyle = 'rgba(251, 245, 165, ' + (0.3 + Math.random() * 0.5) + ')';
      ctx.beginPath();
      ctx.arc(sx, sy, 1.2 + Math.random() * 1.5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // ===========================================================================
  // SCENE 4: Minimalist Radiant Light Dot Touching (2.15s <= t < 3.85s)
  // Two luminous dots glide inward and touch at the center hyphen point,
  // releasing an anamorphic optical streak, delicate ripple, and radiant core spark.
  // ===========================================================================
  renderLightDotTouching(t, cx, cy, scale) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(cx, cy);

    const contactTime = 2.85;
    const sceneEnd = 3.85;

    // Overall scene alpha fade
    let alpha = 1.0;
    if (t < 2.3) {
      alpha = Math.max(0, (t - 2.15) / 0.15);
    } else if (t > 3.65) {
      alpha = Math.max(0, 1 - (t - 3.65) / 0.2);
    }

    if (t < contactTime) {
      // -----------------------------------------------------------------------
      // Stage A: Two light dots glide inward towards the center (2.15s -> 2.85s)
      // -----------------------------------------------------------------------
      const inProg = Math.min(1, Math.max(0, (t - 2.15) / (contactTime - 2.15)));
      const ease = 1 - Math.pow(1 - inProg, 3); // easeOutCubic
      const dist = (1 - ease) * 190 * scale;

      // Left Dot (advancing from "So")
      this.drawLuminousDot(ctx, -dist, 0, alpha * scale, true);

      // Right Dot (advancing from "cio")
      this.drawLuminousDot(ctx, dist, 0, alpha * scale, false);
    } else {
      // -----------------------------------------------------------------------
      // Stage B: The Touch Moment & Unified Radiant Dot (2.85s -> 3.85s)
      // -----------------------------------------------------------------------
      const dt = t - contactTime;

      // Contact shockwave ripple (2.85s -> 3.35s)
      if (dt < 0.5) {
        const rippleProg = dt / 0.5;
        const rippleRadius = (20 + rippleProg * 140) * scale;
        const rippleAlpha = (1 - rippleProg) * 0.75 * alpha;

        ctx.strokeStyle = `rgba(251, 245, 165, ${rippleAlpha})`;
        ctx.lineWidth = Math.max(0.5, (1 - rippleProg) * 2.8);
        ctx.beginPath();
        ctx.arc(0, 0, rippleRadius, 0, Math.PI * 2);
        ctx.stroke();

        // Secondary subtle inner ripple
        if (rippleProg > 0.15) {
          const innerProg = (rippleProg - 0.15) / 0.85;
          ctx.strokeStyle = `rgba(251, 245, 165, ${(1 - innerProg) * 0.45 * alpha})`;
          ctx.lineWidth = 1.0;
          ctx.beginPath();
          ctx.arc(0, 0, (10 + innerProg * 90) * scale, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      // High-end Anamorphic Lens Flare Horizontal Streak
      // Creates that blockbuster cinematic widescreen beam
      const flareProg = Math.min(1, dt / 0.65);
      const flareWidth = (dt < 0.12 ? (dt / 0.12) * 160 : 160 - Math.min(70, (dt - 0.12) * 80)) * scale;
      const flareAlpha = (dt < 0.12 ? 0.95 : Math.max(0.35, 0.95 - (dt - 0.12) * 0.9)) * alpha;

      const streakGrad = ctx.createLinearGradient(-flareWidth, 0, flareWidth, 0);
      streakGrad.addColorStop(0, 'rgba(251, 245, 165, 0)');
      streakGrad.addColorStop(0.3, 'rgba(251, 245, 165, 0.25)');
      streakGrad.addColorStop(0.48, `rgba(255, 255, 255, ${flareAlpha})`);
      streakGrad.addColorStop(0.5, '#FFFFFF');
      streakGrad.addColorStop(0.52, `rgba(255, 255, 255, ${flareAlpha})`);
      streakGrad.addColorStop(0.7, 'rgba(251, 245, 165, 0.25)');
      streakGrad.addColorStop(1, 'rgba(251, 245, 165, 0)');

      ctx.fillStyle = streakGrad;
      ctx.fillRect(-flareWidth, -1.2, flareWidth * 2, 2.4);

      // Micro stardust sparkle bursts (first 0.3s after contact)
      if (dt < 0.35) {
        const sparkProg = dt / 0.35;
        const sparkCount = 10;
        for (let i = 0; i < sparkCount; i++) {
          const angle = (i / sparkCount) * Math.PI * 2 + 0.3;
          const sDist = (8 + sparkProg * 45 * (0.8 + 0.4 * Math.sin(i * 4))) * scale;
          const sx = Math.cos(angle) * sDist;
          const sy = Math.sin(angle) * sDist * 0.6; // slight horizontal ellipse
          ctx.fillStyle = `rgba(251, 245, 165, ${(1 - sparkProg) * 0.8 * alpha})`;
          ctx.beginPath();
          ctx.arc(sx, sy, 1.2 * (1 - sparkProg * 0.5), 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // Breathing unified central light dot
      const breath = 1.0 + 0.12 * Math.sin(dt * 5.5);
      const dotRadius = 4.2 * scale * breath;
      const glowRadius = 24 * scale * breath;

      // Soft diffuse halo
      const haloGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, glowRadius);
      haloGrad.addColorStop(0, `rgba(251, 245, 165, ${0.75 * alpha})`);
      haloGrad.addColorStop(0.4, `rgba(251, 245, 165, ${0.28 * alpha})`);
      haloGrad.addColorStop(1, 'rgba(251, 245, 165, 0)');

      ctx.fillStyle = haloGrad;
      ctx.beginPath();
      ctx.arc(0, 0, glowRadius, 0, Math.PI * 2);
      ctx.fill();

      // Sharp jewel-like luminous core dot
      ctx.shadowColor = '#FBF5A5';
      ctx.shadowBlur = 12;
      ctx.fillStyle = '#FFFFFF';
      ctx.beginPath();
      ctx.arc(0, 0, dotRadius, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    }

    ctx.restore();
  }

  /**
   * Helper to draw an individual approaching luminous dot with subtle trailing aura
   */
  drawLuminousDot(ctx, x, y, alpha, isLeft) {
    if (alpha <= 0.01) return;

    // Whispering tail trailing behind movement direction
    const tailDir = isLeft ? -1 : 1;
    const tailLen = 35;
    const tailGrad = ctx.createLinearGradient(x + tailDir * tailLen, y, x, y);
    tailGrad.addColorStop(0, 'rgba(251, 245, 165, 0)');
    tailGrad.addColorStop(1, `rgba(251, 245, 165, ${0.45 * alpha})`);

    ctx.strokeStyle = tailGrad;
    ctx.lineWidth = 2.0;
    ctx.beginPath();
    ctx.moveTo(x + tailDir * tailLen, y);
    ctx.lineTo(x, y);
    ctx.stroke();

    // Outer glow
    const glowGrad = ctx.createRadialGradient(x, y, 0, x, y, 16);
    glowGrad.addColorStop(0, `rgba(251, 245, 165, ${0.65 * alpha})`);
    glowGrad.addColorStop(0.5, `rgba(251, 245, 165, ${0.2 * alpha})`);
    glowGrad.addColorStop(1, 'rgba(251, 245, 165, 0)');

    ctx.fillStyle = glowGrad;
    ctx.beginPath();
    ctx.arc(x, y, 16, 0, Math.PI * 2);
    ctx.fill();

    // Dot core
    ctx.shadowColor = '#FBF5A5';
    ctx.shadowBlur = 8;
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.arc(x, y, 3.2, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  // ===========================================================================
  // SCENE 5: Swirling Particle Vortex & Transition into Logo
  // ===========================================================================
  renderParticleSwirlAndAssembly(t, cx, cy, scale) {
    const ctx = this.ctx;
    ctx.save();

    // Timing of Scene 5 (3.8s to 5.5s):
    // 3.8s - 4.4s: Hands dissolve, particles burst out into orbital swirl vortex
    // 4.4s - 5.1s: Swirling particles are magnetically pulled into the exact logo shape
    // 5.1s - 5.5s: Particles assemble tightly, locking into place, and logo solidifies
    const dissolveStart = 3.8;
    const assembleStart = 4.4;
    const lockTime = 5.2;
    const sceneEnd = 5.6;

    const dt = t - dissolveStart; // 0..1.8s
    const totalDuration = sceneEnd - dissolveStart;
    const sceneProg = Math.min(1, Math.max(0, dt / totalDuration));

    // Logo render size on stage (refined Netflix proportions ~350px)
    const logoHeight = 350 * scale;
    const logoWidth = logoHeight; // square logo aspect ratio

    ctx.translate(cx, cy);

    // Particle Swirl physics & convergence
    const isSwirlPhase = t < assembleStart;
    const assembleProg = Math.min(1, Math.max(0, (t - assembleStart) / (lockTime - assembleStart)));
    const assembleEase = 1 - Math.pow(1 - assembleProg, 4); // easeOutQuart

    // Global vortex rotation
    const globalAngle = dt * 2.8;

    ctx.shadowBlur = 10;
    ctx.shadowColor = '#FBF5A5';

    for (let i = 0; i < this.particles.length; i++) {
      const p = this.particles[i];
      const targetX = p.normX * (logoWidth * 0.48);
      const targetY = p.normY * (logoHeight * 0.48);

      let currentX, currentY, alpha, size;

      if (t < assembleStart) {
        // Phase 1: Dynamic orbital swirl vortex around center
        const swirlT = (t - dissolveStart) / (assembleStart - dissolveStart);
        const radius = (40 + (i % 120) * 2.2) * (1 + Math.sin(swirlT * Math.PI) * 0.6);
        const theta = p.phase + globalAngle * p.speedFactor + (i * 0.02);
        
        currentX = Math.cos(theta) * radius;
        currentY = Math.sin(theta) * radius * 0.75; // slight oval tilt
        alpha = Math.min(1, swirlT * 3.0);
        size = p.size * (1 + (1 - swirlT) * 0.5);
      } else {
        // Phase 2: Magnetically converge onto exact logo coordinates
        const swirlRadius = (40 + (i % 120) * 1.5);
        const theta = p.phase + globalAngle * p.speedFactor + (i * 0.02);
        const swirlX = Math.cos(theta) * swirlRadius;
        const swirlY = Math.sin(theta) * swirlRadius * 0.75;

        currentX = swirlX * (1 - assembleEase) + targetX * assembleEase;
        currentY = swirlY * (1 - assembleEase) + targetY * assembleEase;
        
        // As they lock into place, brightness matches the logo brightness
        alpha = 0.5 + p.brightness * 0.5;
        if (t > lockTime) {
          // Particles smoothly fade out as high-res chrome image takes over
          const fadeOut = Math.max(0, 1 - (t - lockTime) / (sceneEnd - lockTime));
          alpha *= fadeOut;
        }
        size = p.size * (1 - assembleEase * 0.35);
      }

      // Draw particle with pale-yellow / metallic core
      ctx.fillStyle = p.brightness > 0.6
        ? `rgba(251, 245, 165, ${alpha.toFixed(2)})`
        : `rgba(67, 67, 70, ${(alpha * 0.8).toFixed(2)})`;

      ctx.beginPath();
      ctx.arc(currentX, currentY, Math.max(0.6, size), 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.restore();
  }

  // ===========================================================================
  // SCENE 6: Ambient Glow on Final Logo
  // ===========================================================================
  renderFinalLogoGlow(t, cx, cy, scale) {
    const ctx = this.ctx;
    ctx.save();
    ctx.translate(cx, cy);

    // Subtle breathing pulse (3 seconds hold)
    const holdTime = t - 5.5;
    const breath = 0.12 + Math.sin(holdTime * 1.4) * 0.05;

    // Soft pale-yellow radial aura behind the chrome logo (restrained for pure black void)
    const auraRadius = 200 * scale;
    const grad = ctx.createRadialGradient(0, 0, 30, 0, 0, auraRadius);
    grad.addColorStop(0, `rgba(251, 245, 165, ${breath * 0.55})`);
    grad.addColorStop(0.5, `rgba(67, 67, 70, ${breath * 0.15})`);
    grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(0, 0, auraRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }
}

// Export to window
if (typeof window !== 'undefined') {
  window.CinematicHandshakeEngine = CinematicHandshakeEngine;
}
