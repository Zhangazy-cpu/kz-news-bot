import React, {useEffect, useState} from 'react';
import {AbsoluteFill, Audio, Sequence, continueRender, delayRender, interpolate, staticFile, useCurrentFrame} from 'remotion';
import {ReelProps} from './types';
import {BODY_FONT, C, FPS, TITLE_FONT, isLightBg} from './theme';
import {Background} from './components/Backgrounds';
import {SceneView} from './components/Scenes';
import {Subtitles} from './components/Subtitles';

const AUTO_BG = ['dark', 'light', 'waves', 'marble', 'blobs'] as const;

const Header: React.FC<{handle: string; brand: string; light: boolean}> = ({handle, brand, light}) => (
  <div style={{position: 'absolute', top: 120, left: 90, display: 'flex', alignItems: 'center', gap: 16}}>
    <div
      style={{
        width: 58,
        height: 58,
        borderRadius: 29,
        background: `linear-gradient(135deg, ${C.accent}, ${C.hot})`,
        color: C.white,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: TITLE_FONT,
        fontWeight: 800,
        fontSize: 24,
        border: '3px solid rgba(255,255,255,0.8)',
      }}
    >
      {brand}
    </div>
    <div style={{fontFamily: BODY_FONT, fontWeight: 700, fontSize: 30, color: light ? C.ink : C.white, opacity: 0.9}}>{handle}</div>
  </div>
);

const SceneWrap: React.FC<{children: React.ReactNode; dur: number}> = ({children, dur}) => {
  const f = useCurrentFrame();
  const inP = interpolate(f, [0, 7], [0, 1], {extrapolateRight: 'clamp'});
  const outP = interpolate(f, [dur - 5, dur], [1, 0], {extrapolateLeft: 'clamp'});
  const p = Math.min(inP, outP);
  return (
    <AbsoluteFill style={{opacity: p, transform: `scale(${1.03 - 0.03 * inP})`, filter: `blur(${(1 - p) * 12}px)`}}>
      {children}
    </AbsoluteFill>
  );
};

export const totalFrames = (p: ReelProps) => p.scenes.reduce((a, s) => a + Math.max(1, Math.round(s.duration * FPS)), 0);

export const NewsReel: React.FC<ReelProps> = (props) => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    document.fonts.ready.then(() => continueRender(handle));
  }, [handle]);

  let from = 0;
  return (
    <AbsoluteFill style={{background: C.dark}}>
      {props.audio ? <Audio src={staticFile(props.audio)} /> : null}
      {props.scenes.map((s, i) => {
        const dur = Math.max(1, Math.round(s.duration * FPS));
        const bg = s.bg ?? AUTO_BG[i % AUTO_BG.length];
        const scene = {...s, bg};
        const seq = (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <Background bg={bg} />
            <SceneWrap dur={dur}>
              <SceneView scene={scene} handle={props.handle} source={props.source} />
            </SceneWrap>
            <Header handle={props.handle} brand={props.brand} light={isLightBg(bg)} />
            <Subtitles words={s.words} />
          </Sequence>
        );
        from += dur;
        return seq;
      })}
    </AbsoluteFill>
  );
};
