/**
 * Uniform-grid spatial hash over the play area (counting-sort layout, no per-query allocation).
 * Rebuilt from flat position arrays when the owning kind is marked dirty.
 */
export class SpatialHash {
  readonly cols: number;
  readonly rows: number;
  private readonly start: Int32Array;
  private readonly fill: Int32Array;
  private readonly entries: Int32Array;
  private readonly cellOf: Int32Array;

  constructor(
    private readonly minX: number,
    private readonly minZ: number,
    width: number,
    depth: number,
    private readonly cell: number,
    capacity: number,
  ) {
    this.cols = Math.max(1, Math.ceil(width / cell));
    this.rows = Math.max(1, Math.ceil(depth / cell));
    this.start = new Int32Array(this.cols * this.rows + 1);
    this.fill = new Int32Array(this.cols * this.rows);
    this.entries = new Int32Array(capacity);
    this.cellOf = new Int32Array(capacity);
  }

  private cellIndex(x: number, z: number): number {
    let cx = Math.floor((x - this.minX) / this.cell);
    let cz = Math.floor((z - this.minZ) / this.cell);
    if (cx < 0) cx = 0;
    else if (cx >= this.cols) cx = this.cols - 1;
    if (cz < 0) cz = 0;
    else if (cz >= this.rows) cz = this.rows - 1;
    return cz * this.cols + cx;
  }

  /** Index items [0,count) whose alive[i] != 0. */
  rebuild(count: number, xs: Float32Array, zs: Float32Array, alive: Uint8Array): void {
    const nCells = this.cols * this.rows;
    this.start.fill(0);
    for (let i = 0; i < count; i++) {
      if (!alive[i]) {
        this.cellOf[i] = -1;
        continue;
      }
      const c = this.cellIndex(xs[i], zs[i]);
      this.cellOf[i] = c;
      this.start[c + 1]++;
    }
    for (let c = 0; c < nCells; c++) this.start[c + 1] += this.start[c];
    for (let c = 0; c < nCells; c++) this.fill[c] = this.start[c];
    for (let i = 0; i < count; i++) {
      const c = this.cellOf[i];
      if (c >= 0) this.entries[this.fill[c]++] = i;
    }
  }

  /**
   * Write the indices of every item whose cell overlaps the AABB into `out` (capacity ≥ item capacity);
   * returns the count. Callers do the exact geometric test. Items moved since the last rebuild are
   * found as long as they stayed within the query padding.
   */
  gather(x0: number, z0: number, x1: number, z1: number, out: Int32Array): number {
    let c0 = Math.floor((x0 - this.minX) / this.cell);
    let c1 = Math.floor((x1 - this.minX) / this.cell);
    let r0 = Math.floor((z0 - this.minZ) / this.cell);
    let r1 = Math.floor((z1 - this.minZ) / this.cell);
    if (c1 < 0 || r1 < 0 || c0 >= this.cols || r0 >= this.rows) return 0;
    if (c0 < 0) c0 = 0;
    if (r0 < 0) r0 = 0;
    if (c1 >= this.cols) c1 = this.cols - 1;
    if (r1 >= this.rows) r1 = this.rows - 1;
    let n = 0;
    for (let r = r0; r <= r1; r++) {
      for (let c = c0; c <= c1; c++) {
        const cell = r * this.cols + c;
        for (let k = this.start[cell], e = this.start[cell + 1]; k < e; k++) out[n++] = this.entries[k];
      }
    }
    return n;
  }
}
