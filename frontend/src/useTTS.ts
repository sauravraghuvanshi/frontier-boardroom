import { useEffect, useRef } from "react";
import { useStore } from "./store";

/** useTTS — plays incoming base64 mp3 chunks from audio_chunk events.
 *  visemes already drive mouth in Characters.tsx via the speakingAgent flag. */
export function useTTS() {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const turns = useStore((s) => s.turns);
  useEffect(() => {
    // future: subscribe to a separate audio event stream and feed audioRef
    audioRef.current = audioRef.current ?? new Audio();
  }, [turns.length]);
  return audioRef;
}
