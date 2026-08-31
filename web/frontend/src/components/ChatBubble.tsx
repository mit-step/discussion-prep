import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export type BubbleRole = "ai" | "student" | "system";

export function ChatBubble({ role, text }: { role: BubbleRole; text: string }) {
  if (role === "ai") {
    return (
      <div className="bubble ai">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
      </div>
    );
  }
  return <div className={`bubble ${role}`}>{text}</div>;
}
