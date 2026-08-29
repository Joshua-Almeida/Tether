# Design

Instructions for the Tether desk UI. Tokens live in `frontend/src/styles.css` (`:root`). New color, type, radius, and space values must be variables. Do not invent a second palette in components.

## Metaphor

The product is a **research desk**, not a chat product and not a dashboard.

- **Composer** (left, dark walnut blotter): the question, actions, examples, and pipeline trace. This is the working surface.
- **Folio** (right, parchment): the cited answer, footnotes, empty/loading/refused states. This is what you would take away from the desk.

One question, one folio. No thread history, no settings island, no marketing landing page.

## Tokens

Match `styles.css`. Do not copy Daily paper/cobalt or Studio woven blue into this table.

| Token | Value | Use |
|---|---|---|
| `--desk` | `#14110e` | Page / walnut field |
| `--desk-raised` | `#1d1915` | Composer blotter |
| `--desk-sunken` | `#0e0c0a` | Textarea well |
| `--desk-glow` | verdigris wash | Ambient desk light |
| `--folio` | `#f3ead8` | Parchment panel |
| `--folio-ink` | `#2a241c` | Answer text |
| `--folio-mute` | `#6d6456` | Folio secondary |
| `--folio-rule` / `--folio-dash` | ink at 12% / 20% | Folio hairlines |
| `--parchment` | `#ebe3d3` | Desk body text |
| `--parchment-mute` | `#b3aa98` | Desk secondary |
| `--hairline` | `rgba(235, 227, 211, 0.1)` | Rules on walnut |
| `--hairline-strong` | `rgba(235, 227, 211, 0.22)` | Stronger desk edges |
| `--verdigris` | `#7eb8a4` | Single accent |
| `--verdigris-deep` | `#4e8f7c` | Accent on parchment |
| `--verdigris-tint` | `rgba(126, 184, 164, 0.14)` | Focus ring / cite highlight |
| `--verdigris-ink` | `#10211b` | Text on primary button |
| `--clay` | `#c98972` | Warn / error on desk |
| `--clay-deep` | `#8a4e3a` | Refused answer on parchment |
| `--clay-tint` / `--clay-deep-tint` | clay washes | Error banner, refused folio edge |
| `--font-display` | Fraunces, Palatino fallback | Wordmark, folio answer, section titles |
| `--font-body` | Figtree, Segoe UI fallback | UI copy |
| `--font-mono` | IBM Plex Mono | Eyebrows, pills, cites, loading |
| `--radius` | `12px` | Inputs, examples, banners |
| `--radius-lg` | `20px` | Blotter and folio |
| `--space-1` … `--space-5` | 6 / 10 / 16 / 24 / 40px | Rhythm |
| `--hit` | `42px` | Buttons and pills |
| `--shadow-folio` | soft drop under parchment | Folio only — desk uses hairlines |
| `--ease` | `cubic-bezier(0.2, 0.8, 0.2, 1)` | Motion |

## Type roles

- **Display serif** — wordmark **Tether**, blotter/folio `h2`, the answer body.
- **Body sans** — tagline, hints, example text, footnotes.
- **Mono uppercase** — eyebrows (`Composer`, `Folio`), status pills, example labels, loading line. Letter-spacing about `0.14em`–`0.16em`.

Do not use Outfit. Do not use Geist. One accent: verdigris.

## Layout

- Shell max width ~1180px, horizontal padding `--space-4` (tighter on small screens).
- **Two columns** on desktop: composer `~0.92fr`, folio `~1.08fr`, gap `--space-5`.
- **Stack below 860px**: folio under composer. Masthead stacks; pills stay visible.
- Hit targets on buttons: **42–44px** min-height, pill radius `999px`.
- No nested card-in-card. Group with hairlines and spacing, not inner panels.

## Components

- **Primary button** — verdigris fill, pill, 1px hover lift. Label is a verb (`Ask`, `Ingest corpus`).
- **Ghost button** — transparent, `--hairline-strong` border, parchment text.
- **Examples** — dashed hairline rows, mono label + body question. Click fills the composer; it does not submit.
- **Pills** — LLM ready / No API key, chunk count / Index empty. Ok = verdigris, warn = clay.
- **Footnotes** — ordered list, mono `[n]`, title · source, quote. Click or hover from `[n]` in the answer should highlight the matching note when cheap.
- **Trace** — retrieve / grade / rewrite / decision as labeled rows, not a nested card.

If you add a dropdown, **do not use a native `<select>`**. Match Tether chips or a custom list (same mono labels, hairline, 42px rows).

## States (first-class)

| State | Where | Behavior |
|---|---|---|
| Empty folio | parchment | Dashed inset, italic display title, short hint (RFC question vs World Cup refuse) |
| Loading | folio, not only the Ask button | Finished-looking wait: mono uppercase line + pulse dot. Button may also say Working… |
| Error | composer banner | Human sentence. Never dump raw JSON or FastAPI `detail` arrays |
| Backend down | pills + banner | Unreachable copy; page must still render |
| Refused | folio | Distinct from cited answers (clay family). No fake footnotes |
| Cited answer | folio | Display serif + `[n]` superscripts + footnote list |

## Motion

- Duration **180ms**, easing `--ease`.
- Hover lift **1px** (`translateY(-1px)`), not more.
- Loading pulse on the folio dot.
- `@media (prefers-reduced-motion: reduce)`: no transform/animation on buttons and the loading dot.

## Accessibility

- Question textarea has a visible label or `aria-label`.
- Icon-only controls need `aria-label` (none required today).
- Focus: verdigris border + `3px` `--verdigris-tint` ring on the textarea; buttons must show `:focus-visible`.
- Parchment contrast: `--folio-ink` on `--folio` for the answer; `--folio-mute` only for secondary. Do not put parchment-mute-sized body on walnut as the only copy for errors — use the clay banner.
- Color is not the only refuse signal: copy + missing footnotes.

## Anti-clone

Tether is a walnut desk and a parchment folio. It is **not**:

- Daily — warm newspaper paper, cobalt, Outfit, Woven blue, roman-numeral section headers, recruiter toolkit grid.
- Studio — social-generator chrome, Outfit-on-canvas, woven-blue primary, shadcn dashboard shell.

Steal **principles** only: CSS variables, hairlines over heavy shadows, 42–44px pills, mono uppercase eyebrows, one accent, empty/loading/error as designed states, reduced motion, human errors.

Voice: precise, no exclamation marks, no emoji. Wordmark is **Tether**. Tagline: answers stay tied to cited passages, or the desk refuses.
