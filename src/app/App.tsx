import { useEffect, useMemo, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { World } from '../scene/World';
import { Overlay } from '../ui/Overlay';
import { DebugProbe } from '../ui/DebugOverlay';
import { detectTier, initialDpr } from '../config/quality';
import { useUI } from './store';

function hasWebGL2(): boolean {
  try {
    const c = document.createElement('canvas');
    return !!c.getContext('webgl2');
  } catch {
    return false;
  }
}

const debug = new URLSearchParams(location.search).has('debug');
const forceUnsupported = new URLSearchParams(location.search).has('nowebgl');

export function App() {
  const [stage, setStage] = useState<HTMLDivElement | null>(null);
  const [attempt, setAttempt] = useState(0);
  const debugRef = useRef<HTMLDivElement>(null);
  const tier = useMemo(detectTier, []);
  const dpr = useMemo(() => initialDpr(tier), [tier]);
  const [supported, setSupported] = useState(() => !forceUnsupported && hasWebGL2());

  const retry = () => {
    if (!supported) {
      const ok = !forceUnsupported && hasWebGL2();
      setSupported(ok);
      if (!ok) return;
    }
    useUI.getState().set({ phase: 'loading', errorMessage: null });
    setAttempt((a) => a + 1);
  };

  useEffect(() => {
    if (!supported)
      useUI.getState().set({
        phase: 'unsupported',
        unsupportedReason: 'This interactive scene needs WebGL 2, which is unavailable or disabled in this browser.',
      });
  }, [supported]);

  return (
    <>
      <div
        ref={setStage}
        className="stage"
        tabIndex={0}
        role="application"
        aria-label="Cleaning stage. Drag to guide the vacuum. With this area focused, arrow keys move the nozzle and holding Space vacuums."
        aria-describedby="help-text"
      >
        {supported && stage && (
          <Canvas
            frameloop="demand"
            dpr={dpr}
            camera={{ fov: 26, near: 0.03, far: 40, position: [0, 0.6, 3] }}
            gl={{ antialias: false, powerPreference: 'high-performance', alpha: false }} // post pipeline does MSAA in its HDR target
            onCreated={({ gl }) => {
              gl.domElement.addEventListener('webglcontextlost', (e) => {
                e.preventDefault();
                useUI.getState().set({ phase: 'error', errorMessage: 'The 3D view was interrupted by the graphics driver.' });
              });
            }}
          >
            <World stage={stage} tier={tier} attempt={attempt} maxDpr={tier === 'high' ? 2 : 1.5} />
            {debug && <DebugProbe target={debugRef.current} />}
          </Canvas>
        )}
      </div>
      <div id="scene-fade" aria-hidden="true" />
      <Overlay onRetry={retry} />
      {debug && <div ref={debugRef} className="debug" />}
    </>
  );
}
