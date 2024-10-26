import React, { useState } from "react";
import { Upload, RefreshCw, Image as ImageIcon, Type } from "lucide-react";

const Input = () => {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [caption, setCaption] = useState("");
  const [story, setStory] = useState("");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const uploadedFile = event.target.files[0];
    setFile(uploadedFile);
    setCaption("");
    setStory("");
    setError("");

    if (uploadedFile) {
      if (uploadedFile.size > 5 * 1024 * 1024) {
        setError("File size should be less than 5MB");
        setFile(null);
        setPreviewUrl(null);
        return;
      }
      const url = URL.createObjectURL(uploadedFile);
      setPreviewUrl(url);
    } else {
      setPreviewUrl(null);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file) return;

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`https://phord.onrender.com/caption-image?prompt=${encodeURIComponent(prompt)}`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setCaption(result.caption);
        setStory(result.story);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || "Error generating caption. Try again.");
        setCaption("");
        setStory("");
      }
    } catch (error) {
      setError("Error connecting to the server. Please try again later.");
      setCaption("");
      setStory("");
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFile(null);
    setPreviewUrl(null);
    setCaption("");
    setStory("");
    setPrompt("");
    setError("");
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-teal-50 to-emerald-100 p-4 flex items-center justify-center">
      <div className="w-full max-w-2xl lg:max-w-4xl mx-auto p-4">
        <div className="bg-white rounded-xl shadow-xl p-6 md:p-8 lg:p-12">
          <div className="flex flex-col md:flex-row items-center justify-between mb-6 md:mb-8">
            <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-teal-800 text-center md:text-left">
              Phord.Ai
            </h2>
            {(file || caption || story) && (
              <button
                onClick={resetForm}
                className="mt-4 md:mt-0 flex items-center gap-2 px-4 py-2 text-teal-600 hover:text-teal-800 
                         transition-colors duration-200"
              >
                <RefreshCw className="w-4 h-4" />
                Reset
              </button>
            )}
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
            <div className={`relative  bg-teal-50 p-6 md:p-8 rounded-lg border-2 border-dashed 
                          ${error ? 'border-red-400' : 'border-teal-200'} 
                          hover:border-teal-400 transition-colors duration-200`}>
              {!previewUrl && (
                <div className="absolute inset-0 m-2 flex flex-col items-center justify-center">
                  <ImageIcon className="w-10 md:w-12 h-10 md:h-12 text-teal-400 mb-2" />
                  <p className="text-teal-600">Click to upload or drag and drop</p>
                  <p className="text-teal-400 text-sm">PNG, JPG, JPEG (max 5MB)</p>
                </div>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className={`w-full h-full ${!previewUrl ? 'opacity-0' : ''} cursor-pointer`}
              />
              {previewUrl && (
                <div className="mt-4 flex justify-center">
                  <img
                    src={previewUrl}
                    alt="Selected preview"
                    className="w-full md:w-96 max-h-64 md:max-h-72 lg:max-h-80 object-cover rounded-lg shadow-lg 
                             transition-transform duration-200 hover:scale-105"
                  />
                </div>
              )}
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-4 rounded-lg text-center">
                {error}
              </div>
            )}

            <div className="relative">
              <Type className="absolute left-3 top-3.5 w-5 h-5 text-teal-400" />
              <input
                type="text"
                placeholder="Enter a prompt to guide the story (optional)"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-lg border border-teal-200 
                         text-teal-800 placeholder-teal-400 focus:outline-none 
                         focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>

            <div className="flex justify-center">
              <button
                type="submit"
                disabled={!file || loading}
                className={`flex items-center gap-2 px-8 py-3 rounded-full text-lg font-semibold 
                         ${loading 
                           ? "bg-gray-400 cursor-not-allowed" 
                           : "bg-teal-600 hover:bg-teal-700 active:bg-teal-800"} 
                         text-white transition duration-200 shadow-lg 
                         hover:shadow-xl`}
              >
                {loading ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <Upload className="w-5 h-5" />
                )}
                {loading ? "Generating..." : "Get Caption and Story"}
              </button>
            </div>
          </form>

          {(caption || story) && (
            <div className="mt-8 md:mt-10 lg:mt-12 space-y-6 md:space-y-8">
              {caption && (
                <div className="bg-teal-50 p-4 md:p-6 rounded-lg">
                  <h3 className="text-xl md:text-2xl font-semibold text-teal-800 mb-2 md:mb-4">Caption</h3>
                  <p className="text-teal-700 text-base md:text-lg">{caption}</p>
                </div>
              )}
              
              {story && (
                <div className="bg-emerald-50 p-4 md:p-6 rounded-lg">
                  <h3 className="text-xl md:text-2xl font-semibold text-emerald-800 mb-2 md:mb-4">Story</h3>
                  <p className="text-emerald-700 text-base md:text-lg leading-relaxed">{story}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Input;
