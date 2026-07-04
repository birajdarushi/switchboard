import type { Metadata } from 'next'
import type { ReactNode } from 'react'
import { ThemeProvider } from '@/components/theme-provider'
import { SiteHeader } from '@/components/site-header'
import './globals.scss'

export const metadata: Metadata = {
  title: 'Switchboard Capital \u2014 Agent Fleet',
  description:
    'A multi-agent IC-memo pipeline: 4 cooperating agents screen VC deals, catch bad data and misbehaving agents, and ship only human-approved memos with a full append-only audit trail.',
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <SiteHeader />
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
