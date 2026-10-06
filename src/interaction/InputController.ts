import { MOTION } from '../config/tuning';

export interface InputHandlers {
  mode(): 'clean' | 'add' | 'inspect' | 'none';
  /** client coords -> floor hit; returns false if the ray misses the floor */
  floorHit(clientX: number, clientY: number, out: { x: number; z: number }): boolean;
  /** true when the client point lies under persistent UI (no placement/cleaning there) */
  blocked(clientX: number, clientY: number): boolean;
  beginClean(hit: { x: number; z: number }): void;
  moveClean(hit: { x: number; z: number }): void;
  endClean(): void;
  addPoint(hit: { x: number; z: number }, first: boolean): void;
  endAdd(): void;
  orbit(dxPx: number, dyPx: number): void;
  zoom(factor: number): void;
  key(action: 'clean' | 'add' | 'escape'): void;
}

/**
 * Pointer + keyboard mapping for the stage element. Pointer capture belongs only to the active
 * gesture; cancel / lostpointercapture / blur always end it safely.
 */
export class InputController {
  private gesture: { id: number; type: 'clean' | 'add' | 'inspect'; touch: boolean; lastX: number; lastY: number } | null = null;
  private pinch = new Map<number, { x: number; y: number }>();
  private pinchDist = 0;
  private hit = { x: 0, z: 0 };
  readonly keys = { up: false, down: false, left: false, right: false, space: false };
  private stageFocused = false;

  constructor(private el: HTMLElement, private h: InputHandlers) {
    el.addEventListener('pointerdown', this.onDown);
    el.addEventListener('pointermove', this.onMove);
    el.addEventListener('pointerup', this.onUp);
    el.addEventListener('pointercancel', this.onUp);
    el.addEventListener('lostpointercapture', this.onLost);
    el.addEventListener('wheel', this.onWheel, { passive: false });
    el.addEventListener('focus', this.onFocus);
    el.addEventListener('blur', this.onBlur);
    el.addEventListener('contextmenu', this.prevent);
    window.addEventListener('keydown', this.onKeyDown);
    window.addEventListener('keyup', this.onKeyUp);
    window.addEventListener('blur', this.onWindowBlur);
  }

  get gestureActive() {
    return this.gesture !== null;
  }

  private prevent = (e: Event) => e.preventDefault();

  private hitAt(e: PointerEvent, touch: boolean) {
    // fingertip offset: aim slightly above the finger so it does not cover the nozzle
    const y = touch ? e.clientY - MOTION.touchOffsetPx : e.clientY;
    return this.h.floorHit(e.clientX, y, this.hit);
  }

  private onDown = (e: PointerEvent) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    const mode = this.h.mode();
    if (mode === 'none') return;
    if (mode === 'inspect') {
      this.pinch.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pinch.size === 2) {
        const [a, b] = [...this.pinch.values()];
        this.pinchDist = Math.hypot(a.x - b.x, a.y - b.y);
      }
    }
    if (this.gesture) return; // one gesture at a time
    if (mode !== 'inspect' && this.h.blocked(e.clientX, e.clientY)) return;
    const touch = e.pointerType !== 'mouse';
    this.gesture = { id: e.pointerId, type: mode, touch, lastX: e.clientX, lastY: e.clientY };
    try {
      this.el.setPointerCapture(e.pointerId);
    } catch {
      /* capture can fail for synthetic events */
    }
    e.preventDefault();
    if (mode === 'clean') {
      if (this.hitAt(e, touch)) this.h.beginClean(this.hit);
    } else if (mode === 'add') {
      if (this.hitAt(e, touch) && !this.h.blocked(e.clientX, e.clientY)) this.h.addPoint(this.hit, true);
    }
  };

  private onMove = (e: PointerEvent) => {
    if (this.pinch.has(e.pointerId)) {
      this.pinch.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (this.pinch.size === 2) {
        const [a, b] = [...this.pinch.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (this.pinchDist > 0) this.h.zoom(this.pinchDist / d);
        this.pinchDist = d;
        return;
      }
    }
    const g = this.gesture;
    if (!g || g.id !== e.pointerId) return;
    if (g.type === 'inspect') {
      this.h.orbit(e.clientX - g.lastX, e.clientY - g.lastY);
    } else if (g.type === 'clean') {
      if (this.hitAt(e, g.touch)) this.h.moveClean(this.hit);
    } else if (g.type === 'add') {
      if (!this.h.blocked(e.clientX, e.clientY) && this.hitAt(e, g.touch)) this.h.addPoint(this.hit, false);
    }
    g.lastX = e.clientX;
    g.lastY = e.clientY;
  };

  private onUp = (e: PointerEvent) => {
    this.pinch.delete(e.pointerId);
    if (this.pinch.size < 2) this.pinchDist = 0;
    const g = this.gesture;
    if (!g || g.id !== e.pointerId) return;
    this.end();
    try {
      this.el.releasePointerCapture(e.pointerId);
    } catch {
      /* already released */
    }
  };

  private onLost = (e: PointerEvent) => {
    if (this.gesture && this.gesture.id === e.pointerId) this.end();
  };

  /** End any gesture (also used on tool switch, Back, window blur). */
  end() {
    const g = this.gesture;
    if (!g) return;
    this.gesture = null;
    if (g.type === 'clean') this.h.endClean();
    else if (g.type === 'add') this.h.endAdd();
  }

  private onWheel = (e: WheelEvent) => {
    if (this.h.mode() !== 'inspect') return;
    e.preventDefault();
    this.h.zoom(Math.exp(e.deltaY * 0.0012));
  };

  private onFocus = () => (this.stageFocused = true);
  private onBlur = () => {
    this.stageFocused = false;
    this.clearKeys();
  };
  private onWindowBlur = () => {
    this.end();
    this.clearKeys();
  };

  private clearKeys() {
    this.keys.up = this.keys.down = this.keys.left = this.keys.right = this.keys.space = false;
  }

  private editing(t: EventTarget | null) {
    const el = t as HTMLElement | null;
    if (!el || !el.tagName) return false;
    return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName);
  }

  private onKeyDown = (e: KeyboardEvent) => {
    if (this.editing(e.target) || e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (k === 'Escape') {
      this.h.key('escape');
      return;
    }
    if (k === 'c' || k === 'C') this.h.key('clean');
    if (k === 'a' || k === 'A') this.h.key('add');
    if (!this.stageFocused) return;
    let used = true;
    if (k === 'ArrowUp') this.keys.up = true;
    else if (k === 'ArrowDown') this.keys.down = true;
    else if (k === 'ArrowLeft') this.keys.left = true;
    else if (k === 'ArrowRight') this.keys.right = true;
    else if (k === ' ') this.keys.space = true;
    else used = false;
    if (used) e.preventDefault();
  };

  private onKeyUp = (e: KeyboardEvent) => {
    const k = e.key;
    if (k === 'ArrowUp') this.keys.up = false;
    else if (k === 'ArrowDown') this.keys.down = false;
    else if (k === 'ArrowLeft') this.keys.left = false;
    else if (k === 'ArrowRight') this.keys.right = false;
    else if (k === ' ') this.keys.space = false;
  };

  get keyboardActive() {
    return this.stageFocused && (this.keys.up || this.keys.down || this.keys.left || this.keys.right);
  }

  dispose() {
    const el = this.el;
    el.removeEventListener('pointerdown', this.onDown);
    el.removeEventListener('pointermove', this.onMove);
    el.removeEventListener('pointerup', this.onUp);
    el.removeEventListener('pointercancel', this.onUp);
    el.removeEventListener('lostpointercapture', this.onLost);
    el.removeEventListener('wheel', this.onWheel);
    el.removeEventListener('focus', this.onFocus);
    el.removeEventListener('blur', this.onBlur);
    el.removeEventListener('contextmenu', this.prevent);
    window.removeEventListener('keydown', this.onKeyDown);
    window.removeEventListener('keyup', this.onKeyUp);
    window.removeEventListener('blur', this.onWindowBlur);
  }
}
