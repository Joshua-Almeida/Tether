import { useState } from "react";
import type { AskResponse, GradedChunk } from "./api";

type Props = {
  result: AskResponse;
  title?: string;
};

function scoreLabel(chunk: GradedChunk): string {
  if (typeof chunk.score === "number") return chunk.score.toFixed(2);
  return chunk.relevant ? "in" : "out";
}

export default function Trace({ result, title = "Trace" }: Props) {
  const [openId, setOpenId] = useState<string | null>(null);
  const relevant = result.trace.graded.filter((item) => item.relevant).length;
  const rewrite =
    result.trace.rewrite_count > 0
      ? result.trace.rewritten_query || "rewritten"
      : "skipped";
  const steps = result.trace.steps?.length ? result.trace.steps.join(" → ") : null;
  const retrieval = result.trace.retrieval || "hybrid";

  return (
    <div className="trace">
      <p className="eyebrow">{title}</p>
      {steps ? <p className="trace-flow">{steps}</p> : null}
      <div className="step">
        <span className="step-label">Retrieve</span>
        <b>
          {result.trace.retrieved_count} chunks · {retrieval}
        </b>
      </div>
      <div className="step">
        <span className="step-label">Grade</span>
        <b>
          {result.trace.graded.length
            ? `${relevant} relevant / ${result.trace.graded.length}`
            : "skipped"}
        </b>
      </div>
      <div className="step">
        <span className="step-label">Rewrite</span>
        <b>{rewrite}</b>
      </div>
      <div className="step">
        <span className="step-label">Decision</span>
        <b className={result.trace.decision === "refuse" ? "is-refuse" : "is-answer"}>
          {result.trace.decision}
        </b>
      </div>
      {result.trace.refuse_reason ? (
        <div className="step">
          <span className="step-label">Reason</span>
          <b className="is-mute">{result.trace.refuse_reason}</b>
        </div>
      ) : null}
      {typeof result.latency_ms === "number" && result.latency_ms > 0 ? (
        <div className="step">
          <span className="step-label">Time</span>
          <b className="is-mute">{(result.latency_ms / 1000).toFixed(1)}s</b>
        </div>
      ) : null}
      {result.trace.graded.length > 0 ? (
        <div className="grades">
          <p className="step-label">Passages</p>
          {result.trace.graded.map((chunk) => {
            const key = chunk.chunk_id || chunk.source;
            const open = openId === key;
            return (
              <button
                key={key}
                type="button"
                className={`grade ${chunk.relevant ? "is-in" : "is-out"} ${open ? "is-open" : ""}`}
                onClick={() => setOpenId(open ? null : key)}
              >
                <span className="grade-meta">
                  <span>{chunk.source}</span>
                  <span>{scoreLabel(chunk)}</span>
                </span>
                <span className="grade-reason">{chunk.reason}</span>
                {open && chunk.snippet ? <span className="grade-snippet">{chunk.snippet}</span> : null}
                {open && chunk.section ? <span className="grade-section">{chunk.section}</span> : null}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
