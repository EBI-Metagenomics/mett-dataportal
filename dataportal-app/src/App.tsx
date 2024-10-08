import React from 'react';
import {BrowserRouter as Router, Route, Routes} from 'react-router-dom';
import Header from './components/Header/Header';
import Footer from './components/Footer/Footer';
import HomePage from './components/HomePage/HomePage';
import JBrowseViewer from "@components/JBrowseViewer/JBrowseViewer";

const App: React.FC = () => {
  return (
    <Router>
      <Header />
      <main className="vf-body | vf-stack vf-stack--200">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/jbrowse/:isolateId" element={<JBrowseViewer />} />
          {/* Add other routes here */}
        </Routes>
      </main>
      <Footer />
    </Router>
  );
};

export default App;
