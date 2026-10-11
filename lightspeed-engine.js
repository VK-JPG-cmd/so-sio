/**
 * lightspeed-engine.js
 * High-performance WebGL & Canvas implementation of the React Bits Pro "Lightspeed" component.
 * "A hyperspace jump of streaking stars"
 *
 * Strict Luxury Palette:
 * - Deep black:        #111312
 * - Charcoal grey:     #434346
 * - Pale butter yellow: #FBF5A5
 */

(function (global) {
  'use strict';

  // Palette constants
  const PALETTE = {
    deepBlack: { r: 17 / 255, g: 19 / 255, b: 18 / 255, hex: '#111312' },
    charcoal: { r: 67 / 255, g: 67 / 255, b: 70 / 255, hex: '#434346' },
    butterYellow: { r: 251 / 255, g: 245 / 255, b: 165 / 255, hex: '#FBF5A5' }
  };

  const VS_SOURCE = `
    attribute vec2 aPosition;
    void main() {
      gl_Position = vec4(aPosition, 0.0, 1.0);
    }
  `;

  const FS_SOURCE = `
    precision highp float;

    #define PI 3.14159265359

    uniform float iTime;
    uniform vec2 iResolution;
    uniform vec4 iMouse;
    uniform float uCompression;
    uniform vec3 uColor1;
    uniform vec3 uColor2;
    uniform vec3 uColor3;
    uniform float uStreakCount;
    uniform float uStretchFactor;
    uniform float uIntensity;
    uniform float uSpeed;
    uniform float uRotation;
    uniform float uFadePower;
    uniform float uOpacity;

    float computeStreak(vec2 coord, float timeOffset) {
      coord.x = coord.x * uStreakCount;
      float horizontalPos = fract(coord.x);
      float columnIndex = floor(coord.x);

      coord.y *= uStretchFactor;

      float randomOffset = sin(columnIndex * 215.4);
      float speedVariation = cos(columnIndex * 33.1) * 0.3 + 0.7;
      float dynamicTrail = mix(95.0, 35.0, speedVariation);

      float animatedY = fract(coord.y + timeOffset * speedVariation + randomOffset);
      float streakValue = animatedY * dynamicTrail;

      if (streakValue <= 0.0001) return 0.0;
      streakValue = 1.0 / streakValue;
      streakValue = smoothstep(0.0, 1.0, streakValue * streakValue);
      streakValue = sin(clamp(streakValue, 0.0, 1.0) * PI) * (speedVariation * 5.0);

      float horizontalFalloff = sin(horizontalPos * PI);
      return streakValue * (horizontalFalloff * horizontalFalloff);
    }

    void main() {
      vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution) / iResolution.y;

      // Mouse influence for subtle parallax tunnel steering
      vec2 mouseShift = (iMouse.xy / iResolution.xy - 0.5) * 0.25;
      uv -= mouseShift;

      float distFromCenter = length(uv) + 0.08;

      float angle = atan(uv.x, uv.y) / PI + uRotation;
      float radius = 2.5 / distFromCenter;
      vec2 polarCoord = vec2(angle, radius);

      float compressionFactor = mix(1.0, 0.45, clamp(uCompression, 0.0, 1.0));
      polarCoord.y *= compressionFactor;

      float animTime = iTime * 0.42 * uSpeed;

      vec3 streaks = vec3(0.0);
      streaks += uColor1 * computeStreak(polarCoord, animTime);
      streaks += uColor2 * computeStreak(polarCoord, animTime + 0.33);
      streaks += uColor3 * computeStreak(polarCoord, animTime + 0.66);

      streaks *= uIntensity;
      float distanceFade = pow(distFromCenter, uFadePower);
      streaks *= distanceFade;
      streaks *= uOpacity;

      // Deep Black luxury foundation #111312
      vec3 bg = vec3(17.0 / 255.0, 19.0 / 255.0, 18.0 / 255.0);
      vec3 finalColor = bg + streaks;

      gl_FragColor = vec4(finalColor, 1.0);
    }
  `;

  class LightspeedEngine {
    constructor(options = {}) {
      this.speed = options.speed !== undefined ? options.speed : 1.15;
      this.streakCount = options.streakCount !== undefined ? options.streakCount : 128;
      this.stretchFactor = options.stretchFactor !== undefined ? options.stretchFactor : 0.052;
      this.intensity = options.intensity !== undefined ? options.intensity : 1.25;
      this.fadePower = options.fadePower !== undefined ? options.fadePower : 1.85;
      this.rotation = options.rotation !== undefined ? options.rotation : 0.0;
      this.opacity = options.opacity !== undefined ? options.opacity : 1.0;
      this.compression = 0.0;
      this.targetCompression = 0.0;

      // Primary color: Pale butter yellow #FBF5A5
      this.color1 = options.color1 || PALETTE.butterYellow;
      // Secondary color: Charcoal grey #434346
      this.color2 = options.color2 || PALETTE.charcoal;
      // Tertiary color: Pale yellow #FBF5A5
      this.color3 = options.color3 || PALETTE.butterYellow;

      // Internal offscreen WebGL renderer
      this.offscreenCanvas = document.createElement('canvas');
      this.gl = this.offscreenCanvas.getContext('webgl', {
        alpha: false,
        antialias: false,
        depth: false,
        stencil: false,
        powerPreference: 'high-performance',
        preserveDrawingBuffer: true
      });

      this.program = null;
      this.locations = null;
      this.quadBuffer = null;

      if (this.gl) {
        this.initWebGL();
      } else {
        console.warn('WebGL unavailable, Lightspeed falling back to Canvas2D particles.');
        this.initFallback2D();
      }

      this.bindInteraction();
    }

    initWebGL() {
      const gl = this.gl;

      const compileShader = (type, source) => {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
          console.error('Lightspeed Shader error:', gl.getShaderInfoLog(shader));
          gl.deleteShader(shader);
          return null;
        }
        return shader;
      };

      const vs = compileShader(gl.VERTEX_SHADER, VS_SOURCE);
      const fs = compileShader(gl.FRAGMENT_SHADER, FS_SOURCE);
      if (!vs || !fs) return;

      const program = gl.createProgram();
      gl.attachShader(program, vs);
      gl.attachShader(program, fs);
      gl.linkProgram(program);

      if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
        console.error('Lightspeed Program link error:', gl.getProgramInfoLog(program));
        return;
      }

      this.program = program;
      gl.useProgram(program);

      // Attribute
      const aPosition = gl.getAttribLocation(program, 'aPosition');
      this.quadBuffer = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, this.quadBuffer);
      const vertices = new Float32Array([
        -1.0, -1.0,
         1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
         1.0, -1.0,
         1.0,  1.0
      ]);
      gl.bufferData(gl.ARRAY_BUFFER, vertices, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(aPosition);
      gl.vertexAttribPointer(aPosition, 2, gl.FLOAT, false, 0, 0);

      // Uniforms
      this.locations = {
        iTime: gl.getUniformLocation(program, 'iTime'),
        iResolution: gl.getUniformLocation(program, 'iResolution'),
        iMouse: gl.getUniformLocation(program, 'iMouse'),
        uCompression: gl.getUniformLocation(program, 'uCompression'),
        uColor1: gl.getUniformLocation(program, 'uColor1'),
        uColor2: gl.getUniformLocation(program, 'uColor2'),
        uColor3: gl.getUniformLocation(program, 'uColor3'),
        uStreakCount: gl.getUniformLocation(program, 'uStreakCount'),
        uStretchFactor: gl.getUniformLocation(program, 'uStretchFactor'),
        uIntensity: gl.getUniformLocation(program, 'uIntensity'),
        uSpeed: gl.getUniformLocation(program, 'uSpeed'),
        uRotation: gl.getUniformLocation(program, 'uRotation'),
        uFadePower: gl.getUniformLocation(program, 'uFadePower'),
        uOpacity: gl.getUniformLocation(program, 'uOpacity')
      };
    }

    bindInteraction() {
      // Allow mouse click / hold to compress space (warp burst effect)
      window.addEventListener('mousedown', () => {
        this.targetCompression = 1.0;
      }, { passive: true });

      window.addEventListener('mouseup', () => {
        this.targetCompression = 0.0;
      }, { passive: true });

      window.addEventListener('touchstart', () => {
        this.targetCompression = 1.0;
      }, { passive: true });

      window.addEventListener('touchend', () => {
        this.targetCompression = 0.0;
      }, { passive: true });
    }

    // Canvas 2D fallback generator for environments without WebGL
    initFallback2D() {
      this.stars = [];
      const count = 300;
      for (let i = 0; i < count; i++) {
        this.stars.push({
          x: (Math.random() - 0.5) * 2000,
          y: (Math.random() - 0.5) * 2000,
          z: Math.random() * 1000 + 1,
          color: Math.random() > 0.4 ? PALETTE.butterYellow.hex : PALETTE.charcoal.hex,
          length: Math.random() * 12 + 4
        });
      }
    }

    renderFallback2D(ctx, width, height, timeSec) {
      ctx.fillStyle = PALETTE.deepBlack.hex;
      ctx.fillRect(0, 0, width, height);

      const cx = width / 2;
      const cy = height / 2;
      const speed = 600 * this.speed;

      for (let i = 0; i < this.stars.length; i++) {
        const star = this.stars[i];
        star.z -= speed * 0.016;
        if (star.z <= 1) {
          star.z = 1000;
          star.x = (Math.random() - 0.5) * width * 1.5;
          star.y = (Math.random() - 0.5) * height * 1.5;
        }

        const k = 400 / star.z;
        const px = cx + star.x * k;
        const py = cy + star.y * k;

        const prevK = 400 / (star.z + star.length * 2);
        const prevPx = cx + star.x * prevK;
        const prevPy = cy + star.y * prevK;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          ctx.strokeStyle = star.color;
          ctx.lineWidth = Math.min(2.5, (1000 - star.z) / 400 + 0.5);
          ctx.beginPath();
          ctx.moveTo(prevPx, prevPy);
          ctx.lineTo(px, py);
          ctx.stroke();
        }
      }
    }

    /**
     * Render Lightspeed frame to any 2D canvas context at specified dimensions and timestamp
     * @param {CanvasRenderingContext2D} targetCtx
     * @param {number} width
     * @param {number} height
     * @param {number} timelineSec - animation timeline time in seconds
     * @param {number} mouseXNorm - normalized 0..1 mouse X
     * @param {number} mouseYNorm - normalized 0..1 mouse Y
     * @param {number} wallClockSec - elapsed time in seconds
     */
    renderAt(targetCtx, width, height, timelineSec, mouseXNorm = 0.5, mouseYNorm = 0.5, wallClockSec = 0) {
      if (!this.gl || !this.program) {
        this.renderFallback2D(targetCtx, width, height, wallClockSec);
        return;
      }

      // Smooth compression lerp (smooth warp burst on click/drag)
      this.compression += (this.targetCompression - this.compression) * 0.08;

      const gl = this.gl;
      // Downscale buffer resolution slightly for massive fill-rate performance while maintaining pristine lines
      const scale = 0.65;
      const bw = Math.max(320, Math.round(width * scale));
      const bh = Math.max(180, Math.round(height * scale));

      if (this.offscreenCanvas.width !== bw || this.offscreenCanvas.height !== bh) {
        this.offscreenCanvas.width = bw;
        this.offscreenCanvas.height = bh;
        gl.viewport(0, 0, bw, bh);
      }

      gl.useProgram(this.program);

      // Pass exact uniforms
      gl.uniform1f(this.locations.iTime, wallClockSec);
      gl.uniform2f(this.locations.iResolution, bw, bh);
      gl.uniform4f(this.locations.iMouse, mouseXNorm * bw, (1.0 - mouseYNorm) * bh, this.targetCompression, 0);
      gl.uniform1f(this.locations.uCompression, this.compression);
      gl.uniform3f(this.locations.uColor1, this.color1.r, this.color1.g, this.color1.b);
      gl.uniform3f(this.locations.uColor2, this.color2.r, this.color2.g, this.color2.b);
      gl.uniform3f(this.locations.uColor3, this.color3.r, this.color3.g, this.color3.b);
      gl.uniform1f(this.locations.uStreakCount, this.streakCount);
      gl.uniform1f(this.locations.uStretchFactor, this.stretchFactor);
      gl.uniform1f(this.locations.uIntensity, this.intensity);
      gl.uniform1f(this.locations.uSpeed, this.speed);
      gl.uniform1f(this.locations.uRotation, this.rotation);
      gl.uniform1f(this.locations.uFadePower, this.fadePower);
      gl.uniform1f(this.locations.uOpacity, this.opacity);

      // Draw full screen quad
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      // Draw offscreen WebGL texture onto the destination 2D context
      targetCtx.drawImage(this.offscreenCanvas, 0, 0, width, height);
    }
  }

  // Export to global scope
  global.LightspeedEngine = LightspeedEngine;

})(typeof window !== 'undefined' ? window : globalThis);
