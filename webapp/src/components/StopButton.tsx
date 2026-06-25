import type { StopButtonProps } from "../types";

export function StopButton({ onStop }: StopButtonProps): JSX.Element {
  return <button className="stop" type="button" onClick={onStop}>STOP</button>;
}
