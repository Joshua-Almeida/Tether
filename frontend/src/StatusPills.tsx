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

  if (!health.llm_configured) {
    return (
      <div className="status">
        <span className="pill is-warn">No API key</span>
      </div>
    );
  }

  return (
    <div className="status">
      <span className="pill is-ok">Ready</span>
    </div>
  );
}
