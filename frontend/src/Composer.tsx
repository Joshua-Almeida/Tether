import { FormEvent, ReactNode } from "react";

export type Example = {
  label: string;
  text: string;
};

type Props = {
  question: string;
  onQuestion: (value: string) => void;
  busy: "ask" | "ingest" | null;
  error: string | null;
  examples: Example[];
  onAsk: (event: FormEvent) => void;
  onIngest: () => void;
  children?: ReactNode;
};

export default function Composer({
  question,
  onQuestion,
  busy,
  error,
  examples,
  onAsk,
  onIngest,
  children,
}: Props) {
  return (
    <section className="blotter">
      <p className="eyebrow">Composer</p>
      <h2>Ask the desk</h2>
      <p className="hint">
        Answers stay tied to retrieved passages. If the corpus cannot support a claim, the desk
        refuses.
      </p>
      <form onSubmit={onAsk}>
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
            {busy === "ask" ? "Working…" : "Ask"}
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
