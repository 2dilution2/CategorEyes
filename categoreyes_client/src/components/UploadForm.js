import React, { useCallback, useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import '../assets/css/UploadForm.css';
import { uploadImage } from '../api/apiService';
import { useNavigate } from 'react-router-dom';

const UploadForm = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate(); 
  
  const onDrop = useCallback(acceptedFiles => {
    const mappedFiles = acceptedFiles.map(file => Object.assign(file, {
      preview: URL.createObjectURL(file)
    }));

    setFiles(prevFiles => [...prevFiles, ...mappedFiles]);
  }, []);

  const onSubmit = async () => {
    setLoading(true);
    try {
      const formData = new FormData();
      files.forEach((file) => formData.append('files', file)); // 'files' 필드로 파일을 추가합니다.
      const session_id = await uploadImage(formData); // uploadImage 함수가 formData 객체를 받아 사용합니다.
      if (session_id) {
        console.log('Files uploaded successfully', session_id);
        navigate(`/uploaded_images/${session_id}`);
      } else {
        console.error('No session ID received');
      }
    } catch (error) {
      console.error('Error uploading files:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const removeFile = (file) => (event) => {
    event.stopPropagation();
    const newFiles = files.filter(f => f !== file);
    setFiles(newFiles);
    URL.revokeObjectURL(file.preview);
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  const thumbs = files.map(file => (
    <div className="thumb" key={file.name}>
      <div className="thumbInner">
        <img src={file.preview} className="img" alt="Preview" />
      </div>
      <button onClick={(event) => removeFile(file)(event)} className="dz-remove">삭제</button>
    </div>
  ));

  useEffect(() => () => files.forEach(file => URL.revokeObjectURL(file.preview)), [files]);

  return (
    <section className="container">
      <div {...getRootProps({ className: 'dropzone' })}>
        <input {...getInputProps()} />
        {files.length === 0 && (
          <p>Drop files here or click to upload.</p>
        )}  
        <aside className="thumbsContainer">
          {thumbs}
        </aside>
      </div>
      <button onClick={onSubmit} className="submit-button" disabled={loading}>
        {loading ? 'Uploading...' : 'Upload'}
      </button>
      {loading && <div className="loading-spinner"></div>}
    </section>
  );
};

export default UploadForm;
