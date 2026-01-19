/**
 * FileUpload component - Handles file selection and preview
 */

import React, { useRef, useState } from 'react';
import './FileUpload.css';

interface FileUploadProps {
  onFileSelect: (file: File | null) => void;
  selectedFile: File | null;
}

export const FileUpload: React.FC<FileUploadProps> = ({ onFileSelect, selectedFile }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    onFileSelect(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files?.[0];
    if (file) {
      onFileSelect(file);
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    const items = e.clipboardData?.items;
    if (!items) return;

    for (let i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        const file = items[i].getAsFile();
        if (file) {
          onFileSelect(file);
          break;
        }
      }
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = () => {
    onFileSelect(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return '🖼️';
    if (type === 'application/pdf') return '📄';
    return '📎';
  };

  return (
    <div className="file-upload">
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*,.pdf"
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />

      {selectedFile ? (
        <div className="file-preview">
          <div className="file-info">
            <span className="file-icon-large">{getFileIcon(selectedFile.type)}</span>
            <div className="file-details">
              <span className="file-name">{selectedFile.name}</span>
              <span className="file-size">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </span>
            </div>
          </div>
          <button 
            onClick={handleRemoveFile} 
            className="remove-file-btn"
            aria-label="Remove file"
          >
            ✕
          </button>
        </div>
      ) : (
        <div
          className={`file-drop-zone ${dragActive ? 'drag-active' : ''}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onPaste={handlePaste}
        >
          <button onClick={handleButtonClick} className="upload-btn">
            📎 Attach File
          </button>
          <span className="upload-hint">
            or paste/drag image or PDF
          </span>
        </div>
      )}
    </div>
  );
};
