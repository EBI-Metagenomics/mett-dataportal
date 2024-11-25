import React from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import Header from '@components/organisms/Header/Header';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';
import ErrorBoundary from "@components/atoms/ErrorBoundary";
import Footer from "@components/organisms/Footer/Footer";

const App: React.FC = () => {
    return (
        <div style={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
            <Router>
                <Header/>
                <main
                    className="vf-body | vf-stack vf-stack--200"
                    style={{
                        '--vf-body-width': '80em',
                        paddingBottom: '200px',
                    } as React.CSSProperties}
                >
                    <Routes>
                        <Route path="/" element={<HomePage/>}/>
                        <Route path="/home" element={<HomePage/>}/>
                        <Route path="/genome/:strainName" element={
                            <ErrorBoundary>
                                <GeneViewerPage/>
                            </ErrorBoundary>
                        }/>
                    </Routes>
                </main>
                <Footer/>
            </Router>
        </div>
    );
};

export default App;
