// src/hooks/useWebSocket.ts
import { useEffect, useRef } from "react";
import { serverMessageSchema } from "../schemas/messages";

export function useWebSocket(
  url: string,
  onMessage: (msg: ReturnType<typeof serverMessageSchema.parse>) => void
) {
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket(url);
    socketRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        // Validate
        const parsed = serverMessageSchema.parse(data);
        onMessage(parsed);
      } catch (error) {
        console.error("WS parse/validation error:", error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    return () => {
      ws.close();
    };
  }, [url, onMessage]);

  function sendMessage(message: unknown) {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  }

  return { sendMessage };
}
