import { createParser, type EventSourceMessage } from "eventsource-parser";
import type { SseEvent } from "./types";

/**
 * Stream a fetch Response body as a sequence of Server-Sent Events.
 *
 * Yields one parsed `SseEvent` per `event:` block. Unknown events are
 * skipped silently so the frontend never crashes on a new server-side
 * event type it hasn't been taught about yet.
 */
export async function* parseSseStream(
  response: Response,
): AsyncGenerator<SseEvent, void, unknown> {
  if (!response.body) {
    throw new Error("Response has no body to stream from");
  }

  const queue: SseEvent[] = [];
  let done = false;

  const parser = createParser({
    onEvent(message: EventSourceMessage) {
      if (!message.event) return;
      try {
        const parsed = JSON.parse(message.data || "{}") as Record<string, unknown>;
        queue.push({
          event: message.event,
          phase_id: (parsed.phase_id as string | null | undefined) ?? null,
          data: (parsed.data as Record<string, unknown> | undefined) ?? parsed,
        } as SseEvent);
      } catch {
        // Skip malformed JSON payloads rather than break the stream.
      }
    },
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (!done) {
    const { value, done: streamDone } = await reader.read();
    if (streamDone) {
      done = true;
    } else if (value) {
      parser.feed(decoder.decode(value, { stream: true }));
    }

    while (queue.length > 0) {
      yield queue.shift()!;
    }
  }
}
