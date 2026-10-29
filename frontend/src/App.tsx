import { useState } from 'react'
import type { Screen } from './components/Layout'
import { Layout } from './components/Layout'
import { AccuracyView } from './pages/AccuracyView'
import { DecisionView } from './pages/DecisionView'

export default function App() {
  const [screen, setScreen] = useState<Screen>('decision')

  return (
    <Layout screen={screen} onScreenChange={setScreen}>
      {screen === 'decision' ? <DecisionView /> : <AccuracyView />}
    </Layout>
  )
}
