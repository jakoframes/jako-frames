import React from 'react';
import {Composition} from 'remotion';
import {Reel, DURATION_S, FPS} from './Reel';

export const Root: React.FC = () => (
  <Composition id="Reel" component={Reel} durationInFrames={Math.round(DURATION_S * FPS)} fps={FPS} width={1080} height={1920} />
);
