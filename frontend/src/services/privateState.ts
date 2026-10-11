type ResetReason = 'logout' | 401 | 403;
const listeners = new Set<(reason: ResetReason) => void>();
export let privateEpoch = 0;
export function onPrivateReset(listener: (reason: ResetReason) => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
export function clearPrivateState(reason: ResetReason) {
  privateEpoch++;
  for (const listener of listeners) listener(reason);
}
