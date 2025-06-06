import React, { useState, useRef } from 'react';

export default function OCRPage() {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [ocrResults, setOcrResults] = useState(null);
  const [customerName, setCustomerName] = useState('');
  const [balance, setBalance] = useState('');
  const fileInputRef = useRef();

  const handleFileChange = (e) => setFiles([...e.target.files]);

  const handleUpload = async () => {
    if (!files.length || !customerName || !balance) return;

    setLoading(true);
    setOcrResults(null);
    const form = new FormData();
    form.append('customer_name', customerName);
    form.append('balance', balance);

    files.forEach((file) => {
      form.append('cheques', file);
    });

    try {
      const res = await fetch('http://127.0.0.1:9001/api/cheques/', {
        method: 'POST',
        body: form,
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || `Server error: ${res.status}`);
      }

      const result = await res.json();
      setOcrResults(result);
    } catch (err) {
      alert(`Error: ${err.message || 'Cheque processing failed'}`);
    } finally {
      setLoading(false);
    }
  };

  const downloadPdfReport = async () => {
    if (!ocrResults) return;

    setPdfLoading(true);
    try {
      const response = await fetch(
        `http://127.0.0.1:9001/api/sessions/${ocrResults.session_id}/pdf/`
      );

      if (!response.ok) {
        throw new Error(`Failed to generate PDF: ${response.status}`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `cheque_report_${ocrResults.session_id}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch (err) {
      alert(`PDF Error: ${err.message}`);
    } finally {
      setPdfLoading(false);
    }
  };

  // Compute a client‐side "Remaining Balance":
  // initial_balance minus every cheque marked 'flagged' (positive amount).


  return (
    <div className="flex justify-center px-4 py-8">
      <div className="w-full max-w-4xl bg-white bg-opacity-90 backdrop-blur-md p-6 rounded-xl shadow-lg">
        <h2 className="text-2xl font-semibold mb-6 text-center text-gray-800">
          Cheque Processing System
        </h2>

        {/* Customer Details */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Customer Name
              </label>
              <input
                type="text"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="Enter customer name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Initial Balance (₹)
              </label>
              <input
                type="number"
                value={balance}
                onChange={(e) => setBalance(e.target.value)}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="Enter initial balance"
                step="0.01"
                min="0"
              />
            </div>
          </div>
        </div>

        {/* File Upload */}
        <div className="mb-6 flex flex-col items-center p-6 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
          <input
            type="file"
            accept="image/*"
            multiple
            ref={fileInputRef}
            onChange={handleFileChange}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current.click()}
            className="flex items-center gap-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold text-lg py-3 px-6 rounded-lg transition shadow-md"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
            Select Cheque Images
          </button>

          <div className="mt-4 text-center">
            {files.length > 0 ? (
              <div className="space-y-2">
                <p className="text-gray-700 font-medium">
                  {files.length} cheque(s) selected
                </p>
                <ul className="max-h-32 overflow-y-auto text-sm text-gray-600">
                  {files.map((file, index) => (
                    <li key={index} className="truncate">
                      {file.name}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-gray-500 mt-2">
                No files chosen. Supported formats: JPG, PNG
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={() => {
              setFiles([]);
              setCustomerName('');
              setBalance('');
              setOcrResults(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
            className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold py-3 rounded-lg transition"
          >
            Clear All
          </button>

          <button
            onClick={handleUpload}
            disabled={loading || !files.length || !customerName || !balance}
            className={`flex-1 text-center font-semibold py-3 rounded-lg transition shadow-md
              ${
                loading || !files.length || !customerName || !balance
                  ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg
                  className="animate-spin h-5 w-5 text-white"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Processing Cheques...
              </span>
            ) : (
              'Process Cheques'
            )}
          </button>
        </div>

        {/* OCR Results Display */}
        {ocrResults && (
          <div className="mt-8 animate-fadeIn">
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100">
              {/* Top‐row cards for Customer, InitialBalance, SessionID, RemainingBalance */}
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-500">Customer</p>
                  <p className="mt-1 text-lg font-semibold text-gray-800">
                    {ocrResults.customer_name}
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-500">Initial Balance</p>
                  <p className="mt-1 text-lg font-semibold text-gray-800">
                    ₹{ocrResults.initial_balance.toFixed(2)}
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-500">Session ID</p>
                  <p className="mt-1 text-lg font-semibold text-gray-800">
                    {ocrResults.session_id}
                  </p>
                </div>
                <div className="bg-white p-4 rounded-lg shadow">
                  <p className="text-sm text-gray-500">Remaining Balance</p>
                  <p className="mt-1 text-lg font-semibold text-gray-800">
                    ₹{ocrResults.remaining_balance.toFixed(2)}
                  </p>
                </div>
              </div>

              <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
                Cheque Processing Details
              </h3>

              <div className="overflow-x-auto rounded-lg border border-gray-200">
                <table className="min-w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-700">
                        Image
                      </th>
                      <th className="py-3 px-4 text-right text-sm font-medium text-gray-700">
                        Amount
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-700">
                        Status
                      </th>
                      <th className="py-3 px-4 text-left text-sm font-medium text-gray-700">
                        Reason
                      </th>
                    </tr>
                  </thead>

                  <tbody className="divide-y divide-gray-200">
                    {ocrResults.cheques &&
                    Array.isArray(ocrResults.cheques) ? (
                      ocrResults.cheques.map((cheque, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          {/* Image Name */}
                          <td className="py-3 px-4 text-sm text-gray-900 font-medium">
                            <div className="flex items-center">
                              <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-5 w-5 text-gray-400 mr-2"
                                viewBox="0 0 20 20"
                                fill="currentColor"
                              >
                                <path
                                  fillRule="evenodd"
                                  d="M4 5a2 2 0 00-2 2v8a2 2 0 002 2h12a2 2 0 002-2V7a2 2 0 00-2-2h-1.586a1 1 0 01-.707-.293l-1.121-1.121A2 2 0 0011.172 3H8.828a2 2 0 00-1.414.586L6.293 4.707A1 1 0 015.586 5H4zm6 9a3 3 0 100-6 3 3 0 000 6z"
                                  clipRule="evenodd"
                                />
                              </svg>
                              <span className="truncate max-w-[120px]">
                                {cheque.image_name}
                              </span>
                            </div>
                          </td>

                          {/* Amount */}
                          <td className="py-3 px-4 text-right text-sm font-medium text-gray-900">
                            {cheque.amount !== null &&
                            cheque.amount !== undefined
                              ? `₹${cheque.amount.toFixed(2)}`
                              : 'N/A'}
                          </td>

                          {/* Status */}
                          <td className="py-3 px-4">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                cheque.status === 'flagged'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : cheque.status === 'discarded'
                                  ? 'bg-red-100 text-red-800'
                                  : cheque.status === 'error'
                                  ? 'bg-purple-100 text-purple-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {cheque.status}
                            </span>
                          </td>

                          {/* Reason */}
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {cheque.reason || '-'}
                          </td>
                        </tr>
                      ))
                    ) : null}
                  </tbody>
                </table>

                {/* Accepted Cheques */}
                <h4 className="text-lg font-semibold mt-8">Accepted Cheques</h4>
                <ul className="list-disc list-inside">
                  {ocrResults.history &&
                  Array.isArray(ocrResults.history.accepted) ? (
                    ocrResults.history.accepted.map((c, i) => (
                      <li key={i}>
                        {typeof c.amount === 'number'
                          ? `₹${c.amount.toFixed(2)}`
                          : '– Invalid amount'}
                      </li>
                    ))
                  ) : null}
                </ul>

                {/* Rejected Cheques */}
                <h4 className="text-lg font-semibold mt-4">Rejected Cheques</h4>
                <ul className="list-disc list-inside">
                  {ocrResults.history &&
                  Array.isArray(ocrResults.history.rejected) ? (
                    ocrResults.history.rejected.map((c, i) => (
                      <li key={i}>
                        {c.name}: {c.reason}
                      </li>
                    ))
                  ) : null}
                </ul>
              </div>

              {/* Download PDF Button */}
              <div className="mt-8 text-center">
                <button
                  onClick={downloadPdfReport}
                  disabled={pdfLoading}
                  className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 px-6 rounded-lg transition shadow-md disabled:opacity-75"
                >
                  {pdfLoading ? (
                    <>
                      <svg
                        className="animate-spin h-5 w-5 text-white"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        ></circle>
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                      Generating Report...
                    </>
                  ) : (
                    <>
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        className="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fillRule="evenodd"
                          d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                      Download PDF Report
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
