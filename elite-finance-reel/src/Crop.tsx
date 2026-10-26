import React from 'react';
import {Img, staticFile} from 'remotion';

// Shows the region [x,y,w,h] of a source image, scaled by s, as a positioned window.
export const Crop: React.FC<{
  src: string;
  srcW: number;
  x: number;
  y: number;
  w: number;
  h: number;
  s?: number;
  style?: React.CSSProperties;
}> = ({src, srcW, x, y, w, h, s = 1, style}) => (
  <div style={{position: 'absolute', width: w * s, height: h * s, overflow: 'hidden', ...style}}>
    <Img
      src={staticFile(src)}
      style={{position: 'absolute', left: -x * s, top: -y * s, width: srcW * s, maxWidth: 'none'}}
    />
  </div>
);
