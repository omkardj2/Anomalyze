import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, File, CheckCircle, X } from 'lucide-react';
import { useState, useRef } from 'react';
import { cn } from '../../lib/utils';
import { toast } from 'sonner';

export function FileUpload() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);

  const fileInputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragging(true);
    } else if (e.type === 'dragleave') {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFile = (file) => {
    // TODO: Validate file against backend rules (size, type)
    if (file.type !== 'text/csv') {
      toast.error('Invalid file type', { description: 'Please upload a CSV file.' });
      return;
    }
    setFile(file);
    simulateUpload();
  };

  const simulateUpload = () => {
    // TODO: Implement actual file upload to Cloudflare R2 / AWS S3 using presigned URLs
    // const formData = new FormData();
    // formData.append('file', file);
    // await api.post('/upload', formData);

    // await api.post('/upload', formData);

    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          clearInterval(interval);
          toast.success('File uploaded successfully', { description: 'Processing has started.' });
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const removeFile = () => {
    setFile(null);
    setProgress(0);
    setFile(null);
    setProgress(0);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <AnimatePresence mode="wait">
        {!file ? (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            key="dropzone"
          >
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={cn(
                "relative flex flex-col items-center justify-center w-full h-64 rounded-2xl border-2 border-dashed transition-all cursor-pointer",
                isDragging
                  ? "border-cyan-400 bg-cyan-400/5 scale-[1.02]"
                  : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
              )}
            >
              <div className="p-4 rounded-full bg-indigo-500/10 mb-4 text-indigo-400">
                <UploadCloud className="h-10 w-10" />
              </div>
              <p className="text-lg font-medium text-white mb-1">Click to upload or drag and drop</p>
              <p className="text-sm text-gray-400">CSV files only (max 10MB)</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
              />
            </div>
          </motion.div>
        ) : (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            key="uploading"
            className="bg-[#141522] border border-white/10 rounded-2xl p-6"
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-4">
                <div className="p-3 rounded-xl bg-indigo-500/20 text-indigo-400">
                  <File className="h-6 w-6" />
                </div>
                <div>
                  <h4 className="font-medium text-white">{file.name}</h4>
                  <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
              </div>
              {progress === 100 ? (
                <div className="text-green-400 flex items-center gap-2">
                  <CheckCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">Complete</span>
                </div>
              ) : (
                <button onClick={removeFile} className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors">
                  <X className="h-5 w-5" />
                </button>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs text-gray-400">
                <span>{progress === 100 ? 'Uploaded' : 'Uploading...'}</span>
                <span>{progress}%</span>
              </div>
              <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden">
                <motion.div
                  className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ ease: "linear" }}
                />
              </div>
            </div>

            {progress === 100 && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-6 flex justify-end gap-3"
              >
                <button onClick={removeFile} className="px-4 py-2 rounded-xl text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors">
                  Upload Another
                </button>
                <button className="px-4 py-2 rounded-xl bg-indigo-500 text-white text-sm font-medium hover:bg-indigo-600 transition-colors shadow-lg shadow-indigo-500/20">
                  View Analysis
                </button>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
