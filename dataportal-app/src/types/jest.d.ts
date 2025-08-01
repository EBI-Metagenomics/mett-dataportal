import '@testing-library/jest-dom'

declare global {
    namespace jest {
        interface Matchers<R> {
            toBeInTheDocument(): R
            toBeChecked(): R
            toHaveLength(length: number): R
        }
    }
} 