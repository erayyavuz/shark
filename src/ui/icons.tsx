import type { DirtKind } from '../contracts/types';

type IconName = 'sun' | 'moon' | 'power' | 'inspect' | 'sound' | 'mute' | 'help' | 'back' | 'clean' | 'add' | 'mess' | 'clear' | 'more';

const paths: Record<IconName, string> = {
  sun: 'M12 16.5a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Z M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4',
  moon: 'M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z',
  power: 'M12 3v8 M6.6 6.6a8 8 0 1 0 10.8 0',
  inspect: 'M12 4.5c-5 0-8.5 4.4-9.5 7.5 1 3.1 4.5 7.5 9.5 7.5s8.5-4.4 9.5-7.5c-1-3.1-4.5-7.5-9.5-7.5Z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  sound: 'M4 9.5h3.5L12 5.5v13l-4.5-4H4z M15.5 9a4 4 0 0 1 0 6 M18 6.5a7.5 7.5 0 0 1 0 11',
  mute: 'M4 9.5h3.5L12 5.5v13l-4.5-4H4z M16 9.5l5 5 M21 9.5l-5 5',
  help: 'M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z M9.6 9.3a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.6 M12 16.8v.2',
  back: 'M10 6l-6 6 6 6 M4.5 12H20',
  clean: 'M5 19h14 M7 19l1.2-4.5h7.6L17 19 M12 14.5V4',
  add: 'M6 16.5c1.5-.4 2.2 1.2 3.6.7 M11 13.3c.9 1 2.6.4 3.3 1.6 M15.8 18.2c1-.1 1.6.9 2.6.4 M7.5 11.5h.01 M17.5 11h.01 M12 19h.01 M14 7v6 M11 10h6',
  mess: 'M5.5 15.5h.01 M8.5 18.5h.01 M9 13h.01 M13 16.5h.01 M16.5 19h.01 M18.5 14h.01 M12.5 11.5c1.6-.6 3 .8 4.6.2 M6 9.5c1.2.8 2.6-.3 3.8.5 M14 6.5h.01',
  clear: 'M4 7h16 M9.5 7V4.5h5V7 M6.5 7l1 12.5h9l1-12.5',
  more: 'M4 6h16 M4 12h16 M4 18h16',
};

export function Icon({ name }: { name: IconName }) {
  return (
    <svg className="icon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={paths[name]} />
    </svg>
  );
}

/** Small, honest visual previews for each dirt type (drawn, not photographs). */
export function DirtPreview({ kind }: { kind: DirtKind }) {
  return (
    <svg className="preview" viewBox="0 0 40 28" width="40" height="28" aria-hidden="true">
      {(kind === 'dust' || kind === 'mixed') && (
        <g fill="#8a8178" opacity="0.75">
          <ellipse cx={kind === 'mixed' ? 12 : 20} cy="15" rx={kind === 'mixed' ? 8 : 13} ry="7" opacity="0.35" />
          {[...Array(kind === 'mixed' ? 8 : 16)].map((_, i) => (
            <circle key={i} cx={(kind === 'mixed' ? 6 : 9) + ((i * 7.3) % (kind === 'mixed' ? 12 : 22))} cy={10 + ((i * 5.1) % 10)} r={0.5 + (i % 3) * 0.25} />
          ))}
        </g>
      )}
      {(kind === 'hair' || kind === 'mixed') && (
        <g fill="none" stroke="#3a2f28" strokeWidth="0.7" strokeLinecap="round">
          <path d={kind === 'mixed' ? 'M22 8c4 2 2 7 7 8s4 5 8 4' : 'M5 10c6 1 6 8 13 7s8-9 17-5'} />
          <path d={kind === 'mixed' ? 'M20 20c3-3 7 0 10-3' : 'M8 21c4-4 9 1 14-3s7 1 12-2'} />
        </g>
      )}
      {kind === 'pet' && (
        <g stroke="#b9a58c" strokeWidth="0.6" strokeLinecap="round">
          {[...Array(26)].map((_, i) => {
            const a = i * 2.39;
            const r = 2 + (i % 5) * 1.6;
            const x = 20 + Math.cos(a) * r * 1.4;
            const y = 14 + Math.sin(a) * r * 0.8;
            return <line key={i} x1={x} y1={y} x2={x + Math.cos(a * 1.7) * 3.2} y2={y + Math.sin(a * 1.7) * 2.2} />;
          })}
        </g>
      )}
      {(kind === 'crumbs' || kind === 'mixed') && (
        <g>
          {[...Array(kind === 'mixed' ? 4 : 9)].map((_, i) => {
            const x = (kind === 'mixed' ? 27 : 7) + ((i * 9.7) % (kind === 'mixed' ? 10 : 27));
            const y = 8 + ((i * 6.3) % 13);
            const s = 1.3 + (i % 3) * 0.7;
            return <path key={i} d={`M${x} ${y}l${s} ${-s * 0.4} ${s * 0.5} ${s} ${-s * 0.9} ${s * 0.6}z`} fill={['#b0814e', '#8d5d33', '#c99d63'][i % 3]} />;
          })}
        </g>
      )}
    </svg>
  );
}
