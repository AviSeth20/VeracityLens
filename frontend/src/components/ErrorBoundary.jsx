import React from 'react'
import { AlertTriangle } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo
    })
    
    // Log error for monitoring
    console.error('ErrorBoundary caught an error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.href = '/'
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#faf9f7] dark:bg-[#1a1a1a] flex items-center justify-center px-4">
          <div className="max-w-md w-full bg-white dark:bg-[#1c1917] border border-red-200 dark:border-red-900/50 rounded-2xl p-8 text-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-950/30 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-8 h-8 text-red-600 dark:text-red-400" />
            </div>
            
            <h2 className="text-xl font-semibold text-[#3a3a3a] dark:text-[#f5f5f5] mb-2">
              Something went wrong
            </h2>
            
            <p className="text-sm text-[#8a8a8a] dark:text-[#a8a29e] mb-6">
              We encountered an unexpected error. Please try refreshing the page.
            </p>

            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details className="text-left mb-6 p-4 bg-red-50 dark:bg-red-950/20 rounded-lg">
                <summary className="text-xs font-medium text-red-700 dark:text-red-400 cursor-pointer mb-2">
                  Error Details
                </summary>
                <pre className="text-xs text-red-600 dark:text-red-500 overflow-auto">
                  {this.state.error.toString()}
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            
            <button
              onClick={this.handleReset}
              className="px-6 py-3 bg-[#d97757] text-white rounded-xl hover:bg-[#c86647] transition-colors font-medium"
            >
              Return to Home
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
