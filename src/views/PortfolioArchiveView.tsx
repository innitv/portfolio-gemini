import * as React from "react"

import { m } from "framer-motion"

import { ArchiveSheet } from "@/components/portfolio/archive/archive-sheet"
import { InteractiveLogoMark } from "@/components/portfolio/archive/InteractiveLogoMark"
import { DURATION, EASE, TIMING } from "@/components/portfolio/motion"

import { archiveCompanies, type ArchiveCompany } from "./portfolio-archive.model"
import { contacts, profile, type CompanyId } from "./portfolio.data"

import "@/styles/portfolio-archive.css"

const REVEAL_ORDER = {
  top: 0,
  logo: 1,
  lead: 2,
  worksLabel: 3,
  line: 3,
  companyBase: 4,
} as const

const REVEAL_STAGGER = TIMING.revealStagger
const REVEAL_DURATION = DURATION.reveal
const EASE_REVEAL = EASE.item
const FONTS_TIMEOUT = 600

export interface PortfolioArchiveViewProps {
  /** Компания, синий экран которой раскрыт (`/` — ни одной, `/a3` — А3). */
  companyId?: CompanyId
  /** Показать синий экран сразу открытым, без спуска. */
  instant?: boolean
  /** Содержимое синего экрана уже показано — лесенка не играет. */
  revealed?: boolean
  /** Закрытие синего экрана: маршрут уходит на главную. */
  onCloseCompany?: () => void
  /** Раскрытие компании нажатием на её имя: маршрут уходит на `/<companyId>`. */
  onOpenCompany?: (companyId: CompanyId) => void
  /** Переход на страницу кейса. */
  onOpenCase?: (companyId: CompanyId, caseId: string) => void
}

export function PortfolioArchiveView({
  companyId: openId,
  instant = true,
  revealed = false,
  onCloseCompany,
  onOpenCompany,
  onOpenCase,
}: PortfolioArchiveViewProps) {
  const [ready, setReady] = React.useState(false)

  React.useEffect(() => {
    let cancelled = false
    const timer = window.setTimeout(() => {
      if (!cancelled) setReady(true)
    }, FONTS_TIMEOUT)

    void document.fonts.ready
      .catch(() => undefined)
      .then(() => {
        if (!cancelled) setReady(true)
      })

    return () => {
      cancelled = true
      window.clearTimeout(timer)
    }
  }, [])

  const company: ArchiveCompany | undefined = archiveCompanies.find((item) => item.id === openId)
  const cellsRef = React.useRef(new Map<CompanyId, HTMLButtonElement>())

  React.useEffect(() => {
    const root = document.documentElement
    const previous = root.dataset.portfolioSurface
    root.dataset.portfolioSurface = "archive"

    return () => {
      if (previous === undefined) delete root.dataset.portfolioSurface
      else root.dataset.portfolioSurface = previous
    }
  }, [])

  const screenRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const screen = screenRef.current
    if (!screen) return

    screen.inert = Boolean(openId)

    return () => {
      screen.inert = false
    }
  }, [openId])

  const closeCompany = React.useCallback(() => {
    if (screenRef.current) screenRef.current.inert = false
    if (openId) cellsRef.current.get(openId)?.focus()
    onCloseCompany?.()
  }, [onCloseCompany, openId])

  const reveal = (index: number) => ({
    animate: ready ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 },
    initial: { opacity: 0, y: 10 },
    transition: {
      delay: ready ? index * REVEAL_STAGGER : 0,
      duration: REVEAL_DURATION,
      ease: EASE_REVEAL,
    },
  })

  const drawLineX = (index: number) => ({
    animate: ready ? { scaleX: 1, opacity: 1 } : { scaleX: 0, opacity: 0 },
    initial: { scaleX: 0, opacity: 0 },
    transition: {
      delay: ready ? index * REVEAL_STAGGER : 0,
      duration: REVEAL_DURATION,
      ease: EASE_REVEAL,
    },
  })

  const drawLineY = (index: number) => ({
    animate: ready ? { scaleY: 1, opacity: 1 } : { scaleY: 0, opacity: 0 },
    initial: { scaleY: 0, opacity: 0 },
    transition: {
      delay: ready ? index * REVEAL_STAGGER : 0,
      duration: REVEAL_DURATION,
      ease: EASE_REVEAL,
    },
  })

  return (
    <div className="pa-root" data-testid="pa-root">
      <div className="pa-screen" ref={screenRef}>
        <m.header className="pa-top" data-testid="pa-top" {...reveal(REVEAL_ORDER.top)}>
          <div className="pa-brand">
            <svg
              aria-hidden="true"
              className="pa-top-logo"
              fill="none"
              viewBox="0 0 32 22"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path d="M0 0H7.5V15.5L15.5 7.5V22H8L0 14V0Z" fill="currentColor" />
              <path d="M16.5 0H24L32 8V22H24.5V6.5L16.5 14.5V0Z" fill="currentColor" />
            </svg>
            <div className="pa-brand-text">
              <span className="pa-brand-name">{profile.name}</span>
              <h1 className="pa-brand-title" data-testid="pa-word">
                {profile.title}
              </h1>
            </div>
          </div>

          <span className="pa-contacts" data-testid="pa-contacts">
            {contacts.map((channel) => (
              <a
                className="pa-contact"
                href={channel.href}
                key={channel.label}
                rel={channel.external ? "noreferrer" : undefined}
                target={channel.external ? "_blank" : undefined}
              >
                {channel.label}
              </a>
            ))}
          </span>
        </m.header>

        <section className="pa-hero">
          <div className="pa-hero-centerpiece">
            <InteractiveLogoMark className="pa-hero-logo" revealProps={reveal(REVEAL_ORDER.logo)} />
            <m.p className="pa-hero-lead" {...reveal(REVEAL_ORDER.lead)}>
              {profile.lead}
            </m.p>
          </div>

          <div className="pa-works" data-testid="pa-works">
            <m.div className="pa-works-label" {...reveal(REVEAL_ORDER.worksLabel)}>
              компании и кейсы
            </m.div>
            <div className="pa-row">
              <m.span
                aria-hidden="true"
                className="pa-row-top-line"
                {...drawLineX(REVEAL_ORDER.line)}
              />
              {archiveCompanies.map((item, index) => (
                <React.Fragment key={item.id}>
                  {index > 0 ? (
                    <m.span
                      aria-hidden="true"
                      className="pa-sep"
                      {...drawLineY(REVEAL_ORDER.companyBase + index)}
                    />
                  ) : null}
                  <m.button
                    className="pa-cell"
                    data-testid={`pa-company-${item.id}`}
                    onClick={() => onOpenCompany?.(item.id)}
                    ref={(node) => {
                      if (node) cellsRef.current.set(item.id, node)
                      else cellsRef.current.delete(item.id)
                    }}
                    type="button"
                    {...reveal(REVEAL_ORDER.companyBase + index)}
                  >
                    <span className="pa-cell-head">
                      <span className="pa-meta">{item.meta}</span>
                    </span>
                    <span className="pa-name">{item.wordmark}</span>
                    <m.span
                      aria-hidden="true"
                      className="pa-cell-rail"
                      {...drawLineX(REVEAL_ORDER.companyBase + index)}
                    />
                  </m.button>
                </React.Fragment>
              ))}
            </div>
          </div>
        </section>
      </div>

      <ArchiveSheet
        company={company}
        instant={instant}
        onClose={closeCompany}
        onOpenCase={onOpenCase}
        revealed={revealed}
      />
    </div>
  )
}
