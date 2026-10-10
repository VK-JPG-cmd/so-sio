import React, { useRef, useState, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useReducedMotion } from './useReducedMotion';

export interface ShieldMascotProps {
  pose?: 'guarding' | 'scanning' | 'alert' | 'celebrating' | 'waving';
  scale?: number;
  interactive?: boolean;
}

export const ShieldMascot: React.FC<ShieldMascotProps> = ({
  scale = 1.15,
  interactive = true,
}) => {
  const prefersReducedMotion = useReducedMotion();

  // Head and Eye Tracking References (ONLY these animate for cursor)
  const headPivotRef = useRef<THREE.Group>(null);
  const eyesGroupRef = useRef<THREE.Group>(null);
  const leftEyeRef = useRef<THREE.Mesh>(null);
  const rightEyeRef = useRef<THREE.Mesh>(null);

  // Left Arm Waving References ("Hii" greeting wave)
  const leftForearmRef = useRef<THREE.Group>(null);
  const leftHandRef = useRef<THREE.Group>(null);

  // Floating Exclamation Mark Ref (Gentle ambient glow above pointing hand)
  const exclamationRef = useRef<THREE.Group>(null);

  const [blinkState, setBlinkState] = useState(1);

  // Global viewport cursor tracking across the entire screen
  const mousePosRef = useRef({
    clientX: typeof window !== 'undefined' ? window.innerWidth / 2 : 0,
    clientY: typeof window !== 'undefined' ? window.innerHeight / 2 : 0,
    hasMoved: false,
  });

  useEffect(() => {
    const handlePointerMove = (e: MouseEvent | PointerEvent) => {
      mousePosRef.current = {
        clientX: e.clientX,
        clientY: e.clientY,
        hasMoved: true,
      };
    };

    window.addEventListener('pointermove', handlePointerMove, { passive: true });
    window.addEventListener('mousemove', handlePointerMove, { passive: true });

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('mousemove', handlePointerMove);
    };
  }, []);

  // Materials matching Image 2 reference (Golden-Yellow Robot with CRT Monitor & Glossy Screen)
  const materials = useMemo(() => {
    // Golden-Yellow Robot Shell
    const yellowChassis = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color('#F5A623'),
      emissive: new THREE.Color('#D97706'),
      emissiveIntensity: 0.08,
      roughness: 0.22,
      metalness: 0.15,
      clearcoat: 0.8,
      clearcoatRoughness: 0.1,
    });

    // Dark Metallic Joints & Earcup Bases
    const darkJoint = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#2A2F3B'),
      roughness: 0.35,
      metalness: 0.75,
    });

    // Deep Glossy Obsidian Black Visor Screen
    const screenGlass = new THREE.MeshPhysicalMaterial({
      color: new THREE.Color('#0D0F14'),
      roughness: 0.06,
      metalness: 0.3,
      clearcoat: 1.0,
      clearcoatRoughness: 0.04,
    });

    // Glowing Warm Cream-Yellow LED Eyes
    const glowingEye = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#FFF4B8'),
      emissive: new THREE.Color('#FBBF24'),
      emissiveIntensity: 2.5,
      roughness: 0.1,
    });

    // Silver Ventilation Louvers / Speaker Grille / Laptop Accents
    const silverGrill = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#CBD5E1'),
      roughness: 0.25,
      metalness: 0.85,
    });

    // Metallic Sleek Slate-Grey Laptop Body
    const laptopBody = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#334155'),
      roughness: 0.25,
      metalness: 0.8,
    });

    // Glowing Cyan-Blue Laptop Screen Display
    const laptopScreen = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#38BDF8'),
      emissive: new THREE.Color('#0284C7'),
      emissiveIntensity: 0.9,
      roughness: 0.1,
    });

    // Laptop UI Code / Data Stripes
    const laptopScreenCode = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#F0F9FF'),
      emissive: new THREE.Color('#BAE6FD'),
      emissiveIntensity: 1.2,
      roughness: 0.1,
    });

    // Modern Ergonomic Slate Chair Shell
    const chairSeat = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#3E4C5E'),
      roughness: 0.45,
      metalness: 0.2,
    });

    // Chair Wood/Steel Legs
    const chairLegs = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#8B5A2B'),
      roughness: 0.4,
      metalness: 0.3,
    });

    // Dark Rubber Boot Soles
    const shoeSole = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#181A20'),
      roughness: 0.7,
      metalness: 0.1,
    });

    // Sleek Executive Leather Briefcase Body
    const briefcaseBody = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#1E293B'),
      roughness: 0.4,
      metalness: 0.35,
    });

    // Polished Gold / Brass Latches, Handle Brackets & Corner Guards
    const goldHardware = new THREE.MeshStandardMaterial({
      color: new THREE.Color('#FCD34D'),
      roughness: 0.2,
      metalness: 0.9,
    });

    return {
      yellowChassis,
      darkJoint,
      screenGlass,
      glowingEye,
      silverGrill,
      laptopBody,
      laptopScreen,
      laptopScreenCode,
      shoeSole,
      briefcaseBody,
      goldHardware,
    };
  }, []);

  // Frame Loop: Cursor tracking (Head/Eyes) + Friendly Left Hand Waving Animation
  useFrame(({ clock, pointer, gl }) => {
    if (prefersReducedMotion) return;

    const t = clock.getElapsedTime();

    // Natural Eye Blinking Cycle (● ●)
    const blinkCycle = t % 3.8;
    if (blinkCycle > 3.65) {
      setBlinkState(0.08); // Eyes close briefly
    } else {
      setBlinkState(1); // Eyes fully open
    }
    if (leftEyeRef.current && rightEyeRef.current) {
      leftEyeRef.current.scale.y = blinkState;
      rightEyeRef.current.scale.y = blinkState;
    }

    // ================= DYNAMIC CURSOR POSITION (FULL SCREEN) =================
    // Tracks cursor anywhere across the entire browser viewport relative to the mascot
    let currentNormX = 0;
    let currentNormY = 0;

    if (interactive) {
      if (mousePosRef.current.hasMoved && gl?.domElement) {
        const rect = gl.domElement.getBoundingClientRect();
        const mascotCenterX = rect.left + rect.width / 2;
        // Mascot head is positioned in the upper portion of the 3D canvas
        const mascotCenterY = rect.top + rect.height * 0.38;

        const halfWidth = Math.max(window.innerWidth / 2, 350);
        const halfHeight = Math.max(window.innerHeight / 2, 250);

        currentNormX = (mousePosRef.current.clientX - mascotCenterX) / halfWidth;
        currentNormY = -(mousePosRef.current.clientY - mascotCenterY) / halfHeight;
      } else {
        currentNormX = pointer.x;
        currentNormY = pointer.y;
      }
    }

    // ================= 1. UNCONSTRAINED HEAD TRACKING (NECK PIVOT) =================
    // Expressive range (Yaw ~65 deg, Pitch ~35 deg) without rigid clamping stops
    // Using smooth continuous tanh curves so every cursor movement anywhere animates the head
    if (headPivotRef.current && interactive) {
      const maxYaw = 65 * (Math.PI / 180);   // ~1.13 rad (65 degrees wide rotation)
      const maxPitch = 35 * (Math.PI / 180); // ~0.61 rad (35 degrees pitch up/down)

      const curvedX = Math.tanh(currentNormX * 1.05);
      const curvedY = Math.tanh(currentNormY * 1.05);

      const targetHeadRotY = curvedX * maxYaw;
      const targetHeadRotX = -curvedY * maxPitch;
      const targetHeadRotZ = -curvedX * 0.08; // Natural organic lateral bank

      // Smooth damped interpolation (gentle acceleration & deceleration, no snapping)
      headPivotRef.current.rotation.y = THREE.MathUtils.lerp(
        headPivotRef.current.rotation.y,
        targetHeadRotY,
        0.09
      );
      headPivotRef.current.rotation.x = THREE.MathUtils.lerp(
        headPivotRef.current.rotation.x,
        targetHeadRotX,
        0.09
      );
      headPivotRef.current.rotation.z = THREE.MathUtils.lerp(
        headPivotRef.current.rotation.z,
        targetHeadRotZ,
        0.09
      );
    }

    // ================= 2. UNCONSTRAINED EYE TRACKING (SCREEN SOCKETS) =================
    // Eyes continuously glide across the CRT screen following cursor anywhere
    if (eyesGroupRef.current && interactive) {
      const maxEyeShiftX = 0.12;
      const maxEyeShiftY = 0.085;

      const eyeCurvedX = Math.tanh(currentNormX * 1.2);
      const eyeCurvedY = Math.tanh(currentNormY * 1.2);

      const targetEyeX = eyeCurvedX * maxEyeShiftX;
      const targetEyeY = eyeCurvedY * maxEyeShiftY;

      eyesGroupRef.current.position.x = THREE.MathUtils.lerp(
        eyesGroupRef.current.position.x,
        targetEyeX,
        0.15 // Reacts quickly and naturally with organic glance
      );
      eyesGroupRef.current.position.y = THREE.MathUtils.lerp(
        eyesGroupRef.current.position.y,
        targetEyeY,
        0.15
      );
    }

    // ================= 3. LEFT HAND "HII" WAVING ANIMATION =================
    const waveSpeed = 5.2;
    const waveSin = Math.sin(t * waveSpeed);
    const waveCos = Math.cos(t * waveSpeed);

    if (leftForearmRef.current) {
      leftForearmRef.current.rotation.z = 0.22 + waveSin * 0.28; // Side to side wave
      leftForearmRef.current.rotation.y = -0.15 + waveCos * 0.12;
    }
    if (leftHandRef.current) {
      leftHandRef.current.rotation.z = waveSin * 0.22; // Wrist articulation
    }
  });

  return (
    <group scale={[scale, scale, scale]} position={[0, -0.05, 0]}>
      
      {/* ================= ROBOT STANDING LOWER BODY & LEGS ================= */}
      <group position={[0, -0.22, 0]}>
        {/* Pelvis Joint */}
        <mesh material={materials.darkJoint} position={[0, 0.04, 0]}>
          <cylinderGeometry args={[0.26, 0.24, 0.16, 16]} />
        </mesh>
        <mesh material={materials.yellowChassis} position={[0, -0.03, 0]}>
          <boxGeometry args={[0.42, 0.08, 0.28]} />
        </mesh>

        {/* Left Standing Leg */}
        <group position={[-0.18, -0.08, 0]}>
          {/* Hip Joint */}
          <mesh material={materials.darkJoint} position={[0, 0, 0]}>
            <sphereGeometry args={[0.075, 16, 16]} />
          </mesh>
          {/* Thigh */}
          <mesh material={materials.yellowChassis} position={[0, -0.16, 0]} rotation={[0.02, 0, 0.03]}>
            <capsuleGeometry args={[0.085, 0.22, 16, 16]} />
          </mesh>
          {/* Knee Joint */}
          <mesh material={materials.darkJoint} position={[0, -0.32, 0.01]}>
            <sphereGeometry args={[0.08, 16, 16]} />
          </mesh>
          {/* Shin */}
          <mesh material={materials.yellowChassis} position={[0, -0.48, 0.01]} rotation={[-0.02, 0, 0]}>
            <capsuleGeometry args={[0.08, 0.22, 16, 16]} />
          </mesh>
          {/* Ankle Joint */}
          <mesh material={materials.darkJoint} position={[0, -0.63, 0.02]}>
            <sphereGeometry args={[0.07, 16, 16]} />
          </mesh>
          {/* Boot & Sole (Grounded) */}
          <group position={[0, -0.7, 0.05]}>
            <mesh material={materials.yellowChassis} position={[0, 0.03, 0.02]}>
              <boxGeometry args={[0.18, 0.1, 0.26]} />
            </mesh>
            <mesh material={materials.shoeSole} position={[0, -0.03, 0.02]}>
              <boxGeometry args={[0.2, 0.04, 0.28]} />
            </mesh>
          </group>
        </group>

        {/* Right Standing Leg */}
        <group position={[0.18, -0.08, 0]}>
          {/* Hip Joint */}
          <mesh material={materials.darkJoint} position={[0, 0, 0]}>
            <sphereGeometry args={[0.075, 16, 16]} />
          </mesh>
          {/* Thigh */}
          <mesh material={materials.yellowChassis} position={[0, -0.16, 0]} rotation={[0.02, 0, -0.03]}>
            <capsuleGeometry args={[0.085, 0.22, 16, 16]} />
          </mesh>
          {/* Knee Joint */}
          <mesh material={materials.darkJoint} position={[0, -0.32, 0.01]}>
            <sphereGeometry args={[0.08, 16, 16]} />
          </mesh>
          {/* Shin */}
          <mesh material={materials.yellowChassis} position={[0, -0.48, 0.01]} rotation={[-0.02, 0, 0]}>
            <capsuleGeometry args={[0.08, 0.22, 16, 16]} />
          </mesh>
          {/* Ankle Joint */}
          <mesh material={materials.darkJoint} position={[0, -0.63, 0.02]}>
            <sphereGeometry args={[0.07, 16, 16]} />
          </mesh>
          {/* Boot & Sole (Grounded) */}
          <group position={[0, -0.7, 0.05]}>
            <mesh material={materials.yellowChassis} position={[0, 0.03, 0.02]}>
              <boxGeometry args={[0.18, 0.1, 0.26]} />
            </mesh>
            <mesh material={materials.shoeSole} position={[0, -0.03, 0.02]}>
              <boxGeometry args={[0.2, 0.04, 0.28]} />
            </mesh>
          </group>
        </group>
      </group>

      {/* ================= ROBOT TORSO ================= */}
      <group position={[0, 0.05, 0]}>
        {/* Main Yellow Chest Shell */}
        <mesh material={materials.yellowChassis} position={[0, 0.12, 0]} castShadow>
          <boxGeometry args={[0.62, 0.48, 0.42]} />
        </mesh>
        
        {/* Front Chest Ventilation Louvers / Silver Grill */}
        <group position={[0, 0.12, 0.215]}>
          <mesh material={materials.darkJoint}>
            <boxGeometry args={[0.34, 0.22, 0.02]} />
          </mesh>
          {[-0.06, -0.02, 0.02, 0.06].map((offsetY, idx) => (
            <mesh key={idx} material={materials.silverGrill} position={[0, offsetY, 0.015]}>
              <boxGeometry args={[0.28, 0.022, 0.01]} />
            </mesh>
          ))}
        </group>

        {/* Ribbed Mechanical Neck Joint */}
        <group position={[0, 0.4, 0]}>
          <mesh material={materials.darkJoint}>
            <cylinderGeometry args={[0.16, 0.18, 0.14, 20]} />
          </mesh>
          <mesh material={materials.silverGrill} position={[0, 0.03, 0]}>
            <torusGeometry args={[0.17, 0.02, 12, 24]} />
          </mesh>
        </group>
      </group>

      {/* ================= 💻 HIGHLY VISIBLE STANDING LAPTOP ================= */}
      {/* Positioned in front of the standing robot at comfortable viewing height */}
      <group position={[0, -0.06, 0.38]} rotation={[-0.12, 0, 0]}>
        {/* Sleek Laptop Base Deck */}
        <mesh material={materials.laptopBody} position={[0, 0, 0]} castShadow>
          <boxGeometry args={[0.58, 0.028, 0.36]} />
        </mesh>
        {/* Front Accent Chamfer Strip */}
        <mesh material={materials.silverGrill} position={[0, 0.005, 0.175]}>
          <boxGeometry args={[0.56, 0.012, 0.01]} />
        </mesh>
        {/* Keyboard Well */}
        <mesh material={materials.darkJoint} position={[0, 0.016, -0.03]}>
          <boxGeometry args={[0.5, 0.008, 0.2]} />
        </mesh>
        {/* Key Rows Simulation */}
        {[-0.09, -0.05, -0.01, 0.03].map((zPos, idx) => (
          <mesh key={idx} material={materials.silverGrill} position={[0, 0.022, zPos]}>
            <boxGeometry args={[0.46, 0.005, 0.022]} />
          </mesh>
        ))}
        {/* Smooth Trackpad */}
        <mesh material={materials.silverGrill} position={[0, 0.016, 0.11]}>
          <boxGeometry args={[0.16, 0.006, 0.09]} />
        </mesh>

        {/* Angled High-Visibility Glowing Display Screen */}
        <group position={[0, 0.014, -0.16]} rotation={[-0.92, 0, 0]}>
          {/* Display Shell Bezel */}
          <mesh material={materials.laptopBody} position={[0, 0.19, 0]} castShadow>
            <boxGeometry args={[0.58, 0.36, 0.022]} />
          </mesh>
          {/* Glowing Front Display Screen */}
          <mesh material={materials.laptopScreen} position={[0, 0.19, 0.014]}>
            <planeGeometry args={[0.54, 0.32]} />
          </mesh>
          {/* Futuristic Glowing Code/UI Dashboard Lines on Screen */}
          <group position={[0, 0.19, 0.016]}>
            <mesh material={materials.laptopScreenCode} position={[-0.12, 0.09, 0]}>
              <planeGeometry args={[0.2, 0.028]} />
            </mesh>
            <mesh material={materials.laptopScreenCode} position={[0.1, 0.09, 0]}>
              <planeGeometry args={[0.16, 0.028]} />
            </mesh>
            <mesh material={materials.laptopScreenCode} position={[-0.03, 0.025, 0]}>
              <planeGeometry args={[0.38, 0.024]} />
            </mesh>
            <mesh material={materials.laptopScreenCode} position={[-0.07, -0.04, 0]}>
              <planeGeometry args={[0.3, 0.024]} />
            </mesh>
            <mesh material={materials.laptopScreenCode} position={[0.02, -0.095, 0]}>
              <planeGeometry args={[0.42, 0.024]} />
            </mesh>
          </group>
          {/* Glowing Shield AI Brand Logo on Back Cover */}
          <mesh material={materials.glowingEye} position={[0, 0.19, -0.014]} rotation={[0, Math.PI, 0]}>
            <circleGeometry args={[0.04, 24]} />
          </mesh>
        </group>
      </group>

      {/* ================= 👋 LEFT ARM (WARM "HII" WAVING MOTION) ================= */}
      <group position={[-0.34, 0.22, 0]}>
        {/* Left Shoulder Joint */}
        <mesh material={materials.darkJoint}>
          <sphereGeometry args={[0.09, 16, 16]} />
        </mesh>
        {/* Left Upper Arm (Raised upward & slightly outward for welcoming greeting) */}
        <mesh material={materials.yellowChassis} position={[-0.1, 0.08, 0.1]} rotation={[-0.35, 0.2, 0.75]}>
          <capsuleGeometry args={[0.075, 0.2, 16, 16]} />
        </mesh>

        {/* Left Elbow Joint */}
        <group position={[-0.2, 0.2, 0.18]}>
          <mesh material={materials.darkJoint}>
            <sphereGeometry args={[0.075, 16, 16]} />
          </mesh>

          {/* Animated Forearm Pivot (Waves left-to-right in real time) */}
          <group ref={leftForearmRef} position={[0, 0, 0]}>
            <mesh material={materials.yellowChassis} position={[0, 0.14, 0]} rotation={[0, 0, 0]}>
              <capsuleGeometry args={[0.07, 0.18, 16, 16]} />
            </mesh>
            <mesh material={materials.darkJoint} position={[0, 0.26, 0]}>
              <sphereGeometry args={[0.065, 16, 16]} />
            </mesh>

            {/* Animated Hand Pivot (Waving Hand with Open Palm) */}
            <group ref={leftHandRef} position={[0, 0.3, 0]}>
              {/* Palm */}
              <mesh material={materials.darkJoint} position={[0, 0.04, 0]}>
                <boxGeometry args={[0.09, 0.08, 0.05]} />
              </mesh>
              {/* Four Waving Fingers */}
              {[-0.03, -0.01, 0.01, 0.03].map((xOff, idx) => (
                <mesh key={idx} material={materials.yellowChassis} position={[xOff, 0.1, 0]}>
                  <capsuleGeometry args={[0.012, 0.06, 10, 10]} />
                </mesh>
              ))}
              {/* Thumb */}
              <mesh material={materials.yellowChassis} position={[0.055, 0.04, 0]} rotation={[0, 0, -0.5]}>
                <capsuleGeometry args={[0.012, 0.045, 10, 10]} />
              </mesh>
            </group>
          </group>
        </group>
      </group>

      {/* ================= 💼 RIGHT ARM & CARRIED EXECUTIVE BRIEFCASE ================= */}
      <group position={[0.34, 0.22, 0]}>
        {/* Right Shoulder Joint */}
        <mesh material={materials.darkJoint}>
          <sphereGeometry args={[0.09, 16, 16]} />
        </mesh>

        {/* Upper Arm extending down naturally */}
        <mesh material={materials.yellowChassis} position={[0.08, -0.16, 0.02]} rotation={[0.05, 0, -0.14]}>
          <capsuleGeometry args={[0.075, 0.22, 16, 16]} />
        </mesh>

        {/* Elbow Joint */}
        <group position={[0.13, -0.32, 0.03]}>
          <mesh material={materials.darkJoint}>
            <sphereGeometry args={[0.075, 16, 16]} />
          </mesh>

          {/* Forearm extending down to grip handle */}
          <mesh material={materials.yellowChassis} position={[0.03, -0.16, 0.02]} rotation={[-0.02, 0, -0.06]}>
            <capsuleGeometry args={[0.07, 0.2, 16, 16]} />
          </mesh>

          {/* Wrist Joint */}
          <mesh material={materials.darkJoint} position={[0.05, -0.3, 0.03]}>
            <sphereGeometry args={[0.065, 16, 16]} />
          </mesh>

          {/* Gripping Hand */}
          <group position={[0.05, -0.35, 0.03]}>
            <mesh material={materials.darkJoint} position={[0, 0, 0]}>
              <boxGeometry args={[0.08, 0.07, 0.09]} />
            </mesh>
            {/* Curled Fingers Wrapping Around Handle */}
            <mesh material={materials.yellowChassis} position={[0, -0.02, 0]}>
              <cylinderGeometry args={[0.035, 0.035, 0.09, 12]} />
            </mesh>

            {/* ================= EXECUTIVE BRIEFCASE ================= */}
            <group position={[0, -0.26, 0]} rotation={[0, 0, 0]}>
              {/* Briefcase Main Leather Body */}
              <mesh material={materials.briefcaseBody} position={[0, 0, 0]} castShadow>
                <boxGeometry args={[0.12, 0.36, 0.46]} />
              </mesh>
              
              {/* Center Divider / Trim Seam */}
              <mesh material={materials.goldHardware} position={[0, 0, 0]}>
                <boxGeometry args={[0.124, 0.012, 0.464]} />
              </mesh>

              {/* Polished Gold Dual Key Latches */}
              <mesh material={materials.goldHardware} position={[0.062, 0.08, 0.12]}>
                <boxGeometry args={[0.01, 0.04, 0.03]} />
              </mesh>
              <mesh material={materials.goldHardware} position={[0.062, 0.08, -0.12]}>
                <boxGeometry args={[0.01, 0.04, 0.03]} />
              </mesh>

              {/* Protective Brass Corner Accents */}
              {[
                [-0.17, 0.22],
                [-0.17, -0.22],
                [0.17, 0.22],
                [0.17, -0.22],
              ].map(([yC, zC], idx) => (
                <mesh key={idx} material={materials.goldHardware} position={[0, yC, zC]}>
                  <boxGeometry args={[0.125, 0.04, 0.04]} />
                </mesh>
              ))}

              {/* Top Handle Brackets & Arch Grip */}
              <mesh material={materials.goldHardware} position={[0, 0.19, 0.08]}>
                <boxGeometry args={[0.04, 0.03, 0.02]} />
              </mesh>
              <mesh material={materials.goldHardware} position={[0, 0.19, -0.08]}>
                <boxGeometry args={[0.04, 0.03, 0.02]} />
              </mesh>
              {/* Ergonomic Top Grip Bar */}
              <mesh material={materials.briefcaseBody} position={[0, 0.22, 0]}>
                <cylinderGeometry args={[0.018, 0.018, 0.16, 12]} />
              </mesh>
            </group>
          </group>
        </group>
      </group>

      {/* ================= 🎯 HEAD & EYES (PRECISE REAL-TIME CURSOR TRACKING) ================= */}
      {/* Rotates smoothly on the actual neck pivot [0, 0.58, 0] */}
      <group ref={headPivotRef} position={[0, 0.58, 0]}>
        
        {/* Outer Yellow CRT Monitor Housing */}
        <group position={[0, 0.28, 0]}>
          
          {/* Main Beveled Monitor Shell */}
          <mesh material={materials.yellowChassis} castShadow>
            <boxGeometry args={[0.82, 0.72, 0.56]} />
          </mesh>

          {/* Front Bezel Rim */}
          <mesh material={materials.yellowChassis} position={[0, 0, 0.26]}>
            <boxGeometry args={[0.78, 0.66, 0.06]} />
          </mesh>

          {/* Glossy Obsidian Screen Glass */}
          <mesh material={materials.screenGlass} position={[0, 0, 0.28]}>
            <planeGeometry args={[0.66, 0.52]} />
          </mesh>

          {/* ================= EYE CURSOR TRACKING ================= */}
          {/* Shifted across the screen surface in real-time */}
          <group ref={eyesGroupRef} position={[0, 0.02, 0.29]}>
            {/* Left Glowing LED Eye */}
            <mesh ref={leftEyeRef} material={materials.glowingEye} position={[-0.14, 0, 0]}>
              <capsuleGeometry args={[0.055, 0.08, 16, 16]} />
            </mesh>

            {/* Right Glowing LED Eye */}
            <mesh ref={rightEyeRef} material={materials.glowingEye} position={[0.14, 0, 0]}>
              <capsuleGeometry args={[0.055, 0.08, 16, 16]} />
            </mesh>
          </group>

          {/* Side Headphone Earcups & Antennas (Rigidly attached to head) */}
          {/* Left Earcup */}
          <group position={[-0.44, 0, 0]}>
            <mesh material={materials.darkJoint} rotation={[0, 0, Math.PI / 2]}>
              <cylinderGeometry args={[0.22, 0.22, 0.1, 24]} />
            </mesh>
            <mesh material={materials.silverGrill} position={[-0.04, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
              <torusGeometry args={[0.2, 0.02, 12, 24]} />
            </mesh>
            {/* Left Antenna */}
            <group position={[0, 0.22, 0]} rotation={[0, 0, -0.08]}>
              <mesh material={materials.darkJoint} position={[0, 0.06, 0]}>
                <cylinderGeometry args={[0.025, 0.03, 0.12, 12]} />
              </mesh>
              <mesh material={materials.yellowChassis} position={[0, 0.22, 0]}>
                <boxGeometry args={[0.04, 0.24, 0.06]} />
              </mesh>
            </group>
          </group>

          {/* Right Earcup */}
          <group position={[0.44, 0, 0]}>
            <mesh material={materials.darkJoint} rotation={[0, 0, Math.PI / 2]}>
              <cylinderGeometry args={[0.22, 0.22, 0.1, 24]} />
            </mesh>
            <mesh material={materials.silverGrill} position={[0.04, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
              <torusGeometry args={[0.2, 0.02, 12, 24]} />
            </mesh>
            {/* Right Antenna */}
            <group position={[0, 0.22, 0]} rotation={[0, 0, 0.08]}>
              <mesh material={materials.darkJoint} position={[0, 0.06, 0]}>
                <cylinderGeometry args={[0.025, 0.03, 0.12, 12]} />
              </mesh>
              <mesh material={materials.yellowChassis} position={[0, 0.22, 0]}>
                <boxGeometry args={[0.04, 0.24, 0.06]} />
              </mesh>
            </group>
          </group>
        </group>
      </group>

      {/* ================= SOFT CONTACT SHADOW (STATIONARY) ================= */}
      <mesh position={[0, -0.85, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[2.2, 2.2]} />
        <meshBasicMaterial
          color="#3B2D54"
          transparent
          opacity={0.15}
        />
      </mesh>
    </group>
  );
};
