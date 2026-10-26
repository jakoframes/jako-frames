import React from 'react';
import {Composition} from 'remotion';
import {CakeSubs, CAKE_FRAMES} from './CakeSubs';

export const CakeRoot: React.FC = () => (
  <>
    <Composition id="CakeSubs" component={CakeSubs} durationInFrames={CAKE_FRAMES} fps={24} width={1080} height={1920} />
  </>
);
