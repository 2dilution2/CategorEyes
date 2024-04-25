import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import ImageGrid from '../components/ImageGrid';
import { fetchImagesByCategory } from '../api/apiService';

const ImagesPage = () => {
  const { category, session_id } = useParams();
  const [images, setImages] = useState([]);

  useEffect(() => {
    fetchImagesByCategory(category, session_id)
      .then(response => {
        const imageList = response.images.map(url => ({ src: url, alt: 'Loaded Image' }));
        setImages(imageList);
      })
      .catch(error => console.error('Failed to fetch images', error));
  }, [category, session_id]);

  return (
    <div>
      <h1>{category} Images</h1>
      <ImageGrid images={images} />
    </div>
  );
};

export default ImagesPage;