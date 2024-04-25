import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ImageGrid from '../components/ImageGrid';
import { fetchImagesBySession } from '../api/apiService';
import '../assets/css/UploadedImage.css';

const UploadedImages = () => {
  const { session_id } = useParams(); // URL로부터 session_id 파라미터를 추출
  const [images, setImages] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchImagesBySession(session_id)
      .then(response => {
        if (!Array.isArray(response.uploaded_images_urls)) {
          throw new TypeError('Expected an array of images');
        }
        const imageList = response.uploaded_images_urls.map(url => ({ src: url, alt: 'Loaded Image' }));
        setImages(imageList);
      })
      .catch(error => console.error('Failed to fetch images', error));
  }, [session_id]);

  const redirectToCategories = () => {
    navigate(`/categories/${session_id}`);
  };

  return (
    <div>
      <button onClick={redirectToCategories}>분류하기</button>
      <ImageGrid images={images} />
    </div>
  );
};

export default UploadedImages;