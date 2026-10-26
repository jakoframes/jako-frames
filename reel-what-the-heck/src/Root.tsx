import React from 'react';
import {Composition, Still} from 'remotion';
import {Cover} from './Cover';
import {Reel, DURATION_S, FPS} from './Reel';
import {ReelWide, DURATION_S as WIDE_DURATION_S} from './ReelWide';
import {DolomitesSubs, SUBS_FRAMES} from './DolomitesSubs';

export const Root: React.FC = () => (
  <>
    <Composition id="Reel" component={Reel} durationInFrames={Math.round(DURATION_S * FPS)} fps={FPS} width={1080} height={1920} />
    <Composition id="ReelWide" component={ReelWide} durationInFrames={Math.round(WIDE_DURATION_S * FPS)} fps={FPS} width={1920} height={1080} />
    <Composition id="DolomitesSubs" component={DolomitesSubs} durationInFrames={SUBS_FRAMES} fps={24} width={1080} height={1920} />
    <Still id="Cover" component={Cover} width={1080} height={1920} />
  </>
);
