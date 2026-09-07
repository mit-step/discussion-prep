import { useEffect, useRef, useState } from "react";

const DEBOUNCE_MS = 350;

export function SearchBox({ onQueryChange }: { onQueryChange: (query: string) => void }) {
  const [value, setValue] = useState("");
  const [expanded, setExpanded] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    window.clearTimeout(timeoutRef.current);
    timeoutRef.current = window.setTimeout(() => onQueryChange(value), DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  function expand() {
    setExpanded(true);
    requestAnimationFrame(() => inputRef.current?.focus());
  }

  function collapseIfEmpty() {
    if (!value.trim()) setExpanded(false);
  }

  return (
    <div
      className={`search-box${expanded ? " expanded" : ""}`}
      onClick={!expanded ? expand : undefined}
    >
      <span className="search-icon" aria-hidden="true">
        🔍
      </span>
      <input
        ref={inputRef}
        type="text"
        placeholder="Search readings…"
        value={value}
        onFocus={() => setExpanded(true)}
        onBlur={collapseIfEmpty}
        onChange={(e) => setValue(e.target.value)}
      />
    </div>
  );
}
