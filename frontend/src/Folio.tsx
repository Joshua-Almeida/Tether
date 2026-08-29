import { useState } from "react";
import type { AskResponse } from "./api";

type Props = {
  busy: "ask" | "ingest" | null;
  result: AskResponse | null;
};

function scrollToFootnote(id: number) {
  const el = document.getElementById(`fn-${id}`);
  if (!el) return;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "nearest" });
}

function AnswerBody({
  answer,
  activeCite,
  onCite,
}: {
  answer: string;
  activeCite: number | null;
  onCite: (id: number | null) => void;
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
          scrollToFootnote(id);
        }}
      >
        [{id}]
      </button>
    );
  });
}

export default function Folio({ busy, result }: Props) {
  const [activeCite, setActiveCite] = useState<number | null>(null);
  const asking = busy === "ask";
  const refused = result?.status === "refused";

  return (
    <section className={`folio ${refused && !asking ? "is-refused" : ""}`}>
      <p className="eyebrow">{refused && !asking ? "Refused" : "Folio"}</p>
      <h2>{refused && !asking ? "The desk will not guess" : "Cited answer"}</h2>

      {asking && (
        <div className="folio-wait">
          <p className="loading">
            <span className="loading-dot" />
            Working the blotter
          </p>
          <h3>Retrieving, then grading</h3>
          <p>A rewrite runs only if no passage is relevant. The folio fills when the graph decides.</p>
        </div>
      )}

      {!result && !asking && (
        <div className="folio-empty">
          <h3>Nothing on the blotter yet</h3>
          <p>
            Ask a question the RFCs can prove, or try the World Cup prompt to see a refusal.
          </p>
        </div>
      )}

      {result && !asking && (
        <>
          <p className={`answer ${refused ? "refused" : ""}`}>
            <AnswerBody answer={result.answer} activeCite={activeCite} onCite={setActiveCite} />
          </p>
          {result.citations.length > 0 ? (
            <ol className="footnotes">
              {result.citations.map((citation) => (
                <li
                  key={citation.id}
                  id={`fn-${citation.id}`}
                  className={activeCite === citation.id ? "is-on" : ""}
                >
                  <span className="fn-num">[{citation.id}]</span>
                  <p className="fn-body">
                    <strong>
                      {citation.title} · {citation.source}
                    </strong>
                    {citation.quote}
                  </p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="hint">No footnotes. The desk refused rather than invent a source.</p>
          )}
        </>
      )}
    </section>
  );
}
