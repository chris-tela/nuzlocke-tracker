import { useRef, useState } from 'react';

interface SaveFileUploadProps {
  onFileSelected: (file: File) => void;
  isLoading?: boolean;
  error?: string | null;
}

export const SaveFileUpload = ({ onFileSelected, isLoading, error }: SaveFileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [sizeError, setSizeError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setSizeError(null);
    if (file.size > 1024 * 1024) {
      setSizeError('File is too large. Maximum size is 1 MB.');
      return;
    }
    onFileSelected(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  return (
    <div>
      <div
        onClick={() => fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        style={{
          border: `2px dashed ${isDragging ? 'var(--color-pokemon-yellow)' : 'var(--color-border)'}`,
          borderRadius: '8px',
          padding: '40px 20px',
          textAlign: 'center',
          cursor: isLoading ? 'wait' : 'pointer',
          backgroundColor: isDragging ? 'rgba(255, 215, 0, 0.05)' : 'var(--color-bg-light)',
          transition: 'all 150ms ease',
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".sav"
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />
        {isLoading ? (
          <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
            Parsing save file...
          </p>
        ) : (
          <>
            <p style={{ color: 'var(--color-text-primary)', margin: '0 0 8px 0', fontSize: '16px' }}>
              Drop a .sav file here or click to browse
            </p>
            <p style={{ color: 'var(--color-text-secondary)', margin: 0, fontSize: '12px' }}>
              Supports Pokemon Gen 1-5 save files (max 1 MB)
            </p>
          </>
        )}
      </div>
      {(error || sizeError) && (
        <div style={{
          marginTop: '12px',
          padding: '12px',
          backgroundColor: '#FEE2E2',
          border: '2px solid #F87171',
          borderRadius: '8px',
          color: '#991B1B',
          fontSize: '14px',
        }}>
          {sizeError || error}
        </div>
      )}
    </div>
  );
};
