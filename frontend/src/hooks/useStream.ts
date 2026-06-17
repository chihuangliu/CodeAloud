import { useRef, useCallback } from 'react'

interface StreamCallbacks {
  onChunk: (text: string) => void
  onDone: (data?: Record<string, unknown>) => void
  onError: (err: Error) => void
}

export function useStream() {
  const esRef = useRef<EventSource | null>(null)

  const start = useCallback((url: string, body: unknown, callbacks: StreamCallbacks) => {
    // EventSource doesn't support POST; use fetch with ReadableStream instead
    esRef.current?.close()

    fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const reader = res.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })

          const lines = buffer.split('\n')
          buffer = lines.pop() ?? ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            const raw = line.slice(6).trim()
            if (!raw) continue
            try {
              const parsed = JSON.parse(raw)
              if (parsed.done) {
                callbacks.onDone(parsed)
              } else if (parsed.text) {
                callbacks.onChunk(parsed.text)
              }
            } catch {
              // malformed chunk — skip
            }
          }
        }
      })
      .catch(callbacks.onError)
  }, [])

  const stop = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
  }, [])

  return { start, stop }
}
