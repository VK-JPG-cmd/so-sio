import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

/**
 * Lightspeed - React Bits Pro Component (JSX)
 * "A hyperspace jump of streaking stars"
 * Customized with So-cio Luxury Palette:
 * - Deep black:        #111312
 * - Charcoal grey:     #434346
 * - Pale butter yellow: #FBF5A5
 */

export const Lightspeed = ({
  width = '100%',
  height = '100%',
  speed = 1.15,
  primaryColor = '#FBF5A5',
  secondaryColor = '#434346',
  tertiaryColor = '#FBF5A5',
  streakCount = 128,
  stretchFactor = 0.052,
  intensity = 1.25,
  interactionEnabled = true,
  rotation = 0,
  fadePower = 1.85,
  opacity = 1.0,
  quality = 'medium',
  maxFPS = 60,
  pauseWhenOffscreen = true,
  className = '',
  children
}) => {
  const containerRef = useRef(null);
  const animFrameRef = useRef(0);
  const startTimeRef = useRef(0);
  const lastTimeRef = useRef(0);
  const isMouseDownRef = useRef(false);
  const isVisibleRef = useRef(true);
  const targetCompRef = useRef(0);
  const currentCompRef = useRef(0);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const hexToRGB = (hex) => {
      const match = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
      return match
        ? {
            r: parseInt(match[1], 16) / 255,
            g: parseInt(match[2], 16) / 255,
            b: parseInt(match[3], 16) / 255
          }
        : { r: 0.98, g: 0.96, b: 0.65 };
    };

    const c1 = hexToRGB(primaryColor);
    const c2 = hexToRGB(secondaryColor);
    const c3 = hexToRGB(tertiaryColor);

    const rect = container.getBoundingClientRect();
    const w = rect.width || window.innerWidth;
    const h = rect.height || window.innerHeight;

    const qualityConfig = {
      low: { pixelRatio: 1, antialias: false },
      medium: { pixelRatio: Math.min(window.devicePixelRatio || 1, 2), antialias: true },
      high: { pixelRatio: Math.min(window.devicePixelRatio || 1, 3), antialias: true }
    }[quality];

    const renderer = new THREE.WebGLRenderer({
      antialias: qualityConfig.antialias,
      alpha: true,
      powerPreference: 'high-performance',
      stencil: false,
      depth: false
    });
    renderer.setClearColor(0x111312, 1);
    const pr = qualityConfig.pixelRatio;
    renderer.setSize(w, h, false);
    renderer.setPixelRatio(pr);
    renderer.domElement.style.width = '100%';
    renderer.domElement.style.height = '100%';
    renderer.domElement.style.display = 'block';
    container.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

    const uniforms = {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector2(w * pr, h * pr) },
      iMouse: { value: new THREE.Vector4(0, 0, 0, 0) },
      uCompression: { value: 0 },
      uColor1: { value: new THREE.Color(c1.r, c1.g, c1.b) },
      uColor2: { value: new THREE.Color(c2.r, c2.g, c2.b) },
      uColor3: { value: new THREE.Color(c3.r, c3.g, c3.b) },
      uStreakCount: { value: streakCount },
      uStretchFactor: { value: stretchFactor },
      uIntensity: { value: intensity },
      uSpeed: { value: speed },
      uRotation: { value: rotation },
      uFadePower: { value: fadePower },
      uOpacity: { value: opacity }
    };

    const vertexShader = `
      void main() {
        gl_Position = vec4(position, 1.0);
      }
    `;

    const fragmentShader = `
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

        streakValue = 1.0 / streakValue;
        streakValue = smoothstep(0.0, 1.0, streakValue * streakValue);
        streakValue = sin(streakValue * PI) * (speedVariation * 5.0);

        float horizontalFalloff = sin(horizontalPos * PI);
        return streakValue * (horizontalFalloff * horizontalFalloff);
      }

      void main() {
        vec2 uv = (gl_FragCoord.xy - 0.5 * iResolution) / iResolution.y;

        float distFromCenter = length(uv) + 0.08;

        float angle = atan(uv.x, uv.y) / PI + uRotation;
        float radius = 2.5 / distFromCenter;
        vec2 polarCoord = vec2(angle, radius);

        float compressionFactor = mix(1.0, 0.5, uCompression);
        polarCoord.y *= compressionFactor;

        float animTime = iTime * 0.42 * uSpeed;

        vec3 finalColor = vec3(0.0);
        finalColor += uColor1 * computeStreak(polarCoord, animTime);
        finalColor += uColor2 * computeStreak(polarCoord, animTime + 0.33);
        finalColor += uColor3 * computeStreak(polarCoord, animTime + 0.66);

        finalColor *= uIntensity;
        float distanceFade = pow(distFromCenter, uFadePower);
        finalColor *= distanceFade;
        finalColor *= uOpacity;

        // Luxury Deep black base #111312
        vec3 bg = vec3(17.0 / 255.0, 19.0 / 255.0, 18.0 / 255.0);
        gl_FragColor = vec4(bg + finalColor, 1.0);
      }
    `;

    const material = new THREE.ShaderMaterial({
      uniforms,
      vertexShader,
      fragmentShader,
      transparent: false
    });

    const geometry = new THREE.PlaneGeometry(2, 2);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    const onMouseMove = (e) => {
      const r = container.getBoundingClientRect();
      uniforms.iMouse.value.x = e.clientX - r.left;
      uniforms.iMouse.value.y = h - (e.clientY - r.top);
    };

    const onMouseDown = () => {
      isMouseDownRef.current = true;
      targetCompRef.current = 1;
      uniforms.iMouse.value.z = 1;
    };

    const onMouseUp = () => {
      isMouseDownRef.current = false;
      targetCompRef.current = 0;
      uniforms.iMouse.value.z = 0;
    };

    if (interactionEnabled) {
      container.addEventListener('mousemove', onMouseMove);
      container.addEventListener('mousedown', onMouseDown);
      window.addEventListener('mouseup', onMouseUp);
    }

    const frameInterval = 1000 / maxFPS;
    const animate = (timestamp) => {
      animFrameRef.current = requestAnimationFrame(animate);
      if (!startTimeRef.current) {
        startTimeRef.current = timestamp;
        lastTimeRef.current = timestamp;
      }
      const elapsed = timestamp - lastTimeRef.current;
      if (elapsed < frameInterval) return;
      lastTimeRef.current = timestamp - (elapsed % frameInterval);

      if (pauseWhenOffscreen && !isVisibleRef.current) return;

      uniforms.iTime.value = (timestamp - startTimeRef.current) * 0.001;
      currentCompRef.current += (targetCompRef.current - currentCompRef.current) * 0.1;
      uniforms.uCompression.value = currentCompRef.current;

      renderer.render(scene, camera);
    };

    animFrameRef.current = requestAnimationFrame(animate);

    const onResize = () => {
      const r = container.getBoundingClientRect();
      const rw = r.width || window.innerWidth;
      const rh = r.height || window.innerHeight;
      renderer.setSize(rw, rh, false);
      uniforms.iResolution.value.set(rw * pr, rh * pr);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', onResize);
      if (interactionEnabled) {
        container.removeEventListener('mousemove', onMouseMove);
        container.removeEventListener('mousedown', onMouseDown);
        window.removeEventListener('mouseup', onMouseUp);
      }
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [
    speed,
    primaryColor,
    secondaryColor,
    tertiaryColor,
    streakCount,
    stretchFactor,
    intensity,
    interactionEnabled,
    rotation,
    fadePower,
    opacity,
    quality,
    maxFPS,
    pauseWhenOffscreen
  ]);

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full overflow-hidden ${className}`}
      style={{ width, height, backgroundColor: '#111312' }}
    >
      {children}
    </div>
  );
};

export default Lightspeed;
