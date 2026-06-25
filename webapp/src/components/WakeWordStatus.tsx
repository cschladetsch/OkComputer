import type { WakeWordStatusProps } from "../types";

export function WakeWordStatus({ state }: WakeWordStatusProps): JSX.Element {
  return <div className={`wake wake-${state.toLowerCase()}`} aria-label={state} role="status"><span /></div>;
}
