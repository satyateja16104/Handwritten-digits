import React, { forwardRef, useImperativeHandle, useRef, useEffect, useState } from 'react';

const DrawingPad = forwardRef((props, ref) => {
  const canvasRef = useRef();
  const [drawing, setDrawing] = useState(false);

  useImperativeHandle(ref, () => ({
    clear: () => {
      const ctx = canvasRef.current.getContext('2d');
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    },
    get canvas() {
      return canvasRef.current;
    }
  }));

  useEffect(() => {
    const ctx = canvasRef.current.getContext('2d');
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvasRef.current.width, canvasRef.current.height);
  }, []);

  const start = e => {
    setDrawing(true);
    draw(e);
  };
  const end = () => {
    setDrawing(false);
    canvasRef.current.getContext('2d').beginPath();
  };
  const draw = e => {
    if (!drawing) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const ctx = canvasRef.current.getContext('2d');
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    ctx.lineWidth = 14;
    ctx.lineCap = 'round';
    ctx.strokeStyle = 'black';
    ctx.lineTo(x * (canvasRef.current.width / rect.width),
               y * (canvasRef.current.height / rect.height));
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x * (canvasRef.current.width / rect.width),
               y * (canvasRef.current.height / rect.height));
  };

  return (
    <div className="w-full max-w-9xl h-100 bg-white rounded-xl shadow-md overflow-hidden">
      <canvas
        ref={canvasRef}
        width={800}
        height={400}
        className="w-full h-full cursor-crosshair touch-none"
        onMouseDown={start}
        onMouseUp={end}
        onMouseMove={draw}
        onMouseLeave={end}
      />
    </div>
  );
});

export default DrawingPad;
