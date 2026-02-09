import { FileUpload } from "../components/FileUpload";

export function DataUpload() {
  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-[#2C2C2A]">Data Upload</h1>
        <p className="text-sm text-[#6C6C6A] mt-1">
          Upload your sales data files (CSV, Excel) for analysis and forecasting
        </p>
      </div>
      <FileUpload />
    </div>
  );
}
