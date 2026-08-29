import type { AskResponse } from "./api";

type Props = {
  result: AskResponse;
};

export default function Trace({ result }: Props) {
  const relevant = result.trace.graded.filter((item) => item.relevant).length;
  const rewrite =
    result.trace.rewrite_count > 0
      ? result.trace.rewritten_query || "rewritten"
      : "skipped";

  return (
    <div className="trace">
      <p className="eyebrow">Trace</p>
      <div className="step">
        <span className="step-label">Retrieve</span>
        <b>{result.trace.retrieved_count} chunks</b>
      </div>
      <div className="step">
        <span className="step-label">Grade</span>
        <b>
          {relevant} relevant / {result.trace.graded.length}
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
    </div>
  );
}
