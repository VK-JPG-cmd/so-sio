/**
 * sound.js
 * Procedural Cinematic Sound Design for So-cio using Web Audio API.
 * Synthesizes:
 * 1. Deep cinematic whoosh as "So" and "cio" approach center
 * 2. High-impact cinematic hit/thud (sub-bass + crisp metallic snap) when they meet
 * 3. Subtle ambient resonance drone during the 2-second hold
 * 4. Smooth cinematic fade-out
 */

class CinematicSoundEngine {
  constructor() {
    this.ctx = null;
    this.isMuted = false;
    this.masterGain = null;
    this.hasUserInteracted = false;
  }

  init() {
    if (this.ctx) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;

    this.ctx = new AudioContext();
    this.masterGain = this.ctx.createGain();
    this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : 0.85, this.ctx.currentTime);
    this.masterGain.connect(this.ctx.destination);
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.isMuted ? 0 : 0.85, this.ctx.currentTime, 0.05);
    }
  }

  toggleMute() {
    this.setMuted(!this.isMuted);
    return this.isMuted;
  }

  ensureContext() {
    if (!this.ctx) {
      this.init();
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  /**
   * Returns a MediaStreamAudioDestinationNode for video recording
   */
  getMediaStreamDestination() {
    this.ensureContext();
    if (!this.ctx) return null;
    if (!this.streamDest) {
      this.streamDest = this.ctx.createMediaStreamDestination();
      if (this.masterGain) {
        this.masterGain.connect(this.streamDest);
      }
    }
    return this.streamDest;
  }

  /**
   * Schedule the complete audio choreography synchronized with animation start
   * @param {number} delaySec - delay before sequence begins
   */
  playSequence(delaySec = 0) {
    if (this.isMuted) return;
    this.ensureContext();
    if (!this.ctx) return;

    const t0 = this.ctx.currentTime + delaySec;
    const meetTime = t0 + 2.2;        // Text meets at 2.2s
    const handshakeTime = t0 + 2.95;   // Light hands clasp at 2.95s
    const swirlTime = t0 + 3.8;       // Hands dissolve into swirling particles
    const logoTime = t0 + 5.2;        // Final chrome logo solidifies on pure black void
    const endTime = t0 + 8.8;

    this.scheduleWhoosh(t0 + 0.5, meetTime);
    this.scheduleImpact(handshakeTime);
    this.scheduleSwirl(swirlTime, logoTime);
    this.scheduleNetflixBoom(logoTime);
    this.scheduleGlint(logoTime);
    this.scheduleAmbientDrone(logoTime, endTime);
  }

  /**
   * Swirling vortex sound as particles orbit and converge
   */
  scheduleSwirl(startTime, endTime) {
    if (!this.ctx) return;
    const dur = endTime - startTime;
    if (dur <= 0) return;

    const bufferSize = Math.floor(this.ctx.sampleRate * dur);
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.35;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.Q.setValueAtTime(6.0, startTime);
    filter.frequency.setValueAtTime(350, startTime);
    filter.frequency.exponentialRampToValueAtTime(1800, endTime);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.001, startTime);
    gain.gain.linearRampToValueAtTime(0.2, startTime + 0.4);
    gain.gain.exponentialRampToValueAtTime(0.001, endTime + 0.1);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noise.start(startTime);
    noise.stop(endTime + 0.1);
  }

  /**
   * Blockbuster Netflix Signature "Ta-Dum" Cinematic Hit:
   * 1. "Ta": Pre-hit sub transient kick at (time - 0.12s)
   * 2. "DUM": Deep earthquake sub-bass drop (115Hz -> 28Hz) + punch transient
   * 3. Cinematic brass / cello power resonance chord (warm analog saw + lowpass)
   * 4. Shimmering chromatic harmonic overtone glint across stereo spectrum
   */
  scheduleNetflixBoom(time) {
    if (!this.ctx) return;

    // 1. "Ta" — Pre-hit punch (0.12s before main hit)
    const taTime = time - 0.12;
    const taOsc = this.ctx.createOscillator();
    taOsc.type = 'sine';
    taOsc.frequency.setValueAtTime(85, taTime);
    taOsc.frequency.exponentialRampToValueAtTime(42, taTime + 0.1);

    const taGain = this.ctx.createGain();
    taGain.gain.setValueAtTime(0.55, taTime);
    taGain.gain.exponentialRampToValueAtTime(0.001, taTime + 0.11);

    taOsc.connect(taGain);
    taGain.connect(this.masterGain);
    taOsc.start(taTime);
    taOsc.stop(taTime + 0.12);

    // 2. "DUM" — Massive Sub-Bass Cinematic Boom (Main Impact at time)
    const subOsc = this.ctx.createOscillator();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(115, time);
    subOsc.frequency.exponentialRampToValueAtTime(28, time + 0.6);

    const subGain = this.ctx.createGain();
    subGain.gain.setValueAtTime(1.0, time);
    subGain.gain.exponentialRampToValueAtTime(0.001, time + 2.2);

    subOsc.connect(subGain);
    subGain.connect(this.masterGain);
    subOsc.start(time);
    subOsc.stop(time + 2.3);

    // 3. Cinematic Cello / Brass Harmonic Body (Warm D-minor chord: D2 73Hz + A2 110Hz + F3 174Hz)
    [73.4, 110.0, 174.6].forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq, time);

      const filter = this.ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(480, time);
      filter.frequency.exponentialRampToValueAtTime(110, time + 1.8);

      const gain = this.ctx.createGain();
      const vol = 0.16 / (idx + 1);
      gain.gain.setValueAtTime(vol, time);
      gain.gain.linearRampToValueAtTime(vol * 0.9, time + 0.3);
      gain.gain.exponentialRampToValueAtTime(0.0001, time + 2.6);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);

      osc.start(time);
      osc.stop(time + 2.7);
    });

    // 4. Metallic Glint Sheen (Crystal high harmonic sweep)
    const glintNoise = this.ctx.createOscillator();
    glintNoise.type = 'triangle';
    glintNoise.frequency.setValueAtTime(2800, time);
    glintNoise.frequency.exponentialRampToValueAtTime(650, time + 0.22);

    const glintGain = this.ctx.createGain();
    glintGain.gain.setValueAtTime(0.35, time);
    glintGain.gain.exponentialRampToValueAtTime(0.001, time + 0.24);

    glintNoise.connect(glintGain);
    glintGain.connect(this.masterGain);
    glintNoise.start(time);
    glintNoise.stop(time + 0.25);
  }

  /**
   * Crystalline glint chime at final logo reveal
   */
  scheduleGlint(time) {
    [1760, 2200, 2640, 3520, 4400, 5280].forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, time);

      const gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.12 / (idx + 1), time);
      gain.gain.exponentialRampToValueAtTime(0.0001, time + 1.4);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(time);
      osc.stop(time + 1.5);
    });
  }

  /**
   * Cinematic inbound whoosh as "So" and "cio" speed inward
   */
  scheduleWhoosh(startTime, endTime) {
    const dur = endTime - startTime;
    if (dur <= 0) return;

    // Filtered noise for air rush
    const bufferSize = this.ctx.sampleRate * dur;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.Q.setValueAtTime(3.0, startTime);
    filter.frequency.setValueAtTime(120, startTime);
    filter.frequency.exponentialRampToValueAtTime(1400, endTime);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.001, startTime);
    gain.gain.exponentialRampToValueAtTime(0.35, endTime - 0.05);
    gain.gain.exponentialRampToValueAtTime(0.001, endTime + 0.05);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noise.start(startTime);
    noise.stop(endTime + 0.1);

    // Deep sub riser
    const subOsc = this.ctx.createOscillator();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(45, startTime);
    subOsc.frequency.exponentialRampToValueAtTime(90, endTime);

    const subGain = this.ctx.createGain();
    subGain.gain.setValueAtTime(0.001, startTime);
    subGain.gain.linearRampToValueAtTime(0.25, endTime - 0.1);
    subGain.gain.exponentialRampToValueAtTime(0.001, endTime + 0.05);

    subOsc.connect(subGain);
    subGain.connect(this.masterGain);

    subOsc.start(startTime);
    subOsc.stop(endTime + 0.1);
  }

  /**
   * Deep cinema sub-bass hit + crisp crystal impact snap at 2.0s
   */
  scheduleImpact(time) {
    // 1. Heavy Sub-Bass Boom (808 style movie impact)
    const subOsc = this.ctx.createOscillator();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(110, time);
    subOsc.frequency.exponentialRampToValueAtTime(32, time + 0.45);

    const subGain = this.ctx.createGain();
    subGain.gain.setValueAtTime(0.85, time);
    subGain.gain.exponentialRampToValueAtTime(0.001, time + 1.2);

    subOsc.connect(subGain);
    subGain.connect(this.masterGain);

    subOsc.start(time);
    subOsc.stop(time + 1.3);

    // 2. High-Frequency Metallic / Optical Glint Snap
    const snapOsc = this.ctx.createOscillator();
    snapOsc.type = 'triangle';
    snapOsc.frequency.setValueAtTime(2400, time);
    snapOsc.frequency.exponentialRampToValueAtTime(400, time + 0.08);

    const snapGain = this.ctx.createGain();
    snapGain.gain.setValueAtTime(0.4, time);
    snapGain.gain.exponentialRampToValueAtTime(0.001, time + 0.12);

    snapOsc.connect(snapGain);
    snapGain.connect(this.masterGain);

    snapOsc.start(time);
    snapOsc.stop(time + 0.15);
  }

  /**
   * Ambient warm harmonic drone while the logo is held center for 2 seconds
   */
  scheduleAmbientDrone(startTime, endTime) {
    const freqs = [110, 220, 330]; // Rich warm A harmonic
    freqs.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, startTime);

      const gain = this.ctx.createGain();
      const targetVol = idx === 0 ? 0.08 : 0.03;
      gain.gain.setValueAtTime(0.001, startTime);
      gain.gain.linearRampToValueAtTime(targetVol, startTime + 0.3);
      gain.gain.setValueAtTime(targetVol, endTime - 0.4);
      gain.gain.exponentialRampToValueAtTime(0.0001, endTime + 0.6);

      osc.connect(gain);
      gain.connect(this.masterGain);

      osc.start(startTime);
      osc.stop(endTime + 0.7);
    });
  }

  stopAll() {
    if (this.ctx) {
      try {
        this.ctx.close();
        this.ctx = null;
        this.masterGain = null;
      } catch (e) {
        // ignore
      }
    }
  }
}

window.cinematicAudio = new CinematicSoundEngine();
