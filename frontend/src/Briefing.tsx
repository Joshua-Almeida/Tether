import type { CorpusSource, DeskMode, Health, RetrievalEval } from "./api";

type Props = {
  health: Health | null;
  corpus: CorpusSource[];
  evalResult: RetrievalEval | null;
  evalBusy: boolean;
  evalError: string | null;
  onRunEval: () => void;
  onTry: (question: string, mode: DeskMode) => void;
};

const DEMO = {
  cite: "How many bits is the IPv4 version field, and what does Time to Live mean?",
  refuse: "Who won the 2018 FIFA World Cup?",
};

export default function Briefing({
  health,
  corpus,
  evalResult,
  evalBusy,
  evalError,
  onRunEval,
  onTry,
}: Props) {
  return (
    <article className="briefing">
      <header className="briefing-hero">
        <p className="eyebrow">Briefing</p>
        <h2>Cite the page, or refuse</h2>
        <p>
          Local CRAG over RFC excerpts. If the index cannot support a claim, the desk
          refuses instead of inventing a footnote.
        </p>
      </header>

      <section>
        <p className="eyebrow">Hard parts</p>
        <ul className="brief-list">
          <li>Retrieve always returns neighbors, even for off-corpus questions.</li>
          <li>A bad grade either drops a good chunk or lets junk into generate.</li>
          <li>Rewrite budget is one, so a bad rewrite cannot loop.</li>
          <li>The output gate refuses uncited sentences and invented <code>[n]</code>.</li>
        </ul>
      </section>

      <section>
        <p className="eyebrow">Graph</p>
        <ol className="flow" aria-label="Corrective RAG steps">
          <li>Retrieve</li>
          <li>Grade</li>
          <li>Rewrite or generate</li>
          <li>Refuse gate</li>
        </ol>
        <p>
          Hybrid retrieve, then grade. Relevant passages only go to generate. Naive skips
          the gate so Compare can show the difference.
        </p>
      </section>

      <section>
        <p className="eyebrow">Try</p>
        <div className="brief-actions">
          <button type="button" className="btn btn-primary" onClick={() => onTry(DEMO.cite, "grounded")}>
            Grounded IPv4
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => onTry(DEMO.refuse, "compare")}>
            Compare World Cup
          </button>
        </div>
      </section>

      <section>
        <p className="eyebrow">Corpus</p>
        <p>{health?.index_ready ? "Index ready." : "Upload a file or load the RFC demo."}</p>
        <ul className="corpus">
          {corpus.map((source) => (
            <li key={source.id}>
              <a href={source.url} target="_blank" rel="noreferrer">
                {source.id}
              </a>
              <span>{source.title}</span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <p className="eyebrow">Eval</p>
        <div className="brief-actions">
          <button type="button" className="btn btn-ghost" onClick={onRunEval} disabled={evalBusy}>
            {evalBusy ? "Scoring…" : "Score retrieval gold"}
          </button>
        </div>
        {evalError ? (
          <p className="banner error" role="alert">
            {evalError}
          </p>
        ) : null}
        {evalResult ? (
          <div className="ledger">
            <p className="ledger-score">Recall@k {evalResult.recall.toFixed(2)}</p>
            {evalResult.rows.map((row) => (
              <div key={row.id} className="step">
                <span className="step-label">{row.hit ? "Hit" : "Miss"}</span>
                <b className={row.hit ? "is-answer" : "is-refuse"}>{row.id}</b>
              </div>
            ))}
          </div>
        ) : null}
      </section>
    </article>
  );
}
