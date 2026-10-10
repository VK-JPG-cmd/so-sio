import { useState, useEffect } from 'react';

interface UseTypewriterOptions {
  speed?: number;
  startDelay?: number;
}

export function useTypewriter(
  text: string,
  { speed = 38, startDelay = 600 }: UseTypewriterOptions = {}
) {
  const [displayed, setDisplayed] = useState('');
  const [done, setDone] = useState(false);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    let charIndex = 0;

    const delayTimeout = setTimeout(() => {
      intervalId = setInterval(() => {
        if (charIndex < text.length) {
          setDisplayed(text.slice(0, charIndex + 1));
          charIndex++;
        } else {
          setDone(true);
          if (intervalId) clearInterval(intervalId);
        }
      }, speed);
    }, startDelay);

    return () => {
      clearTimeout(delayTimeout);
      if (intervalId) clearInterval(intervalId);
    };
  }, [text, speed, startDelay]);

  return { displayed, done };
}
