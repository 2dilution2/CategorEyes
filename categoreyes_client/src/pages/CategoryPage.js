import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { fetchCategoriesBySession } from '../api/apiService';
import '../assets/css/CategoryPage.css'; // 스타일은 별도의 CSS 파일로 관리

const CategoryPage = () => {
  const { session_id } = useParams();
  const [categories, setCategories] = useState([]);

  const labelMap = {
    "a photo of a human": "인물",
    "a landscape photo": "풍경",
    "a photo of an animal": "동물",
    "a photo of food": "음식",
    "a photo of a document": "문서",
    "a photo of something else": "기타"
  };

  useEffect(() => {
    fetchCategoriesBySession(session_id)
      .then(response => {
        const categoryArray = Object.entries(response.categories_info).map(([category, imageUrl]) => ({
          category: category,  // 영문 레이블 유지
          imageUrl
        }));
        setCategories(categoryArray);
      })
      .catch(error => console.error('Failed to fetch categories', error));
  }, [session_id]);

  // const downloadCategory = (categoryName) => {
    // 다운로드 URL은 서버 구성에 따라 조정이 필요할 수 있습니다.
  //   navigate(`/download/${categoryName}`);
  // };

  return (
    <div>
      <h1>카테고리</h1>
      <div className="category-container">
        {categories.map(({ category, imageUrl }, index) => (
          <div className="category" key={index}>
            <h2>{labelMap[category] || category}</h2> {/* 한글 레이블로 표시 */}
            <a href={`/categories/${category}/${session_id}`}>
              <img src={imageUrl} alt={category} />
            </a>
            {/* <button onClick={() => downloadCategory(category)}>다운로드 {labelMap[category] || category}</button> 한글 레이블로 표시 */}
          </div>
        ))}
      </div>
    </div>
  );
};

export default CategoryPage;