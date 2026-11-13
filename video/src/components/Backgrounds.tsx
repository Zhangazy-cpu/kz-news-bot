import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Bg} from '../types';
import {C, H, W} from '../theme';

const Dark: React.FC<{f: number}> = ({f}) => {
  const x = 50 + Math.sin(f / 70) * 12;
  const y = 18 + Math.cos(f / 90) * 6;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(900px 700px at ${x}% ${y}%, rgba(139,61,255,0.35), transparent 70%),
          radial-gradient(800px 800px at ${100 - x}% 92%, rgba(120,40,200,0.30), transparent 70%), ${C.dark}`,
      }}
    />
  );
};

const Light: React.FC<{f: number}> = ({f}) => {
  const x = 50 + Math.sin(f / 80) * 20;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(1000px 700px at ${x}% 0%, rgba(178,107,255,0.18), transparent 70%), linear-gradient(180deg, #ECEBFA 0%, ${C.light} 60%)`,
      }}
    />
  );
};

const Waves: React.FC<{f: number}> = ({f}) => {
  const lines = Array.from({length: 26}, (_, i) => i);
  return (
    <AbsoluteFill style={{background: '#1B1530'}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        {lines.map((i) => {
          const off = i * 80 - 200;
          const ph = f / 40 + i * 0.35;
          const d = Array.from({length: 13}, (_, k) => {
            const y = (k / 12) * H;
            const x = off + Math.sin(y / 260 + ph) * 120 + y * 0.35;
            return `${k === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
          }).join(' ');
          return <path key={i} d={d} stroke="rgba(160,140,255,0.22)" strokeWidth={14} fill="none" strokeLinecap="round" />;
        })}
      </svg>
      <AbsoluteFill style={{background: 'radial-gradient(700px 900px at 50% 45%, rgba(27,21,48,0.85), transparent 75%)'}} />
    </AbsoluteFill>
  );
};

const Marble: React.FC<{f: number}> = ({f}) => {
  const blobs = [
    {x: 20, y: 30, r: 520, c: 'rgba(160,150,220,0.45)', sx: 90, sy: 70},
    {x: 80, y: 20, r: 460, c: 'rgba(200,190,240,0.55)', sx: 70, sy: 110},
    {x: 70, y: 75, r: 600, c: 'rgba(150,140,210,0.40)', sx: 120, sy: 80},
    {x: 25, y: 85, r: 480, c: 'rgba(210,205,245,0.6)', sx: 100, sy: 95},
  ];
  return (
    <AbsoluteFill style={{background: '#EEEDF6', overflow: 'hidden'}}>
      {blobs.map((b, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: `${b.x + Math.sin(f / b.sx + i) * 6}%`,
            top: `${b.y + Math.cos(f / b.sy + i) * 4}%`,
            width: b.r,
            height: b.r * 0.6,
            transform: `translate(-50%,-50%) rotate(${(f / 6 + i * 40) % 360}deg)`,
            borderRadius: '50%',
            background: b.c,
            filter: 'blur(60px)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

const Blobs: React.FC<{f: number}> = ({f}) => {
  const bs = [
    {x: 12, y: 58, r: 260},
    {x: 92, y: 50, r: 200},
    {x: 70, y: 88, r: 420},
    {x: 18, y: 92, r: 300},
    {x: 85, y: 18, r: 140},
  ];
  return (
    <AbsoluteFill style={{background: C.dark, overflow: 'hidden'}}>
      <AbsoluteFill style={{background: 'radial-gradient(900px 600px at 50% 10%, rgba(139,61,255,0.25), transparent 70%)'}} />
      {bs.map((b, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: `${b.x + Math.sin(f / 50 + i * 2) * 3}%`,
            top: `${b.y + Math.cos(f / 60 + i) * 2}%`,
            width: b.r,
            height: b.r,
            transform: 'translate(-50%,-50%)',
            borderRadius: '50%',
            background: 'radial-gradient(circle at 30% 30%, #E9D8FF, #9E7BFF 45%, #6E8BFF 75%, #4A2FB8)',
            boxShadow: '0 0 80px rgba(160,120,255,0.45)',
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const Background: React.FC<{bg: Bg}> = ({bg}) => {
  const f = useCurrentFrame();
  switch (bg) {
    case 'light':
      return <Light f={f} />;
    case 'waves':
      return <Waves f={f} />;
    case 'marble':
      return <Marble f={f} />;
    case 'blobs':
      return <Blobs f={f} />;
    default:
      return <Dark f={f} />;
  }
};
