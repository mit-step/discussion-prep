import { useEffect, useState } from "react";

export function LoadingBubble({ label }: { label: string }) {
  const [dots, setDots] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => setDots((d) => (d + 1) % 4), 450);
    return () => window.clearInterval(timer);
  }, []);

  return <div className="bubble ai loading">{label + ".".repeat(dots)}</div>;
}
