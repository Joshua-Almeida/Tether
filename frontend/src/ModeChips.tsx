import type { DeskMode } from "./api";

const MODES: { id: DeskMode; label: string; hint: string }[] = [
  { id: "grounded", label: "Grounded", hint: "Cite or refuse" },
  { id: "naive", label: "Naive", hint: "Retrieve, then guess" },
  { id: "compare", label: "Compare", hint: "Run both" },
];

type Props = {
  mode: DeskMode;
  onMode: (mode: DeskMode) => void;
  disabled?: boolean;
};

export default function ModeChips({ mode, onMode, disabled }: Props) {
  return (
    <div className="modes" role="radiogroup" aria-label="Pipeline">
      {MODES.map((item) => (
        <button
          key={item.id}
          type="button"
          role="radio"
          aria-checked={mode === item.id}
          className={`mode ${mode === item.id ? "is-on" : ""}`}
          disabled={disabled}
          onClick={() => onMode(item.id)}
        >
          <small>{item.label}</small>
          {item.hint}
        </button>
      ))}
    </div>
  );
}
