import { Header } from '../components/layout/Header';
import { FileUpload } from '../components/common/FileUpload';

export default function Upload() {
  return (
    <div>
      <Header title="Data Ingestion" />
      <div className="glass-panel p-12 rounded-2xl min-h-[500px] flex flex-col items-center justify-center">
        <div className="text-center mb-8 max-w-md">
          <h3 className="text-xl font-bold text-white mb-2">Batch Transaction Upload</h3>
          <p className="text-gray-400">Upload your transaction CSV files for batch processing and anomaly detection. Large files will be processed in the background.</p>
        </div>
        <FileUpload />
      </div>
    </div>
  );
}
