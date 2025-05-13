import React from 'react';
import { Routes, Route } from 'react-router-dom';
import HomePage from './components/pages/HomePage';
import GeneViewerPage from './components/pages/GeneViewerPage';

const AppRoutes: React.FC = () => {
    return (
        <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/genome/:strainName" element={<GeneViewerPage />} />
            <Route path="/gene" element={<GeneViewerPage />} />
        </Routes>
    );
};

export default AppRoutes; 