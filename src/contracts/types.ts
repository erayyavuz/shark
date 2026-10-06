export type ExperienceState =
  | 'loading'
  | 'hero'
  | 'starting'
  | 'active'
  | 'inspect'
  | 'returning'
  | 'unsupported'
  | 'error';

export type ActiveTool = 'clean' | 'add';
export type DirtKind = 'dust' | 'hair' | 'pet' | 'crumbs' | 'mixed';
export type DirtDensity = 'light' | 'medium' | 'heavy';
export type SurfaceKind = 'oak' | 'stone' | 'carpet';
export type QualityTier = 'high' | 'balanced';

export type ExperienceEvent =
  | { type: 'start' }
  | { type: 'introComplete' }
  | { type: 'toolChange'; tool: ActiveTool }
  | { type: 'pickup'; kind: Exclude<DirtKind, 'mixed'>; mass: number }
  | { type: 'allClear' }
  | { type: 'returnToHero' };
