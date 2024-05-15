import React from 'react';
import UploadForm from '../components/UploadForm';
import { HeaderHome } from '../components/Header';
import '../assets/css/HomePage.css';

const HomePage = () => {
  console.log("API Base URL:", process.env.REACT_APP_API_BASE_URL);
  return (
    <div>
        <HeaderHome />
        <div className="con_logo">
          <img src="/logo.png" alt="로고" />
        </div>
        <div className="content">
          <UploadForm />
        </div>
    </div>
  );
};

export default HomePage;