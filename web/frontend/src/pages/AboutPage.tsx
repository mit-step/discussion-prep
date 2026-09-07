import { useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { BASE } from "../api/client";
import { useUser } from "../context/UserContext";

/** Reveals its element once, the first time it scrolls into view, then stops watching. */
function useReveal<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T | null>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.unobserve(el);
        }
      },
      { threshold, rootMargin: "0px 0px -10% 0px" },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [threshold]);

  return [ref, visible] as const;
}

function RevealItem({ children, delay = 0 }: { children: ReactNode; delay?: number }) {
  const [ref, visible] = useReveal<HTMLLIElement>();
  return (
    <li ref={ref} className={`reveal-item${visible ? " visible" : ""}`} style={{ transitionDelay: `${delay}ms` }}>
      {children}
    </li>
  );
}

function Section({ n, title, bullets }: { n: string; title: string; bullets: ReactNode[] }) {
  return (
    <section className="about-section" id={`section-${n}`}>
      <div className="about-section-inner">
        <div className="about-eyebrow">{n}</div>
        <h2>{title}</h2>
        <ul className="reveal-list">
          {bullets.map((b, i) => (
            <RevealItem key={i} delay={i * 90}>
              {b}
            </RevealItem>
          ))}
        </ul>
      </div>
    </section>
  );
}

/** A digit strip that spins through a full lap before clicking into place, like a combination lock. */
const DIGIT_STRIP = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];

function Tumbler({ text }: { text: string }) {
  const [ref, visible] = useReveal<HTMLSpanElement>(0.6);
  return (
    <span className="tumbler" ref={ref}>
      {text.split("").map((ch, i) => {
        if (!/[0-9]/.test(ch)) {
          return (
            <span key={i} className={`tumbler-char${visible ? " show" : ""}`} style={{ transitionDelay: `${i * 70}ms` }}>
              {ch}
            </span>
          );
        }
        const digit = Number(ch);
        const steps = 10 + digit;
        return (
          <span className="tumbler-digit" key={i}>
            <span
              className="tumbler-strip"
              style={{
                transform: visible ? `translateY(-${steps}em)` : "translateY(0)",
                transitionDelay: `${i * 70}ms`,
                transitionTimingFunction: `steps(${steps}, end)`,
              }}
            >
              {DIGIT_STRIP.map((d, j) => (
                <span className="tumbler-row" key={j}>
                  {d}
                </span>
              ))}
            </span>
          </span>
        );
      })}
    </span>
  );
}

type FrameKey = "note" | "caseline" | "held";

const FRAMES: Record<FrameKey, { top: number; bottom: number; left: number; right: number }> = {
  note: { top: 19, bottom: 28.5, left: 24.5, right: 76 },
  caseline: { top: 37.8, bottom: 40.2, left: 26.9, right: 73.5 },
  held: { top: 58, bottom: 81, left: 24.5, right: 76 },
};

const CORPUS_STEPS: { frame: FrameKey | null; content: ReactNode }[] = [
  {
    frame: null,
    content: (
      <>
        <p>Fifty-one documents make up the corpus the agent argues from.</p>
        <div className="scrolly-stats">
          <div className="scrolly-stat">
            <span className="scrolly-stat-value">
              <Tumbler text="51" />
            </span>
            <span className="scrolly-stat-label">Documents</span>
          </div>
          <div className="scrolly-stat">
            <span className="scrolly-stat-value">
              ~<Tumbler text="8,600" />
            </span>
            <span className="scrolly-stat-label">Chunks</span>
          </div>
          <div className="scrolly-stat">
            <span className="scrolly-stat-value">
              <Tumbler text="25" />
              MB
            </span>
            <span className="scrolly-stat-label">Before warrants</span>
          </div>
          <div className="scrolly-stat">
            <span className="scrolly-stat-value">
              <Tumbler text="40" />
              MB
            </span>
            <span className="scrolly-stat-label">After warrants</span>
          </div>
        </div>
      </>
    ),
  },
  {
    frame: "note",
    content: (
      <>
        <p className="scrolly-step-kicker">Kelo v. City of New London — a chunk of its own</p>
        <p>
          This two-page reporter syllabus is one document among the 51 — and even inside it, a chunker still has to
          decide where one idea ends and the next begins. The boxed note is its own chunk: boilerplate about the
          Reporter of Decisions, not part of the Court&rsquo;s reasoning, and keeping it separate stops it from
          bleeding into the holding.
        </p>
      </>
    ),
  },
  {
    frame: "caseline",
    content: (
      <>
        <p>
          Three clusters run through the corpus — takings, environmental and administrative law, and environmental
          justice — plus a smaller Massachusetts group.
        </p>
        <p>
          A single line like this one, all docket number and dates, is exactly the kind of dense, low-content chunk
          that gets mis-embedded if it isn&rsquo;t split cleanly from the paragraphs around it.
        </p>
      </>
    ),
  },
  {
    frame: "held",
    content: (
      <>
        <p>
          Chunk counts across the corpus range from 7 to 520 — and the range is informative, not noise. Kelo.pdf is
          only a two-page syllabus, so its dissents never entered the corpus at all.
        </p>
        <p>The case looks thinner here than its real footprint in the reporter — a limit of the source, not the chunker.</p>
      </>
    ),
  },
];

function CorpusScrolly() {
  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const idx = stepRefs.current.indexOf(entry.target as HTMLDivElement);
          if (idx !== -1) setActive(idx);
        });
      },
      { rootMargin: "-42% 0px -42% 0px", threshold: 0 },
    );
    stepRefs.current.forEach((el) => el && observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const activeFrame = CORPUS_STEPS[active]?.frame ?? null;

  return (
    <section className="about-section scrolly-corpus" id="section-02">
      <div className="about-section-inner about-section-header-only">
        <div className="about-eyebrow">02</div>
        <h2>The corpus</h2>
      </div>
      <div className="scrolly-flex">
        <div className="scrolly-sticky">
          <div className="scrolly-image-wrap">
            <img src={`${BASE}/kelo-syllabus.png`} alt="Kelo v. City of New London, official syllabus, page 1" />
            {(Object.keys(FRAMES) as FrameKey[]).map((key) => {
              const box = FRAMES[key];
              return (
                <div
                  key={key}
                  className={`scrolly-frame${activeFrame === key ? " visible" : ""}`}
                  style={{
                    top: `${box.top}%`,
                    left: `${box.left}%`,
                    right: `${100 - box.right}%`,
                    bottom: `${100 - box.bottom}%`,
                  }}
                />
              );
            })}
          </div>
          <p className="scrolly-caption">Kelo v. City of New London — official syllabus, page 1</p>
        </div>
        <div className="scrolly-steps">
          {CORPUS_STEPS.map((step, i) => (
            <div
              className="scrolly-step"
              id={`corpus-step-${i}`}
              key={i}
              ref={(el) => {
                stepRefs.current[i] = el;
              }}
            >
              <div className={`scrolly-step-card${active === i ? " active" : ""}`}>{step.content}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function AboutPage() {
  const { user } = useUser();
  const backTo = user ? "/library" : "/login";
  const backLabel = user ? "← Library" : "← Log in";

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <header className="app-header">
        <Link to={backTo} className="secondary" style={{ textDecoration: "none", padding: "0.5rem 1.1rem", border: "1px solid var(--border)", borderRadius: "8px", color: "var(--muted)" }}>
          {backLabel}
        </Link>
        <h1>About</h1>
        <div className="app-header-actions" />
      </header>

      <main className="about-page">
        <section className="about-hero">
          <div className="about-eyebrow">Discussion Prep · 11.268 Laws of the Land</div>
          <h1>Rehearsing an argument until it holds.</h1>
          <p className="about-hero-sub">
            A retrospective on building a Socratic sparring partner for urban planning students — the corpus it
            argues from, the warrants it extracts, and the bugs that quietly got it wrong.
          </p>
          <div className="about-scroll-cue" aria-hidden="true">
            <span />
          </div>
        </section>

        <Section
          n="01"
          title="What we built"
          bullets={[
            "Discussion Prep helps students rehearse for in-class discussion.",
            <>
              11.268: Laws of the Land equips urban planners with the legal knowledge they need in practice, and
              discussion is integral: students must present and defend a coherent, precise argument.
            </>,
            "The tool lets them rehearse that argument and hold their stance when counterarguments are raised.",
            <>
              Originally conceived for memo evaluation, now built around a three-round session divided into
              phases. Phases make grading easier and mirror how rubrics are already structured.
            </>,
          ]}
        />

        <CorpusScrolly />

        <Section
          n="03"
          title="Chunks"
          bullets={[
            <>
              Docling HybridChunker over MarkItDown: flat markdown has no item tree, and the chunker walks the
              DoclingDocument structure to avoid splitting mid-table or mid-list.
            </>,
            <>
              The tokenizer must be loaded via <code>AutoTokenizer.from_pretrained</code> matching the embedding
              model, or token counts diverge from what the embedder sees.
            </>,
          ]}
        />

        <Section
          n="04"
          title="Retrieval"
          bullets={[
            "Weighted RRF over BM25 and vector search, with opposite weights on the two paths.",
            <>
              The inversion is principled, not tuned: groundedness needs exact terms so lexical dominates; warrant
              matching needs the same rule stated in different vocabulary so dense dominates.
            </>,
            <>
              <code>k_candidates</code> must exceed <code>k_final</code>, or fusion has nothing to fuse.
            </>,
          ]}
        />

        <Section
          n="05"
          title="Warrants"
          bullets={[
            <>
              Every argument rests on a warrant, the unstated rule licensing premises to conclusion. Extract it
              from both the student and the readings, then match warrant to warrant.
            </>,
            <>
              Chosen over fallacy classification: fallacies fire on a minority of turns, every argument has a
              warrant, and a wrong fallacy label is a pedagogical harm.
            </>,
            "A second derived index over the same chunks, not a replacement for topic retrieval.",
          ]}
        />

        <Section
          n="06"
          title="Schema design"
          bullets={[
            <>
              Derived versus source of truth: warrant tables are droppable and rebuilt whenever the prompt
              changes, which made two full rebuilds cheap.
            </>,
            <>
              <code>held_by</code> split into <code>rule_from</code> and <code>reaction_from</code>, because
              refusing needs a refuser and one column cannot hold both.
            </>,
            <>
              <code>distinguished</code> is not <code>refused</code>: the rule is valid but does not reach these
              facts.
            </>,
          ]}
        />

        <Section
          n="07"
          title="Prompt engineering"
          bullets={[
            <>
              The affirmative-statement rule, the highest-impact single change: before it, <code>refused</code>{" "}
              never fired, because rules stated as denials made the model conflate negation with stance.
            </>,
            <>
              Explicit permission to return nothing, since most chunks are footnotes and procedural history — 62%
              empty on a law review article.
            </>,
            <>
              Acknowledge (praise) before challenging, in three places: the Socratic agent, the challenge opening,
              and hardcoded <code>should_concede</code>.
            </>,
          ]}
        />

        <Section
          n="08"
          title="Bugs that produced silent wrong behavior"
          bullets={[
            <>
              FTS5 treats a space-separated MATCH as implicit AND, so a full sentence matched nothing and hybrid
              ran dense-only with no error.
            </>,
            <>
              Stance-blindness: reaction records what a passage did to a rule, not how it stands to a student, so{" "}
              <code>refused</code> returned passages that agreed with a student rejecting the rule.
            </>,
            <>
              Both share a root with the affirmative-statement rule: a rule&rsquo;s content and the stance toward
              it are separate, and collapsing them produces wrong labels.
            </>,
          ]}
        />

        <Section
          n="09"
          title="Leakage"
          bullets={[
            "Passing the student's claim into generation reintroduced the case names the warrant strip had removed.",
            <>
              <em>Loper Bright</em>, a fisheries case, was described as being about the EPA;{" "}
              <em>Lujan</em>, a standing case, drew a question about power plant emissions.
            </>,
            <>
              Over-connection rather than invention. Stripping identifiers from one field is pointless if another
              puts them back.
            </>,
          ]}
        />

        <Section
          n="10"
          title="Results"
          bullets={[
            "Fusion earns its place: dense ranked the best result second, lexical third, hybrid promoted it to first.",
            <>
              Cross-doctrinal retrieval: an SB 375 climate planning argument was challenged with{" "}
              <em>Rapanos</em>, a Clean Water Act case, because both turn on whether text constrains an agency —
              zero topical overlap.
            </>,
            "Label distribution corpus-wide, with challenge pool size.",
          ]}
        />

        <Section
          n="11"
          title="The knowledge graph"
          bullets={[
            "Three node types, with hollow circles for cases the syllabus leans on but never assigns.",
            <>
              Regex over LLM extraction: free and deterministic, self-normalizing on reporter cites, but misses
              articles cited by author and year.
            </>,
            <>
              Filtering finding: 1,087 external cases drop to 125 once you require more than a single mention —
              most of what an article cites, it cites once in a footnote.
            </>,
          ]}
        />

        <Section
          n="12"
          title="Known limitations"
          bullets={[
            <>
              <code>rule_from</code> mixes genuine third-party positions with unattributed doctrine; steelman and
              strawman are indistinguishable.
            </>,
            "Footnote import and reversed holdings both present other courts' law as controlling.",
            <>
              Nothing is validated: no labeled set, no held-out evaluation, single runs. Every improvement was
              judged by reading output.
            </>,
          ]}
        />

        <Section
          n="13"
          title="Future work"
          bullets={[
            "Week-scoped retrieval, so week 3 is not challenged with week 11.",
            "Voice, more rounds, and groundedness checking on generated challenges.",
            "Showing the source passage alongside the challenge, so a hallucination is visible rather than authoritative.",
          ]}
        />

        <Section
          n="14"
          title="Architecture"
          bullets={[
            <>
              One shared SQLite DB in WAL mode; <code>mvp.db</code> is the read-only ingestion artifact,{" "}
              <code>app.db</code> holds users and transcripts.
            </>,
            "MCP servers planned and dropped once no agent was moderating the conversation.",
            "Parley as the gateway, with structured output prompted and validated client-side rather than enforced.",
          ]}
        />

        <section className="about-closing" id="about-closing">
          <div className="about-section-inner">
            <h2>Ready to defend your case?</h2>
            <p>Pick a reading and see how long your position holds up.</p>
            <Link to={backTo} className="about-closing-cta">
              {user ? "Go to the library →" : "Log in to start →"}
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
