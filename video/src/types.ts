export type Word = {w: string; s: number; e: number};

export type Bg = 'dark' | 'light' | 'waves' | 'marble' | 'blobs';

export type Item = {text: string; sub?: string; icon?: string; mark?: 'x' | 'check' | null};

export type Point = {date: string; label: string};

export type Scene = {
  type: 'hook' | 'number' | 'list' | 'timeline' | 'flow' | 'statement' | 'photo' | 'compare' | 'outro';
  bg?: Bg;
  title?: string;
  highlight?: string; // part of title shown as a pill / underlined
  pill?: string; // small pill under the title
  number?: string;
  label?: string;
  items?: Item[];
  points?: Point[];
  steps?: string[];
  note?: string;
  image?: string; // path inside public/
  imageCaption?: string;
  left?: {value: string; label: string};
  right?: {value: string; label: string};
  narration: string;
  duration: number; // seconds
  words: Word[]; // timings relative to scene start, seconds
};

export type ReelProps = {
  handle: string;
  brand: string; // short name shown in avatar
  source?: string;
  audio?: string; // path inside public/
  scenes: Scene[];
};
