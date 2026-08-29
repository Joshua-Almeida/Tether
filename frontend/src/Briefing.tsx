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
  ports: "What default TCP ports do the http and https URI schemes use?",
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
        <h2>Cite the page, or refuse the question</h2>
        <p>
          Tether is a local Corrective RAG desk over IETF RFC excerpts. It exists to make
          uncited generation visible: either every long sentence hangs on a retrieved passage,
          or the folio stays empty. That is the product, not a chatbot with sources attached
          after the fact.
        </p>
      </header>

      <section>
        <p className="eyebrow">Purpose</p>
        <h3>What this webapp is for</h3>
        <p>
          Fluent language models invent plausible facts. A typical RAG demo hides that by
          always answering and sprinkling leftover chunks underneath. Tether inverts the
          contract. The corpus is small and known (IPv4, TCP, URI, HTTP). If a claim is not
          in those pages, the desk says so. You can show a reviewer the difference in one
          click: grounded refuse versus naive “France won.”
        </p>
        <p>
          Use it as a research desk, not a chat log. One question, one folio, a pipeline
          trace you can read aloud. The briefing is the script. The blotter is the proof.
        </p>
      </section>

      <section>
        <p className="eyebrow">Difficulty</p>
        <h3>What is actually hard</h3>
        <ul className="brief-list">
          <li>
            <strong>Retrieval is not understanding.</strong> Dense search returns nearest
            neighbors even for the World Cup. Something always comes back. The hard part is
            deciding those neighbors are irrelevant.
          </li>
          <li>
            <strong>Grading is a second model call with its own failure mode.</strong> A
            relevant chunk marked false triggers rewrite or refuse. A junk chunk marked true
            becomes a footnote. The threshold is 0.5; a sloppy high score still poisons
            generate.
          </li>
          <li>
            <strong>Rewrite can make retrieval worse.</strong> Budget is one. That is
            deliberate. Infinite rewrite looks smart on a slide and loops in production.
          </li>
          <li>
            <strong>Citations are easy to fake.</strong> Models emit <code>[1]</code> and
            then add a second sentence from memory. Grounded mode refuses long uncited
            sentences, invented ids, and <code>REFUSE</code> from the generator itself.
          </li>
          <li>
            <strong>Embeddings must match the index.</strong> Change the embedding model
            without re-ingest and every neighbor is noise. Hybrid BM25 is there so exact
            tokens (IHL, 443, SYN) are not left to paraphrase luck.
          </li>
        </ul>
      </section>

      <section>
        <p className="eyebrow">How it works</p>
        <h3>The grounded graph</h3>
        <ol className="flow" aria-label="Corrective RAG steps">
          <li>Retrieve</li>
          <li>Grade</li>
          <li>Rewrite or generate</li>
          <li>Refuse gate</li>
        </ol>
        <p>
          Ask hits a LangGraph state machine. Retrieve pulls <code>k=6</code> chunks with
          hybrid search: dense vectors plus BM25, fused with reciprocal rank fusion. An LLM
          grades each chunk. If any chunk is relevant, generate sees only those passages,
          numbered <code>[1]…</code>. If none are relevant and the rewrite budget remains,
          the question is rewritten once and retrieve runs again. If the budget is spent,
          refuse. After generate, a deterministic gate still refuses when citations do not
          match or a long sentence has no <code>[n]</code>.
        </p>
        <p>
          That last gate is not another graph. It is a faithfulness check on the way out.
          Naive mode skips grade, rewrite, and the gate so you can show the ablation.
        </p>
      </section>

      <section>
        <p className="eyebrow">Two modes</p>
        <h3>Why compare exists</h3>
        <p>
          Interviewers have seen “RAG + citations.” They have not always seen the same
          question answered two ways. Compare runs grounded CRAG and naive retrieve-then-
          generate on one prompt and writes the contrast on the blotter.
        </p>
        <div className="brief-actions">
          <button type="button" className="btn btn-primary" onClick={() => onTry(DEMO.cite, "grounded")}>
            Grounded IPv4
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => onTry(DEMO.refuse, "compare")}>
            Compare World Cup
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => onTry(DEMO.ports, "grounded")}>
            HTTP ports
          </button>
        </div>
      </section>

      <section>
        <p className="eyebrow">Corpus</p>
        <h3>What the desk can actually know</h3>
        <p>
          Four RFC excerpts on disk. No web search, no hosted database. Chroma lives at
          <code> backend/data/chroma</code>
          {health?.chunk_count ? ` · ${health.chunk_count} chunks indexed` : " · index empty until you ingest"}
          .
        </p>
        <ul className="corpus">
          {(corpus.length ? corpus : []).map((source) => (
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
        <p className="eyebrow">Measurement</p>
        <h3>How we know it is working</h3>
        <p>
          Gold lives in <code>backend/evals/gold.json</code>. Retrieval hit means every
          required RFC appears in the top-k. Citation precision wants every <code>[n]</code>
          to map to a returned footnote. Faithfulness refuses long uncited sentences.
          Refusal accuracy wants out-of-corpus questions to produce no footnotes.
        </p>
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
            <p className="ledger-score">
              Source recall@k {evalResult.recall.toFixed(2)}
            </p>
            {evalResult.rows.map((row) => (
              <div key={row.id} className="step">
                <span className="step-label">{row.hit ? "Hit" : "Miss"}</span>
                <b className={row.hit ? "is-answer" : "is-refuse"}>{row.id}</b>
              </div>
            ))}
          </div>
        ) : (
          <p className="hint">
            Retrieval scoring needs an ingested index and the embedding key. Full faith and
            refuse scores still run from <code>python evals/run_eval.py</code>.
          </p>
        )}
      </section>

      <section>
        <p className="eyebrow">Talk track</p>
        <h3>What to say while you click</h3>
        <ol className="brief-list numbered">
          <li>
            Open the desk. Ingest if the chunk pill is empty. Point at hybrid retrieve and
            the local index — no Postgres, no hosted vector DB.
          </li>
          <li>
            Run the IPv4 question in grounded mode. Walk retrieve → grade → generate. Open
            a passage row in the trace. Click a <code>[n]</code> and land on the footnote.
          </li>
          <li>
            Switch to Compare and run the World Cup prompt. Nearest neighbors still return.
            Grades should mark them irrelevant. Rewrite once. Refuse. Naive will still
            answer. That sentence is the project.
          </li>
          <li>
            If a grounded answer ever refuses on an RFC question, read the reason:
            <code>graded_irrelevant</code>, <code>uncited_sentences</code>, or
            <code>citation_mismatch</code>. Those are product decisions, not crashes.
          </li>
        </ol>
      </section>
    </article>
  );
}
