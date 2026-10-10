import React from 'react';
import { motion } from 'framer-motion';

export type MascotPose = 'guarding' | 'scanning' | 'alert' | 'celebrating' | 'magnifier' | 'waving';

interface MascotProps {
  pose?: MascotPose;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  animate?: boolean;
}

export const Mascot: React.FC<MascotProps> = ({
  pose = 'guarding',
  size = 'md',
  className = '',
  animate = true
}) => {
  const sizeMap = {
    sm: 'w-16 h-16',
    md: 'w-32 h-32',
    lg: 'w-48 h-48',
    xl: 'w-64 h-64'
  };

  const floatAnimation: any = animate ? {
    y: [0, -6, 0],
    rotate: [0, 1, -1, 0],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: "easeInOut"
    }
  } : {};

  return (
    <div className={`relative flex items-center justify-center select-none ${sizeMap[size]} ${className}`}>
      {/* Editorial Soft Halo */}
      <div className="absolute inset-2 rounded-full border border-[#D5D4CE] -z-10" />

      <motion.div
        animate={floatAnimation}
        className="w-full h-full relative"
      >
        <svg
          viewBox="0 0 200 200"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full drop-shadow-md"
        >
          <defs>
            {/* Body Editorial Tone */}
            <linearGradient id="mascotBody" x1="40" y1="30" x2="160" y2="180" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FFFFFF" />
              <stop offset="60%" stopColor="#F6F5F2" />
              <stop offset="100%" stopColor="#E2E1DC" />
            </linearGradient>

            {/* Shield Near-Black & Charcoal Gradient */}
            <linearGradient id="shieldGrad" x1="60" y1="60" x2="140" y2="160" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#434346" />
              <stop offset="50%" stopColor="#252726" />
              <stop offset="100%" stopColor="#111312" />
            </linearGradient>

            {/* Shield Rim Gradient with Pale Yellow */}
            <linearGradient id="shieldRim" x1="50" y1="50" x2="150" y2="170" gradientUnits="userSpaceOnUse">
              <stop offset="0%" stopColor="#FBF5A5" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#434346" stopOpacity="0.6" />
            </linearGradient>

            {/* Eye Pupil Gradient */}
            <linearGradient id="eyeGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#111312" />
              <stop offset="100%" stopColor="#282A29" />
            </linearGradient>

            {/* Cheek Glow */}
            <radialGradient id="cheekGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#FBF5A5" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#FBF5A5" stopOpacity="0" />
            </radialGradient>

            {/* Lens Gradient */}
            <linearGradient id="lensGrad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor="#434346" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#111312" stopOpacity="0.4" />
            </linearGradient>
          </defs>

          {/* Shadow underneath */}
          <ellipse cx="100" cy="188" rx="42" ry="7" fill="#111312" fillOpacity="0.14" />

          {/* Beacon / Antenna */}
          <path d="M100 42 V26" stroke="#434346" strokeWidth="4" strokeLinecap="round" />
          <circle cx="100" cy="22" r="7" fill="#FBF5A5" stroke="#111312" strokeWidth="2" />
          <circle cx="98" cy="20" r="2.5" fill="#FFFFFF" />

          {/* Ears / Side Pods */}
          <rect x="32" y="78" width="12" height="24" rx="6" fill="#434346" />
          <rect x="156" y="78" width="12" height="24" rx="6" fill="#434346" />

          {/* Main Body */}
          <rect
            x="40"
            y="42"
            width="120"
            height="115"
            rx="52"
            fill="url(#mascotBody)"
            stroke="#DCDAD4"
            strokeWidth="2.5"
          />

          {/* Highlight on head */}
          <ellipse cx="100" cy="60" rx="35" ry="12" fill="#FFFFFF" fillOpacity="0.8" />

          {/* Visor / Face Area */}
          <rect
            x="54"
            y="70"
            width="92"
            height="54"
            rx="24"
            fill="#FFFFFF"
            stroke="#E2E1DC"
            strokeWidth="1.5"
          />

          {/* Eyes based on pose */}
          {pose === 'celebrating' ? (
            <>
              <path d="M72 95 Q82 83 92 95" stroke="#111312" strokeWidth="3.5" strokeLinecap="round" fill="none" />
              <path d="M108 95 Q118 83 128 95" stroke="#111312" strokeWidth="3.5" strokeLinecap="round" fill="none" />
            </>
          ) : pose === 'alert' ? (
            <>
              <circle cx="82" cy="94" r="9" fill="url(#eyeGrad)" />
              <circle cx="79" cy="91" r="3.5" fill="#FFFFFF" />
              <circle cx="118" cy="94" r="9" fill="url(#eyeGrad)" />
              <circle cx="115" cy="91" r="3.5" fill="#FFFFFF" />
            </>
          ) : (
            <>
              <circle cx="82" cy="94" r="8" fill="url(#eyeGrad)" />
              <circle cx="80" cy="91" r="3" fill="#FFFFFF" />
              <circle cx="84" cy="97" r="1.5" fill="#FFFFFF" />

              <circle cx="118" cy="94" r="8" fill="url(#eyeGrad)" />
              <circle cx="116" cy="91" r="3" fill="#FFFFFF" />
              <circle cx="120" cy="97" r="1.5" fill="#FFFFFF" />
            </>
          )}

          {/* Smile */}
          <path
            d={pose === 'alert' ? "M94 110 Q100 106 106 110" : "M93 108 Q100 115 107 108"}
            stroke="#111312"
            strokeWidth="2.5"
            strokeLinecap="round"
            fill="none"
          />

          {/* Cheeks with soft butter yellow glow */}
          <circle cx="68" cy="102" r="7" fill="url(#cheekGlow)" />
          <circle cx="132" cy="102" r="7" fill="url(#cheekGlow)" />

          {/* Mascot Props according to pose */}
          {pose === 'guarding' && (
            <g transform="translate(100, 140)">
              <path
                d="M-28 -28 H28 C28 5 15 28 0 38 C-15 28 -28 5 -28 -28 Z"
                fill="url(#shieldGrad)"
                stroke="url(#shieldRim)"
                strokeWidth="2.5"
              />
              <path
                d="M-16 -16 H16 C16 4 9 18 0 25 C-9 18 -16 4 -16 -16 Z"
                fill="#FBF5A5"
                fillOpacity="0.25"
              />
              <circle cx="0" cy="3" r="5" fill="#FBF5A5" />
              <path d="M0 -3 V-6" stroke="#FBF5A5" strokeWidth="2.5" strokeLinecap="round" />
            </g>
          )}

          {pose === 'scanning' && (
            <g>
              <path d="M100 90 L160 30" stroke="#434346" strokeWidth="2" strokeDasharray="3 3" />
              <circle cx="160" cy="30" r="12" fill="#FBF5A5" fillOpacity="0.3" stroke="#111312" strokeWidth="1.5" />
              <path d="M152 30 H168 M160 22 V38" stroke="#111312" strokeWidth="1.5" />
            </g>
          )}

          {pose === 'magnifier' && (
            <g transform="translate(130, 95) rotate(20)">
              <circle cx="0" cy="0" r="18" fill="url(#lensGrad)" stroke="#111312" strokeWidth="3" />
              <path d="M0 18 L0 36" stroke="#434346" strokeWidth="5" strokeLinecap="round" />
              <ellipse cx="-4" cy="-5" rx="7" ry="3" fill="#FBF5A5" fillOpacity="0.7" transform="rotate(-30)" />
            </g>
          )}

          {pose === 'waving' && (
            <g transform="translate(145, 90)">
              <circle cx="10" cy="-10" r="10" fill="#F4F3EF" stroke="#434346" strokeWidth="2" />
              <path d="M14 -24 Q18 -18 10 -10" stroke="#111312" strokeWidth="2" strokeLinecap="round" />
            </g>
          )}

          {/* Security Accents */}
          <g>
            <path d="M38 48 L41 42 L44 48 L50 51 L44 54 L41 60 L38 54 L32 51 Z" fill="#FBF5A5" />
            <path d="M162 135 L164 130 L166 135 L171 137 L166 139 L164 144 L162 139 L157 137 Z" fill="#434346" />
          </g>
        </svg>
      </motion.div>
    </div>
  );
};
