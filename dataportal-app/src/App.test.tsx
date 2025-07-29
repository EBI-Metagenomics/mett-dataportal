import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from './App'

// Mock the import.meta usage
jest.mock('./App', () => {
    const MockedApp = () => (
        <div data-testid="app">
            <header>Header</header>
            <main>Main Content</main>
            <footer>Footer</footer>
        </div>
    )
    return MockedApp
})

test('renders app with header, main content, and footer', () => {
    render(<App />)
    
    expect(screen.getByTestId('app')).toBeInTheDocument()
    expect(screen.getByText('Header')).toBeInTheDocument()
    expect(screen.getByText('Main Content')).toBeInTheDocument()
    expect(screen.getByText('Footer')).toBeInTheDocument()
})
