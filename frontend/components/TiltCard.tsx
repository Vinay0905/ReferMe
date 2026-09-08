"use client";

import React, { useRef, useState } from "react";

interface TiltCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  active?: boolean;
}

export const TiltCard: React.FC<TiltCardProps> = ({
  children,
  className = "",
  onClick,
  active = false,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const [transformStyle, setTransformStyle] = useState<string>("perspective(1000px) rotateX(0deg) rotateY(0deg) translateZ(0px)");
  const [glowPos, setGlowPos] = useState<{ x: number; y: number; opacity: number }>({ x: 50, y: 50, opacity: 0 });
  const [isHovered, setIsHovered] = useState<boolean>(false);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;

    // Tilt limits: max 12 deg
    const rotateX = ((y - centerY) / centerY) * -10;
    const rotateY = ((x - centerX) / centerX) * 10;

    setTransformStyle(
      `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.025, 1.025, 1.025) translateZ(16px)`
    );

    const glowXPercent = (x / rect.width) * 100;
    const glowYPercent = (y / rect.height) * 100;
    setGlowPos({ x: glowXPercent, y: glowYPercent, opacity: 1 });
  };

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    setTransformStyle("perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1) translateZ(0px)");
    setGlowPos((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <div
      ref={cardRef}
      onClick={onClick}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{
        transform: transformStyle,
        transition: isHovered
          ? "transform 0.08s ease-out, box-shadow 0.2s ease-out"
          : "transform 0.45s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.45s ease-out",
        transformStyle: "preserve-3d",
        willChange: "transform",
      }}
      className={`relative cursor-pointer rounded-xl overflow-hidden border backdrop-blur-md transition-colors duration-200 ${
        active
          ? "bg-[#3E0F8D]/80 border-[#E4DA72] shadow-neon-gold"
          : isHovered
          ? "bg-[#3E0F8D]/60 border-[#9564DD] shadow-neon-purple"
          : "bg-[#3E0F8D]/30 border-[#9564DD]/30 hover:border-[#9564DD]"
      } ${className}`}
    >
      {/* 3D Pointer Spotlight Glow */}
      <div
        className="pointer-events-none absolute inset-0 transition-opacity duration-300 z-10"
        style={{
          opacity: glowPos.opacity,
          background: `radial-gradient(circle 220px at ${glowPos.x}% ${glowPos.y}%, rgba(149, 100, 221, 0.35), transparent 70%)`,
        }}
      />

      {/* Cyber Gold Accent Edge on Active */}
      {active && (
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-[#E4DA72] to-transparent z-20" />
      )}

      {/* Card Content with 3D Depth */}
      <div className="relative z-10" style={{ transform: "translateZ(8px)" }}>
        {children}
      </div>
    </div>
  );
};
