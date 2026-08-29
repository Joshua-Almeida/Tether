import { FormEvent, useEffect, useMemo, useState } from "react";
import { askQuestion, getHealth, ingestCorpus, type AskResponse, type Health } from "./api";

const EXAMPLES = [
  {
    label: "Grounded",
    text: "How many bits is the IPv4 version field, and what does Time to Live mean?",
  },
  {
    label: "Grounded",
    text: "What default TCP ports do the http and https URI schemes use?",
  },
  {
    label: "Should refuse",
    text: "Who won the 2018 FIFA World Cup?",
  },
];

function renderAnswer(answer: string) {
  const parts = answer.split(/(\[\d+\])/g);
  return parts.map((part, index) => {
    const cite = part.match(/^\[(\d+)\]$/);
    if (!cite) return <span key={index}>{part}</span>;
    return (
      <sup key={index} className="cite">
        [{cite[1]}]
      </sup>
    );
  });
}

export default function App() {
  const [question, setQuestion] = useState(EXAMPLES[0].text);
  const [health, setHealth] = useState<Health | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [busy, setBusy] = useState<"ask" | "ingest" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshHealth() {
    try {
      setHealth(await getHealth());
    } catch (err) {
      setHealth(null);
      setError(err instanceof Error ? err.message : "Backend is not reachable.");
    }
  }

  useEffect(() => {
    void refreshHealth();
  }, []);

  const relevantCount = useMemo(
    () => result?.trace.graded.filter((item) => item.relevant).length ?? 0,
    [result]
  );

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    setBusy("ask");
    setError(null);
    try {
      setResult(await askQuestion(question.trim()));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ask failed.");
    } finally {
      setBusy(null);
    }
  }

  async function onIngest() {
    setBusy("ingest");
    setError(null);
    try {
      await ingestCorpus();
      await refreshHealth();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ingest failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="shell">
      <header className="masthead">
        <div>
          <p className="wordmark">
            Grounded <em>RAG</em>
          </p>
          <p className="tagline">Cite-or-refuse research Q&amp;A over a local RFC corpus.</p>
        </div>
        <div className="status">
          <span className={`pill ${health?.llm_configured ? "is-ok" : "is-warn"}`}>
            {health?.llm_configured ? "LLM ready" : "No API key"}
          </span>
          <span className={`pill ${health?.index_ready ? "is-ok" : "is-warn"}`}>
            {health?.index_ready ? `${health.chunk_count} chunks` : "Index empty"}
          </span>
        </div>
      </header>

      <main className="desk">
        <section className="blotter">
          <p className="eyebrow">Composer</p>
          <h2>Ask the desk</h2>
          <p className="hint">Answers must quote retrieved passages. If the corpus cannot support a claim, the graph refuses.</p>
          <form onSubmit={onAsk}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              aria-label="Question"
            />
            <div className="actions">
              <button className="btn btn-primary" type="submit" disabled={busy !== null}>
                {busy === "ask" ? "Working…" : "Ask"}
              </button>
              <button
                className="btn btn-ghost"
                type="button"
                onClick={() => void onIngest()}
                disabled={busy !== null}
              >
                {busy === "ingest" ? "Indexing…" : "Ingest corpus"}
              </button>
            </div>
          </form>
          {error && <p className="banner error">{error}</p>}
          <div className="examples">
            {EXAMPLES.map((example) => (
              <button
                key={example.text}
                type="button"
                className="example"
                onClick={() => setQuestion(example.text)}
              >
                <small>{example.label}</small>
                {example.text}
              </button>
            ))}
          </div>
          {result && (
            <div className="trace">
              <div className="step">
                <span>Retrieve</span>
                <b>{result.trace.retrieved_count} chunks</b>
              </div>
              <div className="step">
                <span>Grade</span>
                <b>{relevantCount} relevant</b>
              </div>
              <div className="step">
                <span>Rewrite</span>
                <b>{result.trace.rewrite_count ? result.trace.rewritten_query : "skipped"}</b>
              </div>
              <div className="step">
                <span>Decision</span>
                <b>{result.trace.decision}</b>
              </div>
            </div>
          )}
        </section>

        <section className="folio">
          <p className="eyebrow">Folio</p>
          <h2>Cited answer</h2>
          {busy === "ask" && (
            <p className="loading">
              <span className="loading-dot" />
              Retrieving, grading, rewriting if needed
            </p>
          )}
          {!result && busy !== "ask" && (
            <div className="folio-empty">
              <h3>Nothing on the blotter yet</h3>
              <p>Ask a question the RFCs can prove, or try the World Cup prompt to see a refusal.</p>
            </div>
          )}
          {result && (
            <>
              <p className={`answer ${result.status === "refused" ? "refused" : ""}`}>
                {renderAnswer(result.answer)}
              </p>
              {result.citations.length > 0 ? (
                <ol className="footnotes">
                  {result.citations.map((citation) => (
                    <li key={citation.id}>
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
                <p className="hint">No footnotes. The graph refused rather than guess.</p>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}
