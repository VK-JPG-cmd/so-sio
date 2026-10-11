/**
 * recorder.js
 * High-definition video export and frame capture engine for So-cio.
 * Uses Canvas 2D + MediaRecorder with 60 FPS captureStream.
 */

class LogoVideoRecorder {
  constructor(canvas, config) {
    this.canvas = canvas || document.getElementById('effectsCanvas');
    this.ctx = this.canvas.getContext('2d');
    this.config = Object.assign({
      duration: 8.8,
      fps: 60,
      width: 1920,
      height: 1080,
      fontFamily: 'Transcity',
      brandText: 'So-cio'
    }, config || {});

    this.logoImage = new Image();
    this.logoImage.src = 'socio-logo.png';

    this.bgMode = this.config.bgMode || 'lightspeed';
    this.lightspeedEngine = (typeof window !== 'undefined' && window.LightspeedEngine) ? new window.LightspeedEngine() : null;
    this.bgEngine = (typeof window !== 'undefined' && window.LuxuryBackgroundEngine) ? new window.LuxuryBackgroundEngine() : null;

    // Dedicated 1080p Handshake Engine with offscreen canvas for pristine export
    this.handshakeCanvas = document.createElement('canvas');
    this.handshakeCanvas.width = this.canvas.width;
    this.handshakeCanvas.height = this.canvas.height;
    this.handshakeEngine = (typeof window !== 'undefined' && window.CinematicHandshakeEngine)
      ? new window.CinematicHandshakeEngine(this.handshakeCanvas)
      : null;

    this.isRecording = false;
    this.mediaRecorder = null;
    this.recordedChunks = [];
    this.cancelRequested = false;
  }

  /**
   * Easing function: Quintic / Quartic ease-out for ultra-smooth cinematic motion
   */
  easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  easeOutQuint(t) {
    return 1 - Math.pow(1 - t, 5);
  }

  easeInQuad(t) {
    return t * t;
  }

  /**
   * Resolve typeface styling, weights, and metrics for Canvas rendering
   */
  getFontConfig() {
    const raw = this.config.fontFamily || 'Specimen Swash';
    let family = raw;
    let heroWeight = '900';
    let restWeight = '700';
    let style = 'normal';
    let isUppercase = false;
    let heroScale = 1.75;
    let sSpacingRatio = 0.05;

    if (raw === 'Transcity') {
      family = 'Transcity';
      heroWeight = '400';
      restWeight = '400';
      heroScale = 1.0;
      sSpacingRatio = 0;
    } else if (raw === 'Specimen Swash') {
      family = 'Cormorant Garamond';
      style = 'italic';
      heroWeight = '600';
      restWeight = '400';
    } else if (raw === 'Elsie Swash Caps') {
      family = 'Elsie Swash Caps';
      heroWeight = '900';
      restWeight = '900';
    } else if (raw === 'Cinzel Decorative') {
      family = 'Cinzel Decorative';
      heroWeight = '900';
      restWeight = '700';
    } else if (raw === 'Cinzel' || raw === 'Cinzel Classic') {
      family = 'Cinzel';
      heroWeight = '700';
      restWeight = '600';
    } else if (raw === 'Bodoni Moda') {
      family = 'Bodoni Moda';
      heroWeight = '900';
      restWeight = '700';
    } else if (raw === 'Playfair Display') {
      family = 'Playfair Display';
      style = 'italic';
      heroWeight = '800';
      restWeight = '600';
    } else if (raw === 'Cormorant Garamond') {
      family = 'Cormorant Garamond';
      style = 'italic';
      heroWeight = '600';
      restWeight = '400';
    } else if (raw === 'Prata') {
      family = 'Prata';
      heroWeight = '400';
      restWeight = '400';
    } else if (raw === 'Italiana') {
      family = 'Italiana';
      heroWeight = '400';
      restWeight = '400';
    } else if (raw === 'Abril Fatface') {
      family = 'Abril Fatface';
      heroWeight = '400';
      restWeight = '400';
    } else if (raw === 'Rozha One') {
      family = 'Rozha One';
      heroWeight = '400';
      restWeight = '400';
    } else if (raw === 'Syncopate') {
      family = 'Syncopate';
      heroWeight = '700';
      restWeight = '700';
      isUppercase = true;
      heroScale = 1.35;
    } else if (raw === 'Syne') {
      family = 'Syne';
      heroWeight = '800';
      restWeight = '700';
    } else if (raw === 'Outfit') {
      family = 'Outfit';
      heroWeight = '900';
      restWeight = '800';
    } else if (raw === 'Orbitron') {
      family = 'Orbitron';
      heroWeight = '900';
      restWeight = '800';
      heroScale = 1.5;
    } else if (raw === 'Space Grotesk') {
      family = 'Space Grotesk';
      heroWeight = '700';
      restWeight = '700';
    } else if (raw === 'Bebas Neue') {
      family = 'Bebas Neue';
      heroWeight = '400';
      restWeight = '400';
      isUppercase = true;
      heroScale = 1.45;
    } else if (raw === 'Righteous') {
      family = 'Righteous';
      heroWeight = '400';
      restWeight = '400';
    } else if (raw === 'Montserrat Black' || raw === 'Montserrat') {
      family = 'Montserrat';
      heroWeight = '900';
      restWeight = '800';
    }

    return {
      family,
      heroWeight,
      restWeight,
      style,
      isUppercase,
      heroScale,
      sSpacingRatio
    };
  }

  /**
   * Render a specific frame at time `t` (in seconds) to the canvas
   */
  renderFrameAt(t) {
    const ctx = this.ctx;
    const W = this.canvas.width;
    const H = this.canvas.height;

    // Render Luxury Animated Background (with Netflix intro blackout transition to pure black)
    const mode = this.config.bgMode || this.bgMode || 'lightspeed';
    if (t >= 5.2) {
      // Pure pitch-black void for final S logo reveal (Netflix intro aesthetic)
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, W, H);
    } else {
      let bgFade = 1.0;
      if (t >= 4.7) {
        bgFade = Math.max(0, 1.0 - (t - 4.7) / 0.5);
      }
      ctx.save();
      ctx.globalAlpha = bgFade;
      if (mode === 'lightspeed' && this.lightspeedEngine) {
        this.lightspeedEngine.renderAt(ctx, W, H, t, 0.5, 0.5, t);
      } else if (mode === 'silk' && this.bgEngine) {
        this.bgEngine.renderAt(ctx, W, H, t, 0.5, 0.5, t);
      } else if (mode === 'fusion') {
        if (this.lightspeedEngine) {
          this.lightspeedEngine.renderAt(ctx, W, H, t, 0.5, 0.5, t);
        }
        if (this.bgEngine) {
          ctx.save();
          ctx.globalCompositeOperation = 'screen';
          this.bgEngine.renderAt(ctx, W, H, t, 0.5, 0.5, t);
          ctx.restore();
        }
      } else {
        ctx.fillStyle = '#111312';
        ctx.fillRect(0, 0, W, H);
      }
      ctx.restore();

      if (bgFade < 1.0) {
        ctx.fillStyle = `rgba(0, 0, 0, ${(1.0 - bgFade).toFixed(3)})`;
        ctx.fillRect(0, 0, W, H);
      }
    }

    // Font setup: Get configured typography spec
    const fontCfg = this.getFontConfig();
    const baseScale = (this.config.fontScale || 1.25);
    const baseFontSize = H * 0.145 * baseScale;
    const isHeroScaled = (fontCfg.heroScale && fontCfg.heroScale > 1.05);
    const sFontSize = baseFontSize * (fontCfg.heroScale || 1.0);

    const heroFontString = `${fontCfg.style !== 'normal' ? fontCfg.style + ' ' : ''}${fontCfg.heroWeight} ${sFontSize}px "${fontCfg.family}", sans-serif`;
    const restFontString = `${fontCfg.style !== 'normal' ? fontCfg.style + ' ' : ''}${fontCfg.restWeight} ${baseFontSize}px "${fontCfg.family}", sans-serif`;

    const soText = fontCfg.isUppercase ? 'SO' : 'So';
    const charO = fontCfg.isUppercase ? 'O' : 'o';
    const charCio = fontCfg.isUppercase ? 'CIO' : 'cio';

    let soWidth;
    let sWidth = 0;
    let sSpacing = 0;

    if (isHeroScaled) {
      ctx.font = heroFontString;
      sWidth = ctx.measureText('S').width;
      ctx.font = restFontString;
      const oWidth = ctx.measureText(charO).width;
      sSpacing = baseFontSize * (fontCfg.sSpacingRatio !== undefined ? fontCfg.sSpacingRatio : 0);
      soWidth = sWidth + sSpacing + oWidth;
    } else {
      ctx.font = restFontString;
      soWidth = ctx.measureText(soText).width;
    }

    ctx.font = restFontString;
    const hyphenWidth = ctx.measureText('-').width;
    const cioWidth = ctx.measureText(charCio).width;
    const totalWidth = soWidth + hyphenWidth + cioWidth;

    // Calculate final resting coordinates relative to center
    const centerX = W / 2;
    const centerY = H / 2;
    const baselineY = centerY + baseFontSize * 0.35;
    
    const restSoX = centerX - totalWidth / 2;
    const restHyphenX = restSoX + soWidth;
    const restCioX = restHyphenX + hyphenWidth;

    // Keyframe Timings (6-Scene 8.8s sequence)
    const inStart = 0.5;
    const meetTime = 2.2;
    const claspTime = 2.95;
    const dissolveStart = 3.8;
    const logoTime = 5.3;

    // Determine State at time `t`
    let soOffsetX = 0;
    let cioOffsetX = 0;
    let textAlpha = 1;
    let motionBlurFactor = 0;
    let flareAlpha = 0;
    let flareScale = 0;
    let hyphenAlpha = 0;
    let shimmerProgress = -1;

    if (t < inStart) {
      // In opening beat, only ambient background is rendered; text has not yet entered
      return;
    } else if (t < meetTime) {
      // Inbound flight: So from left, cio from right
      const rawProgress = (t - inStart) / (meetTime - inStart);
      const easeProgress = this.easeOutQuint(rawProgress);

      const travelDist = W * 0.65;
      soOffsetX = -travelDist * (1 - easeProgress);
      cioOffsetX = travelDist * (1 - easeProgress);

      textAlpha = Math.min(1, rawProgress * 2.5);
      motionBlurFactor = (1 - easeProgress) * (this.config.motionBlurStrength || 28);
      hyphenAlpha = 0;
    } else if (t < dissolveStart) {
      // Meet point & Center Handshake Clasp
      soOffsetX = 0;
      cioOffsetX = 0;
      textAlpha = 1;
      hyphenAlpha = 1;

      // Optical flash trigger at clasp moment (2.95s -> 3.5s)
      if (t >= claspTime) {
        const flashDelta = t - claspTime;
        if (flashDelta < 0.55) {
          flareScale = Math.min(1, flashDelta / 0.12);
          flareAlpha = Math.max(0, 1 - (flashDelta / 0.55));
        }
      }
    } else if (t < logoTime) {
      // Dissolve into particles phase
      soOffsetX = 0;
      cioOffsetX = 0;
      hyphenAlpha = Math.max(0, 1 - (t - dissolveStart) / 0.4);
      textAlpha = Math.max(0, 1 - (t - dissolveStart) / 0.5);
    } else {
      // Logo Reveal & Hold Phase
      textAlpha = 0;
      hyphenAlpha = 0;
    }

    // 1. Draw Optical Flash & Flares (Behind/At Impact)
    if (flareAlpha > 0) {
      this.drawOpticalFlare(ctx, centerX, centerY, W, H, flareAlpha, flareScale);
    }

    // 2. Draw Ambient Central Bloom
    if (t >= meetTime && textAlpha > 0) {
      const bloomGrad = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, W * 0.4);
      bloomGrad.addColorStop(0, `rgba(251, 245, 165, ${0.08 * textAlpha})`);
      bloomGrad.addColorStop(0.5, `rgba(251, 245, 165, ${0.035 * textAlpha})`);
      bloomGrad.addColorStop(1, 'rgba(17, 19, 18, 0)');
      ctx.fillStyle = bloomGrad;
      ctx.fillRect(0, 0, W, H);
    }

    // 3. Draw Typography: Hero Capital "S" + "o" + "-" + "cio"
    ctx.save();
    ctx.textBaseline = 'alphabetic';
    ctx.fillStyle = `rgba(255, 255, 255, ${textAlpha})`;

    // "So" (from Left)
    const currentSoX = restSoX + soOffsetX;
    
    if (isHeroScaled) {
      // Draw Hero "S"
      ctx.font = heroFontString;
      if (motionBlurFactor > 1) {
        this.drawBlurredText(ctx, 'S', currentSoX, baselineY, motionBlurFactor, textAlpha, -1);
      } else {
        ctx.fillText('S', currentSoX, baselineY);
      }

      // Draw "o"
      ctx.font = restFontString;
      const oX = currentSoX + sWidth + sSpacing;
      if (motionBlurFactor > 1) {
        this.drawBlurredText(ctx, charO, oX, baselineY, motionBlurFactor, textAlpha, -1);
      } else {
        ctx.fillText(charO, oX, baselineY);
      }
    } else {
      // Draw continuous "So" with identical natural font kerning and spacing as "cio"
      ctx.font = restFontString;
      if (motionBlurFactor > 1) {
        this.drawBlurredText(ctx, soText, currentSoX, baselineY, motionBlurFactor, textAlpha, -1);
      } else {
        ctx.fillText(soText, currentSoX, baselineY);
      }
    }

    // "-" Hyphen (At Center)
    if (hyphenAlpha > 0) {
      ctx.fillStyle = `rgba(255, 255, 255, ${hyphenAlpha * textAlpha})`;
      ctx.fillText('-', restHyphenX, baselineY - baseFontSize * 0.04);
    }

    // "cio" (from Right)
    const currentCioX = restCioX + cioOffsetX;
    if (motionBlurFactor > 1) {
      this.drawBlurredText(ctx, charCio, currentCioX, baselineY, motionBlurFactor, textAlpha, 1);
    } else {
      ctx.fillStyle = `rgba(255, 255, 255, ${textAlpha})`;
      ctx.fillText(charCio, currentCioX, baselineY);
    }

    // 4. Draw Specular Light Shimmer Sweep
    if (shimmerProgress >= 0 && shimmerProgress <= 1) {
      this.drawSpecularShimmer(ctx, restSoX, centerY, totalWidth, sFontSize * 1.4, shimmerProgress);
    }

    ctx.restore();

    // 5. Draw Handshake Engine (Light Trails, Clasping Light Hands, Swirling Particles & Specular Aura)
    if (this.handshakeEngine && this.handshakeCanvas) {
      this.handshakeEngine.render(t, centerX, centerY, 1.0);
      ctx.drawImage(this.handshakeCanvas, 0, 0);
    }

    // 6. Draw Chrome S Handshake Logo on Final Reveal (t >= 5.0s -> solid by 5.3s)
    if (t >= 5.0 && this.logoImage && this.logoImage.complete) {
      const logoProg = Math.min(1, Math.max(0, (t - 5.0) / 0.35));
      ctx.save();
      ctx.globalAlpha = logoProg;
      const holdTime = t - 5.3;
      const holdProg = Math.min(1, Math.max(0, holdTime / (8.8 - 5.3)));
      // Iconic cinematic slow push-in (dolly zoom 0.94 -> 1.015)
      const dollyScale = 0.94 + 0.075 * (1 - Math.pow(1 - holdProg, 2));
      const glowPulse = 0.38 + (holdTime > 0 ? Math.sin(holdTime * 1.5) * 0.08 : 0);
      ctx.shadowColor = '#FBF5A5';
      ctx.shadowBlur = (26 + glowPulse * 14) * logoProg;
      const lSize = 350 * dollyScale; // Refined, slightly smaller Netflix-proportion size
      ctx.drawImage(this.logoImage, centerX - lSize / 2, centerY - lSize / 2, lSize, lSize);
      ctx.restore();
    }
  }

  /**
   * Draw directional horizontal motion blur
   */
  drawBlurredText(ctx, text, x, y, blurFactor, alpha, direction) {
    const steps = 7;
    const stepDist = (blurFactor * 3.5) / steps;
    const stepAlpha = (alpha / steps) * 1.3;

    for (let i = 0; i < steps; i++) {
      const offset = (i - steps / 2) * stepDist;
      ctx.fillStyle = `rgba(255, 255, 255, ${stepAlpha})`;
      ctx.fillText(text, x + offset, y);
    }
    // Center pass
    ctx.fillStyle = `rgba(255, 255, 255, ${alpha * 0.7})`;
    ctx.fillText(text, x, y);
  }

  /**
   * Draw horizontal anamorphic optical lens flare beam and radial halo
   */
  drawOpticalFlare(ctx, cx, cy, W, H, alpha, scale) {
    ctx.save();
    const flareIntensity = this.config.flareIntensity || 1.0;
    const effAlpha = Math.min(1, alpha * flareIntensity);

    // Horizontal Anamorphic Beam
    const beamLength = (W * 0.85) * scale;
    const beamGrad = ctx.createLinearGradient(cx - beamLength / 2, cy, cx + beamLength / 2, cy);
    beamGrad.addColorStop(0, 'rgba(251, 245, 165, 0)');
    beamGrad.addColorStop(0.3, `rgba(251, 245, 165, ${0.45 * effAlpha})`);
    beamGrad.addColorStop(0.5, `rgba(251, 245, 165, ${0.98 * effAlpha})`);
    beamGrad.addColorStop(0.7, `rgba(251, 245, 165, ${0.45 * effAlpha})`);
    beamGrad.addColorStop(1, 'rgba(251, 245, 165, 0)');

    ctx.fillStyle = beamGrad;
    ctx.fillRect(cx - beamLength / 2, cy - 3, beamLength, 6);

    // Core Flash Halo
    const haloRadius = 140 * scale;
    const haloGrad = ctx.createRadialGradient(cx, cy, 0, cx, cy, haloRadius);
    haloGrad.addColorStop(0, `rgba(251, 245, 165, ${0.95 * effAlpha})`);
    haloGrad.addColorStop(0.35, `rgba(251, 245, 165, ${0.5 * effAlpha})`);
    haloGrad.addColorStop(0.7, `rgba(251, 245, 165, ${0.15 * effAlpha})`);
    haloGrad.addColorStop(1, 'rgba(17, 19, 18, 0)');

    ctx.fillStyle = haloGrad;
    ctx.beginPath();
    ctx.arc(cx, cy, haloRadius, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  }

  /**
   * Draw luxury specular metallic shimmer pass across text
   */
  drawSpecularShimmer(ctx, startX, y, width, height, progress) {
    ctx.save();
    ctx.globalCompositeOperation = 'source-atop';

    const shimmerX = startX + width * (progress * 1.6 - 0.3);
    const grad = ctx.createLinearGradient(shimmerX - 80, y, shimmerX + 80, y);
    grad.addColorStop(0, 'rgba(251, 245, 165, 0)');
    grad.addColorStop(0.5, 'rgba(251, 245, 165, 0.7)');
    grad.addColorStop(1, 'rgba(251, 245, 165, 0)');

    ctx.fillStyle = grad;
    ctx.fillRect(startX - 20, y - height / 2, width + 40, height);
    ctx.restore();
  }

  /**
   * Start 60 FPS Video Recording and export as WebM/MP4
   */
  /**
   * Start 60 FPS Video Recording with Synchronized Audio and export as WebM/MP4
   */
  async exportVideo(onProgress, onComplete, onError) {
    if (this.isRecording) return;
    this.isRecording = true;
    this.cancelRequested = false;

    // Ensure fonts loaded
    if (document.fonts) {
      await document.fonts.ready;
    }

    // Ensure logo image loaded
    if (this.logoImage && !this.logoImage.complete) {
      await new Promise(resolve => {
        this.logoImage.onload = resolve;
        this.logoImage.onerror = resolve;
      });
    }

    const fps = this.config.fps || 60;
    const duration = this.config.duration || 8.8;
    const totalFrames = Math.ceil(duration * fps);

    // Setup canvas capture stream
    let stream;
    try {
      stream = this.canvas.captureStream(fps);
    } catch (e) {
      this.isRecording = false;
      if (onError) onError(e);
      return;
    }

    // Attach synchronized audio track if Web Audio engine is available
    if (window.cinematicAudio) {
      try {
        const audioDest = window.cinematicAudio.getMediaStreamDestination();
        if (audioDest && audioDest.stream) {
          const audioTracks = audioDest.stream.getAudioTracks();
          if (audioTracks.length > 0) {
            stream.addTrack(audioTracks[0]);
          }
        }
      } catch (err) {
        console.warn('Audio stream attachment warning:', err);
      }
    }

    const mimeTypes = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8,opus',
      'video/webm;codecs=vp8',
      'video/webm',
      'video/mp4'
    ];
    let selectedMime = mimeTypes.find(m => MediaRecorder.isTypeSupported(m)) || 'video/webm';

    this.recordedChunks = [];
    try {
      this.mediaRecorder = new MediaRecorder(stream, {
        mimeType: selectedMime,
        videoBitsPerSecond: 14000000 // 14 Mbps pristine master quality
      });
    } catch (err) {
      this.isRecording = false;
      if (onError) onError(err);
      return;
    }

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        this.recordedChunks.push(e.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      this.isRecording = false;
      if (this.cancelRequested) return;

      const ext = selectedMime.includes('mp4') ? 'mp4' : 'webm';
      const blob = new Blob(this.recordedChunks, { type: selectedMime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `So-cio-cinematic-intro-${Date.now()}.${ext}`;
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }, 2000);

      if (onComplete) onComplete(blob);
    };

    // Trigger synchronized audio sequence
    if (window.cinematicAudio) {
      window.cinematicAudio.playSequence(0.0);
    }

    this.mediaRecorder.start();

    // Render frames sequentially with drift compensation
    let currentFrame = 0;
    const frameInterval = 1000 / fps;
    const startTime = performance.now();

    const renderLoop = () => {
      if (this.cancelRequested) {
        if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
          this.mediaRecorder.stop();
        }
        this.isRecording = false;
        return;
      }

      const t = currentFrame / fps;
      this.renderFrameAt(t);

      currentFrame++;
      const percent = Math.min(100, Math.round((currentFrame / totalFrames) * 100));
      if (onProgress) onProgress(currentFrame, totalFrames, percent);

      if (currentFrame <= totalFrames) {
        const targetTime = startTime + (currentFrame * frameInterval);
        const delay = Math.max(0, targetTime - performance.now());
        setTimeout(renderLoop, delay);
      } else {
        setTimeout(() => {
          if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
            this.mediaRecorder.stop();
          }
        }, 300);
      }
    };

    renderLoop();
  }

  cancelExport() {
    this.cancelRequested = true;
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      this.mediaRecorder.stop();
    }
    this.isRecording = false;
  }

  /**
   * Capture pristine single PNG frame (defaults to final 4K chrome logo hold at 6.2s)
   */
  capturePng(timeSec = null) {
    const captureT = timeSec !== null ? timeSec : 6.2;
    this.renderFrameAt(captureT);
    const dataUrl = this.canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = `So-cio-Logo-4K-${Date.now()}.png`;
    document.body.appendChild(a);
    a.click();
    setTimeout(() => document.body.removeChild(a), 1000);
  }
}

window.LogoVideoRecorder = LogoVideoRecorder;
