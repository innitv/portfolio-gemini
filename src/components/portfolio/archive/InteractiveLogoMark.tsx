import * as React from "react"

import { m } from "framer-motion"

import { DURATION, EASE } from "@/components/portfolio/motion"

// 1) Стартовые ровные буквы «И» «И» (10 вершин)
const LEFT_LETTER_I =
  "M0 0L2.8 0L2.8 16.5L11.7 0L14.5 0L14.5 22L11.7 22L11.7 5.5L2.8 22L0 22Z"
const RIGHT_LETTER_I =
  "M17.5 0L20.3 0L20.3 16.5L29.2 0L32 0L32 22L29.2 22L29.2 5.5L20.3 22L17.5 22Z"

// 2) Два цельных утолщённых блока до срезов 45° (10 вершин)
const LEFT_FULL_BLOCK =
  "M0 0L7.5 0L7.5 0L11.5 0L15.5 0L15.5 22L11.75 22L10.5 22L8 22L0 22Z"
const RIGHT_FULL_BLOCK =
  "M16.5 0L20.25 0L24 0L32 0L32 8L32 22L24.5 22L24.5 22L16.5 22L16.5 22Z"

// 3) Финальный знак после всех 4 срезов под 45°
const LEFT_FINAL =
  "M0 0L7.5 0L7.5 15.5L11.5 11.5L15.5 7.5L15.5 22L11.75 22L10.5 22L8 22L0 14Z"
const RIGHT_FINAL =
  "M16.5 0L20.25 0L24 0L28 4L32 8L32 22L24.5 22L24.5 6.5L16.5 14.5L16.5 14.5Z"

// Все 4 отрезаемых фрагмента (2 внешних угла + 2 внутренних выреза, как в logo-story)
const LEFT_CUT_CORNER = "M0 14L8 22H0Z"
const LEFT_CUT_INNER = "M7.5 0H15.5V7.5L7.5 15.5Z"
const RIGHT_CUT_CORNER = "M24 0H32V8Z"
const RIGHT_CUT_INNER = "M16.5 14.5L24.5 6.5V22H16.5Z"

const CROSSHAIRS: [number, number][] = [
  [0, 0],
  [32, 0],
  [0, 22],
  [32, 22],
]

const TOTAL_DURATION_MS = 2700

/**
 * Полная пошаговая история из `logo-story`:
 *   1) Старт: две чёткие буквы «И» «И».
 *   2) Морфинг: буквы утолщаются в два цельных блока в сетке 32×22.
 *   3) 4 среза под 45° (2 внешних и 2 внутренних): все 4 лишних фрагмента
 *      отсекаются и уходят в стороны, оставляя чистый знак «ИИ».
 */
export function InteractiveLogoMark({
  className,
  revealProps,
}: {
  className?: string
  revealProps?: Record<string, unknown>
}) {
  const [playing, setPlaying] = React.useState(false)
  const [cycle, setCycle] = React.useState(0)
  const timerRef = React.useRef<number | null>(null)

  React.useEffect(() => {
    return () => {
      if (timerRef.current !== null) window.clearTimeout(timerRef.current)
    }
  }, [])

  const triggerStory = () => {
    if (playing) return
    setPlaying(true)
    setCycle((c) => c + 1)
    timerRef.current = window.setTimeout(() => {
      setPlaying(false)
      timerRef.current = null
    }, TOTAL_DURATION_MS)
  }

  return (
    <m.div
      className="pa-hero-logo-wrap"
      onClick={triggerStory}
      onMouseEnter={triggerStory}
      title="Нажми или наведи, чтобы увидеть все 4 среза сборки знака из «И И»"
      {...revealProps}
    >
      <svg
        aria-hidden="true"
        className={className}
        fill="none"
        viewBox="-5 -5 42 33"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Строительная сетка 32×22 и угловые крестики */}
        <m.g
          animate={playing ? { opacity: [0, 0.85, 0.85, 0] } : { opacity: 0 }}
          initial={{ opacity: 0 }}
          transition={{ duration: 2.65, times: [0, 0.08, 0.88, 1], ease: EASE.item }}
        >
          {[0, 8, 16, 24, 32].map((x) => (
            <line
              key={`vx-${x}`}
              stroke="currentColor"
              strokeOpacity="0.2"
              strokeWidth="0.16"
              x1={x}
              x2={x}
              y1="-2"
              y2="24"
            />
          ))}
          {[0, 7.5, 14.5, 22].map((y) => (
            <line
              key={`hy-${y}`}
              stroke="currentColor"
              strokeOpacity="0.2"
              strokeWidth="0.16"
              x1="-2"
              x2="34"
              y1={y}
              y2={y}
            />
          ))}
          {CROSSHAIRS.map(([cx, cy]) => (
            <g key={`ch-${cx}-${cy}`} stroke="currentColor" strokeOpacity="0.55" strokeWidth="0.22">
              <line x1={cx - 1.1} x2={cx + 1.1} y1={cy} y2={cy} />
              <line x1={cx} x2={cx} y1={cy - 1.1} y2={cy + 1.1} />
            </g>
          ))}
        </m.g>

        {/* Морфинг: И И → цельные блоки → отсечённый финальный знак */}
        <m.path
          animate={
            playing
              ? {
                  d: [
                    LEFT_FINAL,
                    LEFT_LETTER_I,
                    LEFT_LETTER_I,
                    LEFT_FULL_BLOCK,
                    LEFT_FULL_BLOCK,
                    LEFT_FINAL,
                  ],
                }
              : {
                  d: LEFT_FINAL,
                }
          }
          fill="currentColor"
          initial={{ d: LEFT_FINAL }}
          transition={
            playing
              ? { duration: 2.55, times: [0, 0.09, 0.26, 0.52, 0.60, 0.61], ease: EASE.item }
              : { duration: DURATION.reveal, ease: EASE.item }
          }
        />

        <m.path
          animate={
            playing
              ? {
                  d: [
                    RIGHT_FINAL,
                    RIGHT_LETTER_I,
                    RIGHT_LETTER_I,
                    RIGHT_FULL_BLOCK,
                    RIGHT_FULL_BLOCK,
                    RIGHT_FINAL,
                  ],
                }
              : {
                  d: RIGHT_FINAL,
                }
          }
          fill="currentColor"
          initial={{ d: RIGHT_FINAL }}
          transition={
            playing
              ? { duration: 2.55, times: [0, 0.09, 0.26, 0.52, 0.60, 0.61], ease: EASE.item }
              : { duration: DURATION.reveal, ease: EASE.item }
          }
        />

        {/* ПОСЛЕ морфинга (~1.55 с): 4 линии реза 45° и 4 отлетающих фрагмента */}
        {playing ? (
          <m.g key={`axes-${cycle}`}>
            {/* Внешние углы */}
            <m.path
              animate={{ opacity: [0, 0.72, 0.72, 0], x: [0, 0, -3.2], y: [0, 0, 3.2] }}
              d={LEFT_CUT_CORNER}
              fill="currentColor"
              initial={{ opacity: 0 }}
              transition={{ duration: 0.98, delay: 1.54, times: [0, 0.08, 0.6, 1], ease: EASE.item }}
            />
            <m.path
              animate={{ opacity: [0, 0.72, 0.72, 0], x: [0, 0, 3.2], y: [0, 0, -3.2] }}
              d={RIGHT_CUT_CORNER}
              fill="currentColor"
              initial={{ opacity: 0 }}
              transition={{ duration: 0.98, delay: 1.54, times: [0, 0.08, 0.6, 1], ease: EASE.item }}
            />

            {/* Центральные/внутренние вырезы */}
            <m.path
              animate={{ opacity: [0, 0.52, 0.52, 0], y: [0, 0, -3.4] }}
              d={LEFT_CUT_INNER}
              fill="currentColor"
              initial={{ opacity: 0 }}
              transition={{ duration: 0.98, delay: 1.56, times: [0, 0.08, 0.6, 1], ease: EASE.item }}
            />
            <m.path
              animate={{ opacity: [0, 0.52, 0.52, 0], y: [0, 0, 3.4] }}
              d={RIGHT_CUT_INNER}
              fill="currentColor"
              initial={{ opacity: 0 }}
              transition={{ duration: 0.98, delay: 1.56, times: [0, 0.08, 0.6, 1], ease: EASE.item }}
            />

            {/* 4 направляющие линии реза 45° (2 внешних + 2 внутренних) */}
            <m.line
              animate={{ pathLength: [0, 1, 1], opacity: [0, 0.85, 0] }}
              initial={{ pathLength: 0, opacity: 0 }}
              stroke="currentColor"
              strokeDasharray="0.7 0.7"
              strokeWidth="0.26"
              transition={{ duration: 0.9, delay: 1.38, ease: EASE.item }}
              x1="-1.5"
              x2="10.5"
              y1="12.5"
              y2="24.5"
            />
            <m.line
              animate={{ pathLength: [0, 1, 1], opacity: [0, 0.85, 0] }}
              initial={{ pathLength: 0, opacity: 0 }}
              stroke="currentColor"
              strokeDasharray="0.7 0.7"
              strokeWidth="0.26"
              transition={{ duration: 0.9, delay: 1.4, ease: EASE.item }}
              x1="6.5"
              x2="16.5"
              y1="16.5"
              y2="6.5"
            />
            <m.line
              animate={{ pathLength: [0, 1, 1], opacity: [0, 0.85, 0] }}
              initial={{ pathLength: 0, opacity: 0 }}
              stroke="currentColor"
              strokeDasharray="0.7 0.7"
              strokeWidth="0.26"
              transition={{ duration: 0.9, delay: 1.42, ease: EASE.item }}
              x1="15.5"
              x2="25.5"
              y1="15.5"
              y2="5.5"
            />
            <m.line
              animate={{ pathLength: [0, 1, 1], opacity: [0, 0.85, 0] }}
              initial={{ pathLength: 0, opacity: 0 }}
              stroke="currentColor"
              strokeDasharray="0.7 0.7"
              strokeWidth="0.26"
              transition={{ duration: 0.9, delay: 1.44, ease: EASE.item }}
              x1="21.5"
              x2="33.5"
              y1="-2.5"
              y2="9.5"
            />
            <m.text
              animate={{ opacity: [0, 0.8, 0] }}
              fill="currentColor"
              fontFamily="var(--pa-mono)"
              fontSize="1.65"
              initial={{ opacity: 0 }}
              transition={{ duration: 0.9, delay: 1.42, ease: EASE.item }}
              x="-3.5"
              y="25.5"
            >
              45°
            </m.text>
          </m.g>
        ) : null}
      </svg>
    </m.div>
  )
}
