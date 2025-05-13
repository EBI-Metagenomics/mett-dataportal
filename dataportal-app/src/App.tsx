import React from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { FacetProvider } from './contexts/FacetContext';
import AppRoutes from './routes';
import Header from '@components/organisms/Header/Header';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';
import ErrorBoundary from "@components/atoms/ErrorBoundary";
import Footer from "@components/organisms/Footer/Footer";

const App: React.FC = () => {
    return (
        <div style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
            <Router>
                <FacetProvider>
                    <Header/>
                    <main
                        className="vf-body | vf-stack vf-stack--200"
                        style={{
                            '--vf-body-width': '80em',
                            paddingBottom: '200px',
                        } as React.CSSProperties}
                    >
                        <AppRoutes />
                    </main>
                    <Footer/>
                </FacetProvider>
            </Router>
        </div>
    );
};

export default App;
