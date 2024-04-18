import React from 'react';
import UploadForm from '../components/UploadForm';
import { HeaderHome } from '../components/Header';
import '../assets/css/HomePage.css';

const HomePage = () => {
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