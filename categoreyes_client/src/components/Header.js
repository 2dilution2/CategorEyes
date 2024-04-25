import React from 'react';
import logo from '../assets/img/logo.png';
import '../assets/css/Header.css';

export const Header = () => {
  return (
    <header className="app-header">
      <img src={logo} alt="CategorEyes 로고" className="app-logo" />
      {/* 여기에 다른 네비게이션 요소들을 추가할 수 있습니다 */}
    </header>
  );
};

export const HeaderHome = () => {
  return (
    <header className="app-header-home">
      {/* 여기에 Home 전용 요소들을 추가할 수 있습니다 */}
    </header>
  );
};