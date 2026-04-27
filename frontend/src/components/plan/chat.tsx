"use client";

import * as React from "react";
import { Send, Square, User, Bot, AlertTriangle } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import type {
  ChatMessage,
  ClarifyingQuestion,
  StreamStatus,
} from "@/hooks/use-plan-stream";

/* ------------------------------------------------------------------ */
/*  Props                                                              */
/* ------------------------------------------------------------------ */

interface ChatPanelProps {
  messages: ChatMessage[];
  status: StreamStatus;
  pendingQuestions: ClarifyingQuestion[];
  onSubmitAnswers: (answers: Record<string, string>) => void;
  onSendIteration?: (message: string) => void;
  onCancel: () => void;
  editPrompt?: string;
}

/* ------------------------------------------------------------------ */
/*  Message bubble                                                     */
/* ------------------------------------------------------------------ */

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isAssistant = message.role === "assistant";

  return (
    <div
      className={cn(
        "flex gap-3 animate-in-fade",
        isUser && "flex-row-reverse",
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-full",
          isUser
            ? "gradient-bg text-white"
            : isSystem
              ? "bg-[oklch(0.5_0.22_25/0.15)] text-[oklch(0.85_0.18_25)]"
              : "bg-muted text-muted-foreground",
        )}
      >
        {isUser ? (
          <User className="h-3.5 w-3.5" />
        ) : isSystem ? (
          <AlertTriangle className="h-3.5 w-3.5" />
        ) : (
          <Bot className="h-3.5 w-3.5" />
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          "rounded-xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "gradient-bg text-white max-w-[80%]"
            : isSystem
              ? "bg-[oklch(0.5_0.22_25/0.1)] text-[oklch(0.85_0.18_25)] border border-[oklch(0.55_0.22_25/0.25)] max-w-[80%]"
              : "bg-card border border-border text-foreground/90 max-w-[90%]",
        )}
      >
        {isAssistant && message.content ? (
          <div className="prose prose-sm max-w-none 
            prose-headings:font-semibold prose-headings:tracking-tight
            prose-h1:text-base prose-h1:mt-4 prose-h1:mb-2
            prose-h2:text-sm prose-h2:mt-3 prose-h2:mb-2
            prose-h3:text-sm prose-h3:mt-3 prose-h3:mb-1.5
            prose-p:my-2 prose-p:leading-relaxed
            prose-ul:my-2 prose-ul:space-y-1
            prose-ol:my-2 prose-ol:space-y-1
            prose-li:my-0.5
            prose-strong:font-semibold prose-strong:text-foreground
            prose-code:text-xs prose-code:bg-muted/50 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:font-mono prose-code:before:content-none prose-code:after:content-none
            prose-pre:bg-muted/50 prose-pre:border prose-pre:border-border prose-pre:text-xs
            prose-blockquote:border-l-2 prose-blockquote:border-border prose-blockquote:pl-4 prose-blockquote:italic
            prose-hr:border-border prose-hr:my-4
            [&>*:first-child]:mt-0 [&>*:last-child]:mb-0">
            <ReactMarkdown
              components={{
                // Customize heading styles
                h1: (props) => <h1 {...props} />,
                h2: (props) => <h2 {...props} />,
                h3: (props) => <h3 {...props} />,
                // Customize list styles
                ul: (props) => <ul {...props} />,
                ol: (props) => <ol {...props} />,
                // Customize code blocks
                code: (props: { inline?: boolean; className?: string; children?: React.ReactNode }) => {
                  const { inline, children, ...rest } = props;
                  return inline ? (
                    <code {...rest}>{children}</code>
                  ) : (
                    <code className="block overflow-x-auto" {...rest}>{children}</code>
                  );
                },
                // Customize links
                a: (props) => (
                  <a className="text-primary underline underline-offset-2 hover:text-primary/80 transition-colors" target="_blank" rel="noopener noreferrer" {...props} />
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <span>{message.content || '(empty message)'}</span>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Clarifying Questions Form                                          */
/* ------------------------------------------------------------------ */

function ClarifyForm({
  questions,
  onSubmit,
}: {
  questions: ClarifyingQuestion[];
  onSubmit: (answers: Record<string, string>) => void;
}) {
  const [answers, setAnswers] = React.useState<Record<string, string>>({});
  const allAnswered = questions.every(
    (q) => (answers[q.id] ?? "").trim().length > 0,
  );

  return (
    <div className="space-y-4 rounded-xl border border-border bg-card p-4 animate-in-up">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        Clarifying questions
      </p>
      {questions.map((q, i) => (
        <div key={q.id} className="space-y-1.5">
          <label
            htmlFor={`cq-${q.id}`}
            className="text-sm font-medium text-foreground/90"
          >
            {i + 1}. {q.text}
          </label>
          <Input
            id={`cq-${q.id}`}
            value={answers[q.id] ?? ""}
            onChange={(e) =>
              setAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
            }
            placeholder="Your answer..."
            className="text-sm"
          />
        </div>
      ))}
      <Button
        variant="gradient"
        size="sm"
        disabled={!allAnswered}
        onClick={() => onSubmit(answers)}
        className="group"
      >
        Submit answers
        <Send className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
      </Button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Streaming indicator                                                */
/* ------------------------------------------------------------------ */

function StreamingDots() {
  return (
    <div className="flex gap-3 animate-in-fade">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Bot className="h-3.5 w-3.5" />
      </div>
      <div className="flex items-center gap-1.5 rounded-xl bg-card border border-border px-4 py-2.5">
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60 animate-pulse" />
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60 animate-pulse delay-100" />
        <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground/60 animate-pulse delay-200" />
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Main Chat Panel                                                    */
/* ------------------------------------------------------------------ */

export function ChatPanel({
  messages,
  status,
  pendingQuestions,
  onSubmitAnswers,
  onSendIteration,
  onCancel,
  editPrompt,
}: ChatPanelProps) {
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const inputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, status]);

  React.useEffect(() => {
    if (editPrompt && inputRef.current) {
      inputRef.current.value = editPrompt;
      inputRef.current.focus();
    }
  }, [editPrompt]);

  const isStreaming = status === "streaming" || status === "connecting";

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold tracking-tight text-foreground">
          Chat
        </h2>
        {isStreaming && (
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <Square className="h-3 w-3" />
            Stop
          </Button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && (
          <p className="text-center text-sm text-muted-foreground py-12">
            Your conversation will appear here as the advisor works through
            each phase.
          </p>
        )}
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Clarifying questions */}
        {status === "clarifying" && pendingQuestions.length > 0 && (
          <ClarifyForm
            questions={pendingQuestions}
            onSubmit={onSubmitAnswers}
          />
        )}

        {isStreaming && <StreamingDots />}

        <div ref={bottomRef} />
      </div>

      {/* Input area for iterations */}
      {(status === "complete" || status === "idle" || status === "error") && onSendIteration && (
        <div className="border-t border-border p-4">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const form = e.target as HTMLFormElement;
              const input = form.elements.namedItem("message") as HTMLInputElement;
              if (input.value.trim() && onSendIteration) {
                onSendIteration(input.value.trim());
                input.value = "";
              }
            }}
            className="flex gap-2"
          >
            <Input
              ref={inputRef}
              name="message"
              placeholder="E.g., What if I use MongoDB instead?"
              className="flex-1 bg-muted/50"
              autoComplete="off"
            />
            <Button type="submit" size="sm" variant="gradient" className="group px-3">
              <Send className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              <span className="sr-only">Send</span>
            </Button>
          </form>
        </div>
      )}
    </div>
  );
}
