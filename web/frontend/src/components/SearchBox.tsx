import { useEffect, useRef, useState } from "react";

const DEBOUNCE_MS = 350;

export function SearchBox({ onQueryChange }: { onQueryChange: (query: string) => void }) {
  const [value, setValue] = useState("");
  const timeoutRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    window.clearTimeout(timeoutRef.current);
    timeoutRef.current = window.setTimeout(() => onQueryChange(value), DEBOUNCE_MS);
    return () => window.clearTimeout(timeoutRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="search-box">
      <span className="search-icon" aria-hidden="true">
        🔍
      </span>
      <input
        type="text"
        placeholder="Search readings…"
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
    </div>
  );
}
