import React from 'react';
import {Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {Scene} from '../types';
import {BODY_FONT, C, FPS, TITLE_FONT, isLightBg} from '../theme';
import {Icon} from './Icons';

const useSpring = (delay: number, damping = 14) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: f - delay, fps, config: {damping, mass: 0.7}});
};

const Appear: React.FC<{delay: number; children: React.ReactNode; y?: number; style?: React.CSSProperties}> = ({
  delay,
  children,
  y = 40,
  style,
}) => {
  const s = useSpring(delay);
  const blur = interpolate(s, [0, 1], [10, 0]);
  return (
    <div style={{opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * y}px) scale(${0.96 + s * 0.04})`, filter: `blur(${blur}px)`, ...style}}>
      {children}
    </div>
  );
};

// ---------- Title with highlight ----------
const Title: React.FC<{scene: Scene; size?: number; top?: number}> = ({scene, size = 84, top = 230}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  const color = light ? C.ink : C.white;
  const title = scene.title ?? '';
  const hl = scene.highlight && title.includes(scene.highlight) ? scene.highlight : '';
  const [before, after] = hl ? [title.slice(0, title.indexOf(hl)), title.slice(title.indexOf(hl) + hl.length)] : [title, ''];
  const words = before.split(' ').filter(Boolean);
  const afterWords = after.split(' ').filter(Boolean);
  const pillS = useSpring(words.length * 3 + 4, 11);
  return (
    <div style={{position: 'absolute', top, left: 70, right: 70, textAlign: 'center', fontFamily: TITLE_FONT, fontWeight: 800, fontSize: size, lineHeight: 1.12, color}}>
      {words.map((w, i) => (
        <WordPop key={i} delay={i * 3}>
          {w}
        </WordPop>
      ))}
      {hl ? (
        light ? (
          <span style={{display: 'inline-block', position: 'relative', margin: '0 0.15em'}}>
            <WordPop delay={words.length * 3}>{hl}</WordPop>
            <svg style={{position: 'absolute', left: 0, bottom: -10, width: '100%', height: 18}} viewBox="0 0 200 18" preserveAspectRatio="none">
              <path
                d="M2 10 Q12 2 22 10 T42 10 T62 10 T82 10 T102 10 T122 10 T142 10 T162 10 T182 10 T198 10"
                stroke={C.hot}
                strokeWidth={3.5}
                fill="none"
                strokeDasharray={260}
                strokeDashoffset={260 * (1 - pillS)}
              />
            </svg>
          </span>
        ) : (
          <span
            style={{
              display: 'inline-block',
              margin: '6px 0.12em',
              padding: '2px 30px 8px',
              borderRadius: 60,
              background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
              boxShadow: '0 10px 40px rgba(139,61,255,0.5)',
              transform: `scale(${0.6 + pillS * 0.4})`,
              opacity: pillS,
            }}
          >
            {hl}
          </span>
        )
      ) : null}
      {afterWords.map((w, i) => (
        <WordPop key={'a' + i} delay={(words.length + 1 + i) * 3}>
          {w}
        </WordPop>
      ))}
      {scene.pill ? (
        <div style={{marginTop: 18}}>
          <Appear delay={10} y={10}>
            <SmallPill text={scene.pill} />
          </Appear>
        </div>
      ) : null}
    </div>
  );
};

const WordPop: React.FC<{delay: number; children: React.ReactNode}> = ({delay, children}) => {
  const s = useSpring(delay, 12);
  return (
    <span style={{display: 'inline-block', margin: '0 0.13em', opacity: Math.min(1, s * 1.5), transform: `translateY(${(1 - s) * 30}px)`, filter: `blur(${(1 - s) * 8}px)`}}>
      {children}
    </span>
  );
};

const SmallPill: React.FC<{text: string; dark?: boolean}> = ({text, dark}) => (
  <span
    style={{
      display: 'inline-block',
      padding: '8px 22px 10px',
      borderRadius: 30,
      background: dark ? C.ink : `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
      color: C.white,
      fontFamily: TITLE_FONT,
      fontWeight: 700,
      fontSize: 30,
      lineHeight: 1.1,
    }}
  >
    {text}
  </span>
);

const Card: React.FC<{light: boolean; children: React.ReactNode; style?: React.CSSProperties}> = ({light, children, style}) => (
  <div
    style={{
      borderRadius: 26,
      background: light ? '#FFFFFF' : 'rgba(255,255,255,0.06)',
      border: light ? '1px solid rgba(0,0,0,0.04)' : '1px solid rgba(255,255,255,0.09)',
      boxShadow: light ? '0 14px 40px rgba(60,40,120,0.12)' : '0 14px 40px rgba(0,0,0,0.35)',
      color: light ? C.ink : C.white,
      ...style,
    }}
  >
    {children}
  </div>
);

const Content: React.FC<{top?: number; children: React.ReactNode}> = ({top = 520, children}) => (
  <div style={{position: 'absolute', top, left: 120, right: 120, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 26}}>{children}</div>
);

const revealAt = (i: number, n: number, dur: number) => Math.round((0.12 * dur + (i * 0.62 * dur) / Math.max(1, n)) * FPS);

// ---------- Scene types ----------
const ImageCard: React.FC<{scene: Scene; light: boolean}> = ({scene, light}) => {
  if (!scene.image) return null;
  return (
    <Appear delay={8}>
      <div style={{position: 'relative', width: 840, height: 520, borderRadius: 30, overflow: 'hidden', boxShadow: '0 20px 60px rgba(0,0,0,0.35)'}}>
        <Img src={staticFile(scene.image)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
        {scene.imageCaption ? (
          <div style={{position: 'absolute', left: 0, right: 0, bottom: 22, textAlign: 'center'}}>
            <SmallPill text={scene.imageCaption} dark={light} />
          </div>
        ) : null}
      </div>
    </Appear>
  );
};

const Hook: React.FC<{scene: Scene}> = ({scene}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  return (
    <>
      <Title scene={scene} size={scene.image ? 80 : 96} top={scene.image ? 230 : 520} />
      <Content top={scene.pill ? 560 : 500}>
        <ImageCard scene={scene} light={light} />
      </Content>
    </>
  );
};

const parseNum = (s: string) => {
  const m = s.match(/^(\D*?)(-?\d+(?:[  ]\d{3})*(?:[.,]\d+)?)(.*)$/);
  if (!m) return null;
  const num = m[2].replace(/\s/g, '');
  const dec = num.includes(',') || num.includes('.') ? num.split(/[.,]/)[1].length : 0;
  return {pre: m[1], val: parseFloat(num.replace(',', '.')), post: m[3], dec, sep: num.includes(',') ? ',' : '.'};
};

const fmt = (v: number, dec: number, sep: string) => {
  const [i, d] = v.toFixed(dec).split('.');
  const grouped = i.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return d ? `${grouped}${sep}${d}` : grouped;
};

const NumberScene: React.FC<{scene: Scene}> = ({scene}) => {
  const f = useCurrentFrame();
  const light = isLightBg(scene.bg ?? 'dark');
  const p = parseNum(scene.number ?? '');
  const prog = interpolate(f, [6, 36], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: (t) => 1 - Math.pow(1 - t, 3)});
  const text = p ? `${p.pre}${fmt(p.val * prog, p.dec, p.sep)}${p.post}` : scene.number;
  const labelS = useSpring(30);
  return (
    <>
      <Title scene={scene} size={72} top={260} />
      <div style={{position: 'absolute', top: 600, left: 0, right: 0, textAlign: 'center'}}>
        {scene.image ? <ImageCard scene={{...scene, imageCaption: undefined}} light={light} /> : null}
        <div
          style={{
            fontFamily: TITLE_FONT,
            fontWeight: 800,
            fontSize: Math.min(scene.image ? 170 : 260, Math.floor(900 / (Math.max(1, (scene.number ?? '').length) * 0.66))),
            lineHeight: 1,
            color: light ? C.ink : C.white,
            marginTop: scene.image ? -150 : 0,
            textShadow: scene.image ? '0 6px 30px rgba(0,0,0,0.6)' : 'none',
            position: 'relative',
          }}
        >
          {text}
        </div>
        {scene.label ? (
          <div style={{marginTop: 26, opacity: labelS, transform: `scale(${0.7 + 0.3 * labelS})`}}>
            <SmallPill text={scene.label} dark={light} />
          </div>
        ) : null}
      </div>
    </>
  );
};

const Mark: React.FC<{mark?: 'x' | 'check' | null; delay: number}> = ({mark, delay}) => {
  const s = useSpring(delay, 10);
  if (!mark) return null;
  return (
    <div
      style={{
        width: 46,
        height: 46,
        borderRadius: 23,
        background: mark === 'x' ? '#F0533A' : '#22B573',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: `scale(${s})`,
        flexShrink: 0,
      }}
    >
      <Icon name={mark === 'x' ? 'x' : 'check'} size={26} />
    </div>
  );
};

const ListScene: React.FC<{scene: Scene; numbered?: boolean}> = ({scene, numbered}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  const items = scene.items ?? [];
  return (
    <>
      <Title scene={scene} size={72} top={250} />
      <Content top={scene.pill ? 560 : 480}>
        {items.map((it, i) => {
          const d = revealAt(i, items.length, scene.duration);
          return (
            <Appear key={i} delay={d} style={{width: '100%'}}>
              <Card light={light} style={{display: 'flex', alignItems: 'center', gap: 26, padding: '24px 28px'}}>
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: 16,
                    background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    fontFamily: TITLE_FONT,
                    fontWeight: 800,
                    fontSize: 32,
                    color: C.white,
                  }}
                >
                  {numbered || !it.icon ? i + 1 : <Icon name={it.icon} size={34} />}
                </div>
                <div style={{flex: 1}}>
                  <div style={{fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 36, lineHeight: 1.2}}>{it.text}</div>
                  {it.sub ? (
                    <div style={{fontFamily: BODY_FONT, fontWeight: 500, fontSize: 26, marginTop: 6, opacity: 0.7, lineHeight: 1.3}}>{it.sub}</div>
                  ) : null}
                </div>
                <Mark mark={it.mark} delay={d + 10} />
              </Card>
            </Appear>
          );
        })}
        {scene.note ? (
          <Appear delay={revealAt(items.length, items.length, scene.duration)}>
            <div style={{fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 34, color: light ? C.ink : C.white, textAlign: 'center', marginTop: 10}}>{scene.note}</div>
          </Appear>
        ) : null}
      </Content>
    </>
  );
};

const TimelineScene: React.FC<{scene: Scene}> = ({scene}) => {
  const f = useCurrentFrame();
  const light = isLightBg(scene.bg ?? 'dark');
  const pts = (scene.points ?? []).slice(0, 3);
  const line = interpolate(f, [12, 40], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const dotColors = ['#A99BFF', C.hot, '#22B573'];
  return (
    <>
      <Title scene={scene} size={74} top={250} />
      <Content top={scene.pill ? 600 : 520}>
        <Appear delay={6} style={{width: '100%'}}>
          <Card light={light} style={{padding: '40px 40px 34px', position: 'relative'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', position: 'relative'}}>
              <div
                style={{
                  position: 'absolute',
                  top: 11,
                  left: 60,
                  right: 60,
                  borderTop: `4px dotted ${light ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.35)'}`,
                  clipPath: `inset(0 ${(1 - line) * 100}% 0 0)`,
                }}
              />
              {pts.map((p, i) => (
                <PointView key={i} p={p} delay={10 + i * 18} color={dotColors[i]} />
              ))}
            </div>
          </Card>
        </Appear>
        <ImageCard scene={scene} light={light} />
        {scene.note ? (
          <Appear delay={revealAt(1, 2, scene.duration)}>
            <div style={{fontFamily: TITLE_FONT, fontWeight: 700, fontSize: 38, color: light ? C.ink : C.white, textAlign: 'center'}}>{scene.note}</div>
          </Appear>
        ) : null}
      </Content>
    </>
  );
};

const PointView: React.FC<{p: {date: string; label: string}; delay: number; color: string}> = ({p, delay, color}) => {
  const s = useSpring(delay, 11);
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: 260, opacity: s, transform: `translateY(${(1 - s) * 20}px)`, position: 'relative'}}>
      <div style={{width: 26, height: 26, borderRadius: 13, background: color, boxShadow: `0 0 20px ${color}`}} />
      <div style={{fontFamily: TITLE_FONT, fontWeight: 800, fontSize: 38, marginTop: 20, textAlign: 'center'}}>{p.date}</div>
      <div style={{fontFamily: BODY_FONT, fontWeight: 500, fontSize: 26, opacity: 0.7, marginTop: 4, textAlign: 'center'}}>{p.label}</div>
    </div>
  );
};

const FlowScene: React.FC<{scene: Scene}> = ({scene}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  const steps = (scene.steps ?? []).slice(0, 4);
  return (
    <>
      <Title scene={scene} size={74} top={250} />
      <Content top={scene.pill ? 600 : 530}>
        {steps.map((s, i) => {
          const d = revealAt(i, steps.length, scene.duration);
          const darkBox = i % 2 === 1;
          return (
            <React.Fragment key={i}>
              {i > 0 ? (
                <Appear delay={d - 6} y={-20}>
                  <Icon name="arrowDown" size={56} color={light ? C.ink : C.white} />
                </Appear>
              ) : null}
              <Appear delay={d}>
                <div
                  style={{
                    padding: '26px 44px',
                    borderRadius: 22,
                    minWidth: 520,
                    textAlign: 'center',
                    fontFamily: TITLE_FONT,
                    fontWeight: 700,
                    fontSize: 36,
                    background: darkBox ? C.ink : '#FFFFFF',
                    color: darkBox ? C.white : C.ink,
                    boxShadow: '0 14px 40px rgba(40,20,90,0.18)',
                  }}
                >
                  {s}
                </div>
              </Appear>
            </React.Fragment>
          );
        })}
        {scene.note ? (
          <Appear delay={revealAt(steps.length, steps.length, scene.duration)}>
            <SmallPill text={scene.note} dark />
          </Appear>
        ) : null}
      </Content>
    </>
  );
};

const CompareScene: React.FC<{scene: Scene}> = ({scene}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  const box = (v?: {value: string; label: string}, d = 0, hot = false) =>
    v ? (
      <Appear delay={d}>
        <Card light={light} style={{width: 360, padding: '36px 20px', textAlign: 'center'}}>
          <div style={{fontFamily: TITLE_FONT, fontWeight: 800, fontSize: 76, color: hot ? C.hot : undefined}}>{v.value}</div>
          <div style={{fontFamily: BODY_FONT, fontWeight: 700, fontSize: 28, opacity: 0.75, marginTop: 8}}>{v.label}</div>
        </Card>
      </Appear>
    ) : null;
  return (
    <>
      <Title scene={scene} size={74} top={260} />
      <div style={{position: 'absolute', top: 640, left: 60, right: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 30}}>
        {box(scene.left, 8)}
        <Appear delay={revealAt(1, 2, scene.duration) - 8}>
          <div style={{transform: 'rotate(-90deg)'}}>
            <Icon name="arrowDown" size={60} color={light ? C.ink : C.white} />
          </div>
        </Appear>
        {box(scene.right, revealAt(1, 2, scene.duration), true)}
      </div>
      {scene.note ? (
        <div style={{position: 'absolute', top: 1000, left: 0, right: 0, textAlign: 'center'}}>
          <Appear delay={revealAt(2, 2, scene.duration)}>
            <SmallPill text={scene.note} dark={light} />
          </Appear>
        </div>
      ) : null}
    </>
  );
};

const PhotoScene: React.FC<{scene: Scene}> = ({scene}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  if (!scene.image) {
    return (
      <>
        <Title scene={scene} size={80} top={330} />
        <div style={{position: 'absolute', top: 760, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
          <Appear delay={10}>
            <div style={{width: 260, height: 260, borderRadius: 130, background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 20px 80px rgba(139,61,255,0.55)'}}>
              <Icon name={scene.items?.[0]?.icon ?? 'info'} size={130} />
            </div>
          </Appear>
        </div>
        {scene.imageCaption ? (
          <div style={{position: 'absolute', top: 1080, left: 0, right: 0, textAlign: 'center'}}>
            <Appear delay={18}>
              <SmallPill text={scene.imageCaption} dark={light} />
            </Appear>
          </div>
        ) : null}
      </>
    );
  }
  return (
    <>
      <Title scene={scene} size={74} top={240} />
      <Content top={scene.pill ? 560 : 480}>
        <ImageCard scene={scene} light={light} />
      </Content>
    </>
  );
};

const Outro: React.FC<{scene: Scene; handle: string; source?: string}> = ({scene, handle, source}) => {
  const light = isLightBg(scene.bg ?? 'dark');
  return (
    <>
      <Title scene={scene} size={84} top={480} />
      <div style={{position: 'absolute', top: 880, left: 0, right: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 28}}>
        <Appear delay={14}>
          <div
            style={{
              padding: '22px 56px 26px',
              borderRadius: 60,
              background: `linear-gradient(135deg, ${C.accent}, ${C.accent2})`,
              color: C.white,
              fontFamily: TITLE_FONT,
              fontWeight: 800,
              fontSize: 46,
              boxShadow: '0 16px 60px rgba(139,61,255,0.55)',
            }}
          >
            {handle}
          </div>
        </Appear>
        {source ? (
          <Appear delay={24}>
            <div style={{fontFamily: BODY_FONT, fontWeight: 700, fontSize: 30, color: light ? C.ink : C.white, opacity: 0.7}}>Дереккөз: {source}</div>
          </Appear>
        ) : null}
      </div>
    </>
  );
};

export const SceneView: React.FC<{scene: Scene; handle: string; source?: string}> = ({scene, handle, source}) => {
  switch (scene.type) {
    case 'number':
      return <NumberScene scene={scene} />;
    case 'list':
      return <ListScene scene={scene} />;
    case 'statement':
      return <ListScene scene={scene} />;
    case 'timeline':
      return <TimelineScene scene={scene} />;
    case 'flow':
      return <FlowScene scene={scene} />;
    case 'compare':
      return <CompareScene scene={scene} />;
    case 'photo':
      return <PhotoScene scene={scene} />;
    case 'outro':
      return <Outro scene={scene} handle={handle} source={source} />;
    default:
      return <Hook scene={scene} />;
  }
};
