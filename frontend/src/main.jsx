import React, { Suspense, lazy } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ThemeProvider } from './contexts/ThemeContext.jsx'
import ErrorBoundary from './components/ErrorBoundary.jsx'
import App from './App.jsx'
import NewsPage from './pages/NewsPage.jsx'
import './index.css'

// Lazy load HistoryPage for better performance
const HistoryPage = lazy(() => import('./pages/HistoryPage.jsx'))

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<App />} />
            <Route path="/news" element={<NewsPage />} />
            <Route 
              path="/history" 
              element={
                <Suspense fallback={
                  <div className="min-h-screen bg-[#faf9f7] dark:bg-[#1a1a1a] flex items-center justify-center">
                    <div className="text-[#8a8a8a] dark:text-[#a8a29e]">Loading...</div>
                  </div>
                }>
                  <HistoryPage />
                </Suspense>
              } 
            />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
