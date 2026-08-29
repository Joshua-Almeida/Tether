import { DragEvent, useRef } from "react";
import type { LibrarySource } from "./api";

type Props = {
  sources: LibrarySource[];
  busy: "ask" | "ingest" | "upload" | null;
  onUpload: (files: File[]) => void;
  onRemove: (sourceId: string) => void;
  onLoadDemo: () => void;
};

export default function Library({ sources, busy, onUpload, onRemove, onLoadDemo }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const blocked = busy !== null;

  function takeFiles(list: FileList | File[] | null) {
    const files = list ? Array.from(list) : [];
    if (files.length) onUpload(files);
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    if (!blocked) takeFiles(event.dataTransfer.files);
  }

  return (
    <aside className="shelf">
      <p className="eyebrow">Shelf</p>
      <h2>Documents</h2>
      <input
        ref={inputRef}
        id="upload-files"
        className="file-input"
        type="file"
        accept=".pdf,.txt,.md,.markdown,application/pdf,text/plain,text/markdown"
        multiple
        disabled={blocked}
        onChange={(event) => {
          takeFiles(event.target.files);
          event.target.value = "";
        }}
      />
      <label
        htmlFor="upload-files"
        className={`drop ${blocked ? "is-off" : ""}`}
        onDragOver={(event) => event.preventDefault()}
        onDrop={onDrop}
      >
        {busy === "upload" ? "Indexing…" : "Drop a PDF or text file, or click to upload"}
      </label>
      <button
        type="button"
        className="btn btn-ghost"
        onClick={onLoadDemo}
        disabled={blocked}
      >
        {busy === "ingest" ? "Indexing…" : "Load RFC demo"}
      </button>
      <ul className="shelf-list">
        {sources.map((source) => (
          <li key={source.id}>
            <div>
              <strong>{source.title}</strong>
              <small>{source.origin === "demo" ? "Demo" : "Upload"}</small>
            </div>
            <button
              type="button"
              className="linkish"
              aria-label={`Remove ${source.title}`}
              disabled={blocked}
              onClick={() => onRemove(source.id)}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </aside>
  );
}
