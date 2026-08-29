import type { Health } from "./api";

type Props = {
  health: Health | null;
};

export default function StatusPills({ health }: Props) {
  if (!health) {
    return (
      <div className="status">
        <span className="pill is-warn">Backend unreachable</span>
      </div>
    );
  }

  return (
    <div className="status">
      <span className={`pill ${health.llm_configured ? "is-ok" : "is-warn"}`}>
        {health.llm_configured ? "LLM ready" : "No API key"}
      </span>
      <span className={`pill ${health.index_ready ? "is-ok" : "is-warn"}`}>
        {health.index_ready ? `${health.chunk_count} chunks` : "Index empty"}
      </span>
    </div>
  );
}
