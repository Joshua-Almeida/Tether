import { useState } from "react";
import { warningCopy, type AskResponse } from "./api";

type Props = {
  busy: "ask" | "ingest" | null;
  result: AskResponse | null;
  variant?: "default" | "grounded" | "naive";
};

function scrollToFootnote(id: number, rootId?: string) {
  const scope = rootId ? document.getElementById(rootId) : document;
  const el = scope?.querySelector(`[data-fn="${id}"]`);
  if (!el) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" });
}

function AnswerBody({
  answer,
  activeCite,
  onCite,
  folioId,
}: {
  answer: string;
  activeCite: number | null;
  onCite: (id: number | null) => void;
  folioId?: string;
}) {
  const parts = answer.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (!cite) return <span key={index}>{part}</span>;
    const id = Number(cite[1]);
    return (
      <button
        key={index}
        type="button"
        className={`cite ${activeCite === id ? "is-on" : ""}`}
        aria-label={`Citation ${id}`}
        onMouseEnter={() => onCite(id)}
        onMouseLeave={() => onCite(null)}
        onFocus={() => onCite(id)}
        onBlur={() => onCite(null)}
        onClick={() => {
          onCite(id);
          scrollToFootnote(id, folioId);
        }}
      >
        [{id}]
      </button>
    );
  });
}

export default function Folio({ busy, result, variant = "default" }: Props) {
  const [activeCite, setActiveCite] = useState<number | null>(null);
  const asking = busy === "ask";
  const refused = result?.status === "refused";
  const naive = variant === "naive" || result?.mode === "naive";
  const grounded = variant === "grounded";
  const folioId = variant === "default" ? "folio-main" : `folio-${variant}`;
  const warnings = result?.warnings ?? [];
  const eyebrow = refused && !asking ? "Refused" : naive ? "Naive folio" : grounded ? "Grounded folio" : "Folio";
  const heading = refused && !asking
    ? "The desk will not guess"
    : naive
      ? "Ungated answer"
      : "Cited answer";

  return (
    <section id={folioId} className={`folio ${refused && !asking ? "is-refused" : ""} ${naive && !asking ? "is-naive" : ""}`}>
      <p className="eyebrow">{eyebrow}</p>
      <h2>{heading}</h2>

      {asking && (
        <div className="folio-wait">
          <p className="loading">
            <span className="loading-dot" />
            Working the blotter
          </p>
          <h3>{naive ? "Retrieving, then answering" : "Retrieving, then grading"}</h3>
          <p>
            {naive
              ? "Naive RAG skips the grader and the refuse gate."
              : "A rewrite runs only if no passage is relevant. The folio fills when the graph decides."}
          </p>
        </div>
      )}

      {!result && !asking && (
        <div className="folio-empty">
          <h3>Nothing on the blotter yet</h3>
          <p>
            Ask a question the RFCs can prove, compare it with naive RAG, or try the World Cup
            prompt to see a refusal.
          </p>
        </div>
      )}

      {result && !asking && (
        <>
          {warnings.length > 0 ? (
            <ul className="warn-list">
              {warnings.map((code) => (
                <li key={code}>{warningCopy(code)}</li>
              ))}
            </ul>
          ) : null}
          <p className={`answer ${refused ? "refused" : ""}`}>
            <AnswerBody
              answer={result.answer}
              activeCite={activeCite}
              onCite={setActiveCite}
              folioId={folioId}
            />
          </p>
          {result.citations.length > 0 ? (
            <ol className="footnotes">
              {result.citations.map((citation) => (
                <li
                  key={`${folioId}-${citation.id}`}
                  data-fn={citation.id}
                  className={activeCite === citation.id ? "is-on" : ""}
                >
                  <span className="fn-num">[{citation.id}]</span>
                  <p className="fn-body">
                    <strong>
                      {citation.title} · {citation.source}
                      {citation.section ? ` · ${citation.section}` : ""}
                    </strong>
                    {citation.quote}
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="hint">
              {refused
                ? "No footnotes. The desk refused rather than invent a source."
                : "No footnotes. Naive mode left the answer untethered."}
            </p>
          )}
        </>
      )}
    </section>
  );
}
