import { FormEvent, useEffect, useState } from "react";
import Briefing from "./Briefing";
import Composer from "./Composer";
import Folio from "./Folio";
import StatusPills from "./StatusPills";
import Trace from "./Trace";
import {
  askQuestion,
  compareQuestion,
  getCorpus,
  getHealth,
  getRetrievalEval,
  humanizeError,
  ingestCorpus,
  type AskResponse,
  type CompareResponse,
  type CorpusSource,
  type DeskMode,
  type Health,
  type RetrievalEval,
} from "./api";

const EXAMPLES = [
  {
    label: "Should cite",
    text: "How many bits is the IPv4 version field, and what does Time to Live mean?",
  },
  {
    label: "Should cite",
    text: "What default TCP ports do the http and https URI schemes use?",
  },
  {
    label: "Should refuse",
    text: "Who won the 2018 FIFA World Cup?",
  },
  {
    label: "Compare this",
    text: "What is Apple's current stock price?",
  },
];

type View = "desk" | "briefing";

export default function App() {
  const [view, setView] = useState<View>("desk");
  const [question, setQuestion] = useState(EXAMPLES[0].text);
  const [mode, setMode] = useState<DeskMode>("grounded");
  const [health, setHealth] = useState<Health | null>(null);
  const [corpus, setCorpus] = useState<CorpusSource[]>([]);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [compare, setCompare] = useState<CompareResponse | null>(null);
  const [busy, setBusy] = useState<"ask" | "ingest" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evalResult, setEvalResult] = useState<RetrievalEval | null>(null);
  const [evalBusy, setEvalBusy] = useState(false);
  const [evalError, setEvalError] = useState<string | null>(null);

  async function refreshHealth() {
    try {
      setHealth(await getHealth());
      setError((current) =>
        current?.startsWith("The desk cannot reach the API") ? null : current
      );
    } catch (err) {
      setHealth(null);
      setError(
        humanizeError(
          err,
          "The desk cannot reach the API. Start the backend on 127.0.0.1:8000."
        )
      );
    }
  }

  useEffect(() => {
    void refreshHealth();
    void getCorpus()
      .then((payload) => setCorpus(payload.sources))
      .catch(() => setCorpus([]));
    const id = window.setInterval(() => void refreshHealth(), 8000);
    return () => window.clearInterval(id);
  }, []);

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    setBusy("ask");
    setError(null);
    setResult(null);
    setCompare(null);
    try {
      const q = question.trim();
      if (mode === "compare") {
        setCompare(await compareQuestion(q));
      } else {
        setResult(await askQuestion(q, mode));
      }
    } catch (err) {
      setError(humanizeError(err, "The desk could not finish that question."));
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
      setError(humanizeError(err, "Indexing failed. Check embedding keys and try again."));
    } finally {
      setBusy(null);
    }
  }

  async function onRunEval() {
    setEvalBusy(true);
    setEvalError(null);
    try {
      setEvalResult(await getRetrievalEval());
    } catch (err) {
      setEvalError(humanizeError(err, "Retrieval eval needs an ingested index."));
    } finally {
      setEvalBusy(false);
    }
  }

  function onTry(nextQuestion: string, nextMode: DeskMode) {
    setQuestion(nextQuestion);
    setMode(nextMode);
    setView("desk");
    setResult(null);
    setCompare(null);
    setError(null);
  }

  return (
    <div className="shell">
      <header className="masthead">
        <div>
          <p className="wordmark">Tether</p>
          <p className="tagline">
            Answers stay tied to cited passages, or the desk refuses.
          </p>
        </div>
        <div className="mast-end">
          <nav className="nav" aria-label="Desk sections">
            <button
              type="button"
              className={`nav-btn ${view === "desk" ? "is-on" : ""}`}
              aria-current={view === "desk" ? "page" : undefined}
              onClick={() => setView("desk")}
            >
              Desk
            </button>
            <button
              type="button"
              className={`nav-btn ${view === "briefing" ? "is-on" : ""}`}
              aria-current={view === "briefing" ? "page" : undefined}
              onClick={() => setView("briefing")}
            >
              Briefing
            </button>
          </nav>
          <StatusPills health={health} />
        </div>
      </header>

      {view === "briefing" ? (
        <Briefing
          health={health}
          corpus={corpus}
          evalResult={evalResult}
          evalBusy={evalBusy}
          evalError={evalError}
          onRunEval={() => void onRunEval()}
          onTry={onTry}
        />
      ) : (
        <main className={`desk ${compare ? "is-compare" : ""}`}>
          <Composer
            question={question}
            onQuestion={setQuestion}
            mode={mode}
            onMode={setMode}
            busy={busy}
            error={error}
            contrast={compare?.contrast ?? null}
            examples={EXAMPLES}
            onAsk={onAsk}
            onIngest={() => void onIngest()}
          >
            {result && <Trace result={result} />}
            {compare && (
              <>
                <Trace result={compare.grounded} title="Grounded trace" />
                <Trace result={compare.naive} title="Naive trace" />
              </>
            )}
          </Composer>
          {compare || (mode === "compare" && busy === "ask") ? (
            <div className="folio-pair">
              <Folio busy={busy} result={compare?.grounded ?? null} variant="grounded" />
              <Folio busy={busy} result={compare?.naive ?? null} variant="naive" />
            </div>
          ) : (
            <Folio busy={busy} result={result} />
          )}
        </main>
      )}
    </div>
  );
}
