import { useCallback, useEffect, useRef, useState } from 'react';
import { useUI } from '../app/store';
import { experienceRef } from '../app/experienceRef';
import type { DirtDensity, DirtKind, SurfaceKind } from '../contracts/types';
import { DirtPreview, Icon } from './icons';

const KINDS: { id: DirtKind; label: string }[] = [
  { id: 'dust', label: 'Dust' },
  { id: 'hair', label: 'Hair' },
  { id: 'pet', label: 'Pet hair' },
  { id: 'crumbs', label: 'Crumbs' },
  { id: 'mixed', label: 'Mixed' },
];
const DENSITIES: { id: DirtDensity; label: string }[] = [
  { id: 'light', label: 'Light' },
  { id: 'medium', label: 'Medium' },
  { id: 'heavy', label: 'Heavy' },
];
const FLOORS: { id: SurfaceKind; label: string }[] = [
  { id: 'oak', label: 'Oak' },
  { id: 'stone', label: 'Stone' },
  { id: 'carpet', label: 'Carpet' },
];

const exp = () => experienceRef.current;

function formatBytes(n: number) {
  return n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1e3))} KB`;
}

function useIsMobile() {
  const q = '(max-width: 699px), (max-height: 480px)';
  const [m, setM] = useState(() => matchMedia(q).matches);
  useEffect(() => {
    const mq = matchMedia(q);
    const f = () => setM(mq.matches);
    mq.addEventListener('change', f);
    return () => mq.removeEventListener('change', f);
  }, []);
  return m;
}

export function Overlay({ onRetry }: { onRetry: () => void }) {
  const ui = useUI();
  const mobile = useIsMobile();
  const [helpOpen, setHelpOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const [pressed, setPressed] = useState(false);
  const startRef = useCallback((el: HTMLButtonElement | null) => {
    if (el) exp()?.setStartButton(el);
  }, []);
  const startEl = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    if (ui.phase === 'hero') {
      setPressed(false);
      exp()?.setStartButton(startEl.current);
    }
    if (ui.phase !== 'active') {
      setMoreOpen(false);
    }
  }, [ui.phase]);

  const onStart = () => {
    if (pressed) return; // repeated presses never spawn duplicate timelines
    setPressed(true);
    // let the 1–2 px press travel read before the transition begins
    window.setTimeout(() => exp()?.start(), 120);
  };

  const active = ui.phase === 'active';
  const showControls = active && ui.controlsVisible;
  const collapsed = ui.strokeActive;

  return (
    <div className={`overlay phase-${ui.phase}${collapsed ? ' is-stroking' : ''}${ui.night || ui.phase === 'hero' || ui.phase === 'loading' || ui.phase === 'starting' || ui.phase === 'returning' ? ' is-night' : ''}`}>
      <header className="brand" data-ui-block>
        <span className="brand-name">Shark PowerDetect Clean &amp; Empty</span>
        {(ui.phase === 'hero' || ui.phase === 'loading') && <span className="brand-line">Make a mess.</span>}
      </header>
      <p className="concept-label">Unofficial fan concept · not affiliated with or endorsed by SharkNinja</p>

      {(ui.phase === 'loading' || ui.phase === 'error' || ui.phase === 'unsupported') && (
        <div className={`loader${ui.phase !== 'loading' ? ' is-static' : ''}`} role="status" aria-live="polite">
          <div className="poster" aria-hidden="true" style={{ backgroundImage: `url(${import.meta.env.BASE_URL}poster.webp)` }} />
          {ui.phase === 'loading' && (
            <p className="loader-text">
              Loading product
              <span className="loader-bytes">
                {ui.loadedBytes > 0 &&
                  (ui.totalBytes ? ` · ${formatBytes(ui.loadedBytes)} of ${formatBytes(ui.totalBytes)}` : ` · ${formatBytes(ui.loadedBytes)}`)}
              </span>
            </p>
          )}
          {ui.phase === 'error' && (
            <div className="notice">
              <p>{ui.errorMessage ?? 'Something went wrong while loading.'}</p>
              <button className="pill" onClick={onRetry}>
                Retry
              </button>
            </div>
          )}
          {ui.phase === 'unsupported' && (
            <div className="notice">
              <p>{ui.unsupportedReason}</p>
              <p className="muted">The image shown is a still render of the 3D model.</p>
              <button className="pill" onClick={onRetry}>
                Retry
              </button>
            </div>
          )}
        </div>
      )}

      {ui.phase === 'hero' && (
        <button
          ref={(el) => {
            startEl.current = el;
            startRef(el);
          }}
          className={`start${pressed ? ' is-pressed' : ''}`}
          onClick={onStart}
          aria-label="Start"
        >
          <span className="start-cap" aria-hidden="true">
            <Icon name="power" />
          </span>
          <span className="start-label">Start</span>
        </button>
      )}


      {ui.phase === 'starting' && (
        <button className="skip pill ghost" onClick={() => exp()?.skipIntro()}>
          Skip intro
        </button>
      )}

      {(active || ui.phase === 'inspect') && (
        <nav className={`utility${ui.controlsVisible ? '' : ' is-hidden'}`} aria-label="View" data-ui-block>
          {ui.phase === 'inspect' ? (
            <>
              <button className="pill ghost" onClick={() => exp()?.inspectPreset('full')}>
                Full
              </button>
              <button className="pill ghost" onClick={() => exp()?.inspectPreset('head')}>
                Head
              </button>
              <button className="pill ghost" onClick={() => exp()?.inspectPreset('bin')}>
                Bin
              </button>
              <button className="pill" onClick={() => exp()?.exitInspect()}>
                Done
              </button>
            </>
          ) : (
            <>
              <button className="icon-btn" onClick={() => exp()?.setNight(!ui.night)} aria-pressed={ui.night} aria-label={ui.night ? 'Night lighting on' : 'Night lighting off'} title={ui.night ? 'Day' : 'Night'}>
                <Icon name={ui.night ? 'sun' : 'moon'} />
              </button>
              <button className="icon-btn" onClick={() => exp()?.inspect()} aria-label="Inspect product" title="Inspect">
                <Icon name="inspect" />
              </button>
              <button
                className="icon-btn"
                onClick={() => exp()?.setSound(!ui.sound)}
                aria-pressed={ui.sound}
                aria-label={ui.sound ? 'Sound on' : 'Sound off'}
                title={ui.sound ? 'Sound on' : 'Sound off'}
              >
                <Icon name={ui.sound ? 'sound' : 'mute'} />
              </button>
              <button className="icon-btn" onClick={() => setHelpOpen((h) => !h)} aria-expanded={helpOpen} aria-controls="help-text" aria-label="Controls help" title="Controls">
                <Icon name="help" />
              </button>
              <button className="icon-btn" onClick={() => exp()?.back()} aria-label="Back to product" title="Back">
                <Icon name="back" />
              </button>
            </>
          )}
        </nav>
      )}

      <div id="help-text" className={`help${helpOpen && active ? ' is-open' : ''}`} role="note">
        <p>
          <strong>Clean</strong> — drag anywhere on the floor to guide the vacuum. Forward and backward strokes both pick up.
        </p>
        <p>
          <strong>Add dirt</strong> — tap to scatter, drag to paint a trail.
        </p>
        <p className="muted">Keys: C clean · A add dirt · Esc close · focus the floor, then arrows move and Space vacuums.</p>
      </div>

      {active && ui.detecting && <p className="status-chip" aria-live="polite">Detecting</p>}

      {active && ui.allClear && !ui.strokeActive && (
        <div className="clear-msg" role="status">
          <p>All clear.</p>
          <button className="pill" onClick={() => exp()?.makeMess()}>
            Make another mess.
          </button>
        </div>
      )}

      {active && (
        <div className={`dock${showControls ? '' : ' is-hidden'}${mobile ? ' is-mobile' : ''}`} data-ui-block data-hidden={showControls ? 'false' : 'true'}>
          {ui.drawerOpen && (
            <div className="drawer" role="group" aria-label="Dirt">
              <div className="kinds" role="radiogroup" aria-label="Dirt type">
                {KINDS.map((k) => (
                  <button
                    key={k.id}
                    role="radio"
                    aria-checked={ui.dirtKind === k.id}
                    className={`kind${ui.dirtKind === k.id ? ' is-on' : ''}`}
                    onClick={() => ui.set({ dirtKind: k.id })}
                  >
                    <DirtPreview kind={k.id} />
                    <span>{k.label}</span>
                  </button>
                ))}
              </div>
              <div className="seg" role="radiogroup" aria-label="Density">
                {DENSITIES.map((d) => (
                  <button key={d.id} role="radio" aria-checked={ui.density === d.id} className={ui.density === d.id ? 'is-on' : ''} onClick={() => ui.set({ density: d.id })}>
                    {d.label}
                  </button>
                ))}
              </div>
              <p className="drawer-hint">{ui.budgetFull ? 'That’s plenty of mess — clean some up first.' : 'Tap to scatter · drag to paint'}</p>
            </div>
          )}
          {mobile && moreOpen && !ui.drawerOpen && (
            <div className="drawer" role="group" aria-label="Floor and reset">
              <div className="seg" role="radiogroup" aria-label="Floor">
                {FLOORS.map((f) => (
                  <button key={f.id} role="radio" aria-checked={ui.surface === f.id} className={ui.surface === f.id ? 'is-on' : ''} onClick={() => exp()?.setSurface(f.id)}>
                    {f.label}
                  </button>
                ))}
              </div>
              <button
                className="pill ghost wide"
                onClick={() => {
                  exp()?.clearFloor();
                  setMoreOpen(false);
                }}
              >
                Clear floor
              </button>
            </div>
          )}
          <div className="toolbar" role="toolbar" aria-label="Tools">
            <div className="seg tools" role="radiogroup" aria-label="Tool">
              <button role="radio" aria-checked={ui.tool === 'clean'} className={ui.tool === 'clean' ? 'is-on' : ''} onClick={() => exp()?.setTool('clean')}>
                <Icon name="clean" />
                <span>Clean</span>
              </button>
              <button role="radio" aria-checked={ui.tool === 'add'} className={ui.tool === 'add' ? 'is-on' : ''} onClick={() => exp()?.setTool('add')}>
                <Icon name="add" />
                <span>Add dirt</span>
              </button>
            </div>
            <span className="sep" aria-hidden="true" />
            <button className="tb-btn" onClick={() => exp()?.makeMess()}>
              <Icon name="mess" />
              <span>Make a mess</span>
            </button>
            {mobile ? (
              <button className="tb-btn" aria-expanded={moreOpen} onClick={() => setMoreOpen((m) => !m)}>
                <Icon name="more" />
                <span>Floor</span>
              </button>
            ) : (
              <>
                <button className="tb-btn" onClick={() => exp()?.clearFloor()}>
                  <Icon name="clear" />
                  <span>Clear floor</span>
                </button>
                <span className="sep" aria-hidden="true" />
                <div className="seg floors" role="radiogroup" aria-label="Floor">
                  {FLOORS.map((f) => (
                    <button key={f.id} role="radio" aria-checked={ui.surface === f.id} className={ui.surface === f.id ? 'is-on' : ''} onClick={() => exp()?.setSurface(f.id)}>
                      <span className={`swatch swatch-${f.id}`} aria-hidden="true" />
                      <span>{f.label}</span>
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
