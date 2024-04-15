import React from 'react';
import '../assets/css/ImageGrid.css';

const ImageGrid = ({ images }) => {
  return (
    <div className="image-grid">
      {images.map((image, index) => (
        <img key={index} src={image.src} alt={image.alt || `Content ${index + 1}`} />
      ))}
    </div>
  );
};

export default ImageGrid;