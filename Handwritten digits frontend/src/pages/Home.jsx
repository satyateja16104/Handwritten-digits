// src/pages/Home.jsx
import React, { useRef, useState } from 'react';
import DrawingPad from '../DrawingPad';

const Home = () => {
  const [prediction, setPrediction] = useState('');
  const [loading, setLoading] = useState(false);
  const drawingRef = useRef();

  const handleSubmit = async () => {
    setLoading(true);
    const blob = await new Promise(resolve =>
      drawingRef.current.canvas.toBlob(resolve, 'image/png')
    );
    const form = new FormData();
    form.append('image', blob, 'drawing.png');

    try {
      const res = await fetch('http://127.0.0.1:9000/api/predict/', {
        method: 'POST',
        body: form
      });
      const data = await res.json();
      setPrediction(data.prediction || '');
    } catch {
      setPrediction('Error');
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    drawingRef.current.clear();
    setPrediction('');
  };

  return (
    // Only a content wrapper—no bg/animated blobs here.
    <div className="relative z-10 flex flex-col items-center px-4 py-12">
      <h1 className="text-5xl font-extrabold text-white mb-8 drop-shadow-lg">
        Handwritten Digits Classification
      </h1>

      <div className="w-full max-w-4xl space-y-6">
        <DrawingPad ref={drawingRef} />

        <p className="text-center text-white italic opacity-90">
          ✍️ Hint: Leave a bit of space between digits for best results.
        </p>

        <div className="flex justify-center gap-6">
          <button
            onClick={handleClear}
            className="px-6 py-3 bg-white/80 hover:bg-white text-gray-800 rounded-lg shadow-md transform hover:-translate-y-1 transition-all duration-200"
          >
            Clear
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className={`px-6 py-3 rounded-lg shadow-md text-white transition-all duration-200
              ${loading
                ? 'bg-blue-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 hover:-translate-y-1 hover:shadow-lg'}`}
          >
            {loading ? 'Predicting…' : 'Predict'}
          </button>
        </div>

        {prediction && (
          <div className="mx-auto p-6 bg-white rounded-2xl shadow-lg transform transition-transform duration-500 hover:scale-105">
            <p className="text-center text-2xl font-semibold text-gray-800">
              Prediction: <span className="text-blue-600">{prediction}</span>
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
