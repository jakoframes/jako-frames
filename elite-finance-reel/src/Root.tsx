import React from 'react';
import {AbsoluteFill, Composition} from 'remotion';
import {Intro, INTRO_FRAMES} from './Intro';
import {Main, MAIN_FRAMES} from './Main';
import {Outro, OUTRO_FRAMES} from './Outro';
import {FPS, H, W} from './theme';

const OnGrey: React.FC = () => (
  <AbsoluteFill style={{background: '#333'}}>
    <Outro />
  </AbsoluteFill>
);

export const Root: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={MAIN_FRAMES} fps={FPS} width={W} height={H} />
    <Composition id="Intro" component={Intro} durationInFrames={INTRO_FRAMES} fps={FPS} width={W} height={H} />
    <Composition id="Outro" component={OnGrey} durationInFrames={OUTRO_FRAMES} fps={FPS} width={W} height={H} />
  </>
);
