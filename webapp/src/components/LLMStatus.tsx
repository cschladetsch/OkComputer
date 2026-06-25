import type { LLMStatusProps } from "../types";

export function LLMStatus({ status }: LLMStatusProps): JSX.Element {
  const max = Math.max(1, ...status.latencies_ms);
  const points = status.latencies_ms.map((latency, index) => `${index * 20},${40 - (latency / max) * 36}`).join(" ");
  return (
    <section className="panel llm">
      <div><span className={status.primary.healthy ? "dot ok" : "dot fail"} />{status.primary.model} {status.primary.latency_ms ?? "-"}ms</div>
      <div><span className={status.fallback.healthy ? "dot ok" : "dot fail"} />{status.fallback.model} {status.fallback.latency_ms ?? "-"}ms</div>
      <svg aria-label="Last 5 query latencies" viewBox="0 0 80 40"><polyline points={points} fill="none" stroke="#e53e3e" strokeWidth="2" /></svg>
    </section>
  );
}
