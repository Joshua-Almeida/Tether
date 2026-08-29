import { FormEvent, useEffect, useState } from "react";
import Composer from "./Composer";
import Folio from "./Folio";
import StatusPills from "./StatusPills";
import Trace from "./Trace";
import {
  askQuestion,
  getHealth,
  humanizeError,
  ingestCorpus,
  type AskResponse,
  type Health,
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
];

export default function App() {
  const [question, setQuestion] = useState(EXAMPLES[0].text);
  const [health, setHealth] = useState<Health | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);
  const [busy, setBusy] = useState<"ask" | "ingest" | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    const id = window.setInterval(() => void refreshHealth(), 8000);
    return () => window.clearInterval(id);
  }, []);

  async function onAsk(event: FormEvent) {
    event.preventDefault();
    setBusy("ask");
    setError(null);
    setResult(null);
    try {
      setResult(await askQuestion(question.trim()));
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

  return (
    <div className="shell">
      <header className="masthead">
        <div>
          <p className="wordmark">Tether</p>
          <p className="tagline">
            Answers stay tied to cited passages, or the desk refuses.
          </p>
        </div>
        <StatusPills health={health} />
      </header>

      <main className="desk">
        <Composer
          question={question}
          onQuestion={setQuestion}
          busy={busy}
          error={error}
          examples={EXAMPLES}
          onAsk={onAsk}
          onIngest={() => void onIngest()}
        >
          {result && <Trace result={result} />}
        </Composer>
        <Folio busy={busy} result={result} />
      </main>
    </div>
  );
}
