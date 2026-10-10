import React, { Suspense, useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { ShieldMascot, ShieldMascotProps } from './ShieldMascot';
import { Mascot as SvgMascot } from '../ui/Mascot';

interface ShieldMascotSceneProps extends ShieldMascotProps {
  className?: string;
}

// Error boundary state for WebGL context failures
function isWebGLAvailable() {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
  } catch (e) {
    return false;
  }
}

export const ShieldMascotScene: React.FC<ShieldMascotSceneProps> = ({
  pose = 'guarding',
  scale = 1.15,
  className = 'w-80 h-80 sm:w-[420px] sm:h-[420px]',
  interactive = true,
}) => {
  const [hasWebGL, setHasWebGL] = useState(true);

  useEffect(() => {
    setHasWebGL(isWebGLAvailable());
  }, []);

  if (!hasWebGL) {
    return (
      <div className={`relative flex items-center justify-center ${className}`}>
        <SvgMascot pose={pose} size="xl" />
      </div>
    );
  }

  return (
    <div className={`relative flex items-center justify-center select-none ${className}`}>
      {/* Refined Ambient Editorial Pedestal Ring */}
      <div className="absolute inset-4 rounded-full border border-[#D5D4CE] pointer-events-none -z-10" />
      <div className="absolute inset-8 rounded-full border border-[#FBF5A5]/40 pointer-events-none -z-10" />

      {/* 3D Canvas */}
      <Suspense fallback={<SvgMascot pose={pose} size="lg" />}>
        <Canvas
          shadows
          camera={{ position: [0, 0.25, 4.1], fov: 42 }}
          className="w-full h-full pointer-events-auto cursor-default"
          gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
          eventSource={typeof document !== 'undefined' ? (document.getElementById('root') || document.body) : undefined}
        >
          {/* Studio Lighting System */}
          <ambientLight intensity={0.9} color="#FFFFFF" />

          {/* Key Directional Sunlight */}
          <directionalLight
            position={[4, 5, 4]}
            intensity={1.6}
            color="#FFFFFF"
            castShadow
            shadow-mapSize={[1024, 1024]}
            shadow-bias={-0.0001}
          />

          {/* Warm Fill Light */}
          <pointLight position={[-3, 2, 2.5]} intensity={1.0} color="#FBF5A5" />

          {/* Rim / Back Light */}
          <pointLight position={[0, -2, -3]} intensity={0.8} color="#FFFFFF" />

          {/* Top Spotlight */}
          <spotLight
            position={[0, 6, 2]}
            intensity={1.2}
            angle={0.6}
            penumbra={0.8}
            color="#FFFEEF"
          />

          {/* Precise Head & Eye Cursor Tracking Mascot */}
          <ShieldMascot
            pose={pose}
            scale={scale}
            interactive={interactive}
          />
        </Canvas>
      </Suspense>
    </div>
  );
};
