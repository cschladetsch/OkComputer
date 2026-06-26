import { useEffect, useRef } from "react";
import type { TranscriptFeedProps } from "../types";

export function TranscriptFeed({ entries }: TranscriptFeedProps): JSX.Element {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [entries]);
  return (
    <div className="transcript" ref={ref}>
      {entries.map((entry) => (
        <div className={`entry ${entry.speaker.toLowerCase()}`} key={entry.utterance_id ?? `${entry.timestamp}-${entry.text}`}>
          <time>{entry.timestamp}</time>
          <strong>{entry.speaker}</strong>
          <p>{entry.text}</p>
        </div>
      ))}
    </div>
  );
}
