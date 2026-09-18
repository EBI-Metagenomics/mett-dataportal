import '@testing-library/jest-dom'

// Mock Vite env variables used in the app
(globalThis as any).import = {
    meta: {
        env: {
            VITE_BASENAME: '/',
            VITE_API_BASE_URL: 'http://localhost:8000',
            VITE_BACINTERACTOME_SHINY_APP_URL: 'http://localhost:3838',
            VITE_JBROWSE_INDEXES_PATH: '/jbrowse-indexes',
            MODE: 'test',
        },
    },
}

// Extend the global interface for import.meta
declare global {
    interface ImportMeta {
        env: {
            VITE_BASENAME: string
            VITE_API_BASE_URL: string
            VITE_BACINTERACTOME_SHINY_APP_URL: string
            VITE_JBROWSE_INDEXES_PATH: string
            MODE: string
        }
    }
}
