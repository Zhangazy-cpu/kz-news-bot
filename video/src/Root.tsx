import React from 'react';
import {Composition} from 'remotion';
import {NewsReel, totalFrames} from './NewsReel';
import {ReelProps} from './types';
import {FPS, H, W} from './theme';
import sample from './sample.json';

export const Root: React.FC = () => (
  <Composition
    id="NewsReel"
    component={NewsReel as unknown as React.FC<Record<string, unknown>>}
    width={W}
    height={H}
    fps={FPS}
    durationInFrames={totalFrames(sample as ReelProps)}
    defaultProps={sample as unknown as Record<string, unknown>}
    calculateMetadata={({props}) => ({durationInFrames: totalFrames(props as unknown as ReelProps)})}
  />
);
