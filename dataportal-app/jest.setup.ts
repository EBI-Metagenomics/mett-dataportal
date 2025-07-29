import '@testing-library/jest-dom'

// Mock Vite env variables used in the app
(globalThis as any).import = {
    meta: {
        env: {
            VITE_BASENAME: '/',
            VITE_API_BASE_URL: 'http://localhost:8000',
        },
    },
}
