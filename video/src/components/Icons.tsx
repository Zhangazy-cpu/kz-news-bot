import React from 'react';

// Simple stroke icons. The script writer may only use these names.
const P: Record<string, React.ReactNode> = {
  shield: <path d="M12 3l7 3v6c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V6l7-3z" />,
  flag: <path d="M5 21V4m0 0h11l-2 4 2 4H5" />,
  heart: <path d="M12 20s-7-4.5-7-10a4 4 0 017-2.6A4 4 0 0119 10c0 5.5-7 10-7 10z" />,
  search: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="M20 20l-4.5-4.5" />
    </>
  ),
  check: <path d="M5 12.5l4.5 4.5L19 7" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v6M12 7.5v.5" />
    </>
  ),
  bolt: <path d="M13 3L5 14h6l-1 7 8-11h-6l1-7z" />,
  chart: <path d="M4 20V10m6 10V4m6 16v-7m4 7H3" />,
  money: (
    <>
      <rect x="3" y="6" width="18" height="12" rx="2" />
      <circle cx="12" cy="12" r="2.5" />
    </>
  ),
  building: <path d="M4 21V5l8-2v18M12 8h8v13M8 8v.01M8 12v.01M8 16v.01M16 12v.01M16 16v.01M2 21h20" />,
  people: (
    <>
      <circle cx="9" cy="8" r="3" />
      <path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6" />
      <circle cx="17" cy="9" r="2.3" />
      <path d="M16 14.2c2.8.4 5 2.8 5 5.8" />
    </>
  ),
  globe: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" />
    </>
  ),
  calendar: (
    <>
      <rect x="4" y="5" width="16" height="15" rx="2" />
      <path d="M4 10h16M8 3v4M16 3v4" />
    </>
  ),
  car: <path d="M5 16h14M6 16l1.5-5h9L18 16M7 16v3m10-3v3M5 16v-2m14 2v-2" />,
  home: <path d="M3 11l9-7 9 7M5 9.5V20h14V9.5" />,
  leaf: <path d="M5 19C5 10 10 5 20 4c-1 10-6 15-15 15zm0 0l7-7" />,
  oil: <path d="M12 3s6 7 6 11a6 6 0 01-12 0c0-4 6-11 6-11z" />,
  plane: <path d="M10 20l2-6-7-2 1-2 8 1 4-6 2 1-2 7 6 3-1 2-6-1-3 6z" />,
  school: <path d="M2 9l10-5 10 5-10 5L2 9zm4 2v5c3 2 9 2 12 0v-5" />,
  health: <path d="M12 21s-8-5-8-11a5 5 0 018-3 5 5 0 018 3c0 6-8 11-8 11zM12 9v6M9 12h6" />,
  law: <path d="M12 3v18M5 7h14M7 7l-3 7a3 3 0 006 0L7 7zm10 0l-3 7a3 3 0 006 0l-3-7M8 21h8" />,
  weather: <path d="M7 18a4 4 0 010-8 6 6 0 0111.5 1.5A3.5 3.5 0 0117.5 18H7z" />,
  sport: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3v18M3 12h18" />
    </>
  ),
  arrowUp: <path d="M12 20V5m-6 6l6-6 6 6" />,
  arrowDown: <path d="M12 4v15m-6-6l6 6 6-6" />,
};

export const Icon: React.FC<{name?: string; size?: number; color?: string}> = ({name, size = 30, color = '#fff'}) => {
  const node = P[name ?? ''] ?? P.info;
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      {node}
    </svg>
  );
};

export const ICON_NAMES = Object.keys(P);
