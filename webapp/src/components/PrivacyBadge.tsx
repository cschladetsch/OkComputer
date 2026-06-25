import type { PrivacyBadgeProps } from "../types";

export function PrivacyBadge({ privacyMode }: PrivacyBadgeProps): JSX.Element {
  return <div className={privacyMode ? "privacy active" : "privacy"}>{privacyMode ? "PRIVACY MODE" : "LISTENING"}</div>;
}
