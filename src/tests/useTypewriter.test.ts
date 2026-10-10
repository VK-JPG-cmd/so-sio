import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTypewriter } from '../hooks/useTypewriter';

describe('useTypewriter hook', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should type out characters after startDelay', () => {
    const text = 'Hello world';
    const { result } = renderHook(() => useTypewriter(text, { speed: 30, startDelay: 200 }));

    expect(result.current.displayed).toBe('');
    expect(result.current.done).toBe(false);

    // Advance past startDelay
    act(() => {
      vi.advanceTimersByTime(200);
    });

    // Advance 3 characters
    act(() => {
      vi.advanceTimersByTime(90);
    });

    expect(result.current.displayed.length).toBeGreaterThan(0);

    // Advance until complete
    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(result.current.displayed).toBe(text);
    expect(result.current.done).toBe(true);
  });
});
