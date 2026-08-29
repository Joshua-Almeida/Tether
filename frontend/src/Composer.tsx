import { FormEvent, ReactNode } from "react";
import ModeChips from "./ModeChips";
import type { DeskMode } from "./api";

export type Example = {
  label: string;
  text: string;
};

type Props = {
  question: string;
  onQuestion: (value: string) => void;
  mode: DeskMode;
  onMode: (mode: DeskMode) => void;
  busy: "ask" | "ingest" | null;
  error: string | null;
  contrast: string | null;
  examples: Example[];
  onAsk: (event: FormEvent) => void;
  onIngest: () => void;
  children?: ReactNode;
};

export default function Composer({
  question,
  onQuestion,
  mode,
  onMode,
  busy,
  error,
  contrast,
  examples,
  onAsk,
  onIngest,
  children,
}: Props) {
  const askLabel =
    busy === "ask" ? "Working…" : mode === "compare" ? "Compare" : "Ask";

  return (
    <section className="blotter">
      <p className="eyebrow">Composer</p>
      <h2>Ask</h2>
      <form onSubmit={onAsk}>
        <ModeChips mode={mode} onMode={onMode} disabled={busy !== null} />
        <label className="field-label" htmlFor="question">
          Question
        </label>
        <textarea
          id="question"
          value={question}
          onChange={(event) => onQuestion(event.target.value)}
        />
        <div className="actions">
          <button className="btn btn-primary" type="submit" disabled={busy !== null}>
            {askLabel}
          </button>
          <button
            className="btn btn-ghost"
            type="button"
            onClick={onIngest}
            disabled={busy !== null}
          >
            {busy === "ingest" ? "Indexing…" : "Ingest corpus"}
          </button>
        </div>
      </form>
      {error && (
        <p className="banner error" role="alert">
          {error}
        </p>
      )}
      {contrast && !error ? (
        <p className="banner contrast" role="status">
          {contrast}
        </p>
      ) : null}
      <div className="examples">
        {examples.map((example) => (
          <button
            key={example.text}
            type="button"
            className="example"
            onClick={() => onQuestion(example.text)}
          >
            <small>{example.label}</small>
            {example.text}
          </button>
        ))}
      </div>
      {children}
    </section>
  );
}
