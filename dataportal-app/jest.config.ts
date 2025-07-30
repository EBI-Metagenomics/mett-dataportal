import type {Config} from 'jest'

const config: Config = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
    testPathIgnorePatterns: ['/node_modules/', '/dist/'],
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1',
        '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
        '^.*/appConstants$': '<rootDir>/src/utils/__mocks__/appConstants.tsx',
        '^.*/errorHandler$': '<rootDir>/src/utils/__mocks__/errorHandler.ts',
        '^.*/geneViewerConfig$': '<rootDir>/src/utils/__mocks__/geneViewerConfig.ts',
    },
    transform: {
        '^.+\\.(ts|tsx)$': ['ts-jest', {
            tsconfig: 'tsconfig.jest.json',
        }],
    },
}

export default config
