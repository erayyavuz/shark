import { useEffect, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { Experience } from '../app/Experience';
import { experienceRef } from '../app/experienceRef';
import { useUI } from '../app/store';
import { PerfGovernor } from '../app/PerfGovernor';
import { loadProduct } from '../product/loadProduct';
import { VacuumRig } from '../product/VacuumRig';
import { buildProxyRig } from '../product/proxyRig';
import type { QualityTier } from '../contracts/types';
import { PostPipeline } from './post/PostPipeline';

interface Props {
  stage: HTMLElement;
  tier: QualityTier;
  attempt: number;
  maxDpr: number;
}

const params = new URLSearchParams(location.search);

export function World({ stage, tier, attempt, maxDpr }: Props) {
  const { gl, scene, camera, invalidate, size, setDpr, viewport } = useThree();
  const exp = useRef<Experience | null>(null);
  const gov = useRef<PerfGovernor | null>(null);
  const post = useRef<PostPipeline | null>(null);

  useEffect(() => {
    gl.toneMapping = THREE.NeutralToneMapping;
    gl.toneMappingExposure = 1.0;
    gl.outputColorSpace = THREE.SRGBColorSpace;
    gl.shadowMap.enabled = true;
    gl.shadowMap.type = THREE.PCFShadowMap;
    // the post pipeline renders several passes per frame; counters are reset once per frame there (?debug overlay)
    gl.info.autoReset = false;
    const e = new Experience({ renderer: gl, scene, camera: camera as THREE.PerspectiveCamera, stage, tier, invalidate });
    exp.current = e;
    experienceRef.current = e;
    e.resize(size.width, size.height);
    const pp = new PostPipeline(gl, scene, camera, tier, params.get('post'));
    post.current = pp;
    pp.setSize(size.width * gl.getPixelRatio(), size.height * gl.getPixelRatio());
    // never render above the display's own pixel ratio
    gov.current = new PerfGovernor(Math.min(maxDpr, window.devicePixelRatio || 1), viewport.dpr, (d) => setDpr(d));
    const ctrl = new AbortController();
    const ui = useUI.getState();
    ui.set({ phase: 'loading', errorMessage: null, loadedBytes: 0, totalBytes: null });

    const go = async () => {
      if (params.has('proxy')) {
        e.attachRig(new VacuumRig(buildProxyRig(), null, true));
      } else {
        const p = await loadProduct(params.get('model') === 'high' ? 'high' : 'balanced', (l, t) => useUI.getState().set({ loadedBytes: l, totalBytes: t }), ctrl.signal);
        e.attachRig(new VacuumRig(p.scene, p.meta));
      }
      // compile shaders before revealing to avoid a hitch on Start
      await gl.compileAsync(scene, camera).catch(() => undefined);
      e.enterHero();
      // desktop: upgrade to the high-detail asset in the background (same rig, swapped in hero only)
      if (tier === 'high' && !params.has('proxy')) {
        try {
          const hi = await loadProduct('high', () => undefined, ctrl.signal);
          if (ctrl.signal.aborted) return;
          const swap = () => {
            if (e.getPhase() === 'hero') {
              e.attachRig(new VacuumRig(hi.scene, hi.meta));
              e.layoutStartButton();
            } else setTimeout(swap, 1500);
          };
          swap();
        } catch {
          /* balanced asset stays; nothing to report to the visitor */
        }
      }
    };
    go().catch((err: unknown) => {
      if (ctrl.signal.aborted) return;
      console.error(err);
      useUI.getState().set({ phase: 'error', errorMessage: 'The product model could not be loaded.' });
    });

    return () => {
      ctrl.abort();
      e.dispose();
      pp.dispose();
      post.current = null;
      gl.info.autoReset = true;
      exp.current = null;
      if (experienceRef.current === e) experienceRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt]);

  useEffect(() => {
    exp.current?.resize(size.width, size.height);
    post.current?.setSize(size.width * viewport.dpr, size.height * viewport.dpr);
    invalidate();
  }, [size.width, size.height, viewport.dpr, invalidate]);

  useFrame((_, dt) => {
    const e = exp.current;
    e?.update(dt);
    // hero launch stage follows the floor reveal (Start dissolves it into the floor, Back restores it)
    if (e) e.studio.setStage(e.floor.reveal);
    // day/night crossfade + LED-driven product lights; keep rendering while the transition runs
    if (e?.studio.update(dt)) invalidate();
    gov.current?.frame(dt);
  });

  // priority 1: we own the render (R3F stops auto-rendering); still only runs when invalidated (frameloop="demand")
  useFrame(() => {
    const pp = post.current;
    if (!pp || params.get('post') === 'off') {
      gl.render(scene, camera);
      return;
    }
    gl.info.reset();
    const st = exp.current?.studio;
    pp.render({ exposure: st?.exposure ?? 1, night: st?.nightAmount ?? 0, stage: st?.stageAmount ?? 0 });
  }, 1);

  return null;
}
