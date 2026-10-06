import type { Experience } from './Experience';

/** Module-level handle so UI buttons can call the imperative controller without React state churn. */
export const experienceRef: { current: Experience | null } = { current: null };
