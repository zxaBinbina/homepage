/** Keep WAAPI easing in sync with the --motion-ease design token in src/style.css. */
export const MOTION_EASE = 'cubic-bezier(0.22, 1, 0.36, 1)'

/**
 * Read the live CSS token so runtime overrides stay in sync, with a safe fallback
 * for the brief moment before the main stylesheet has been applied.
 */
export function motionEase(root: HTMLElement = document.documentElement): string {
  return getComputedStyle(root).getPropertyValue('--motion-ease').trim() || MOTION_EASE
}
