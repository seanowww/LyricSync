import { BrowserRouter, Routes, Route } from "react-router-dom";
import { UploadScreen } from "./components/UploadScreen";
import { PreviewScreen } from "./components/PreviewScreen";

export default function App() {
  return (
    <BrowserRouter>
      <div className="size-full">
        <Routes>
          <Route path="/" element={<UploadScreen />} />
          <Route path="/preview" element={<PreviewScreen />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
