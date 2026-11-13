import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {Word} from '../types';
import {BODY_FONT, C, FPS} from '../theme';

// Split words into short chunks like in the reference (max ~6 words / 40 chars)
const chunk = (words: Word[]) => {
  const out: Word[][] = [];
  let cur: Word[] = [];
  let len = 0;
  for (const w of words) {
    if (cur.length && (cur.length >= 6 || len + w.w.length > 40)) {
      out.push(cur);
      cur = [];
      len = 0;
    }
    cur.push(w);
    len += w.w.length + 1;
    if (/[.!?…]$/.test(w.w) && cur.length >= 3) {
      out.push(cur);
      cur = [];
      len = 0;
    }
  }
  if (cur.length) out.push(cur);
  return out;
};

export const Subtitles: React.FC<{words: Word[]}> = ({words}) => {
  const f = useCurrentFrame();
  const t = f / FPS;
  if (!words.length) return null;
  const chunks = chunk(words);
  let idx = chunks.findIndex((c) => t < c[c.length - 1].e + 0.05);
  if (idx === -1) idx = chunks.length - 1;
  const cur = chunks[idx];
  const start = cur[0].s;
  const appear = interpolate(t, [start - 0.05, start + 0.15], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0,
        right: 0,
        top: 1500,
        display: 'flex',
        justifyContent: 'center',
      }}
    >
      <div
        style={{
          maxWidth: 820,
          padding: '20px 34px',
          borderRadius: 22,
          background: 'rgba(22,19,31,0.88)',
          fontFamily: BODY_FONT,
          fontWeight: 700,
          fontSize: 40,
          lineHeight: 1.32,
          textAlign: 'center',
          color: C.white,
          opacity: appear,
          transform: `translateY(${(1 - appear) * 14}px)`,
          boxShadow: '0 12px 40px rgba(0,0,0,0.25)',
        }}
      >
        {cur.map((w, i) => {
          const active = t >= w.s && t < w.e + 0.08;
          const spoken = t >= w.s;
          return (
            <span key={i} style={{color: active ? C.hot : C.white, opacity: spoken ? 1 : 0.45}}>
              {w.w}
              {i < cur.length - 1 ? ' ' : ''}
            </span>
          );
        })}
      </div>
    </div>
  );
};
