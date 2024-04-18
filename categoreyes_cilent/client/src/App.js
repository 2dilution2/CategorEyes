import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import HomePage from './pages/HomePage';
import CategoryPage from './pages/CategoryPage';
import ImagesPage from './pages/ImagesPage';
import UploadedImages from './pages/uploadedImages'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/uploaded_images/:session_id" element={<UploadedImages />} />
        <Route path="/categories/:session_id" element={<CategoryPage />} />
        <Route path="/categories/:category/:session_id" element={<ImagesPage />} />
      </Routes>
    </Router>
  );
}

export default App;
