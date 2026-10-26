import React from 'react';
import {Composition} from 'remotion';
import {Main, MAIN_FRAMES} from './Main';
import {FPS, H, W} from './theme';

export const Root: React.FC = () => (
  <Composition id="Main" component={Main} durationInFrames={MAIN_FRAMES} fps={FPS} width={W} height={H} />
);
