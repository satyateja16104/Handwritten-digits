import React, { useEffect, useState } from 'react';

export default function HistoryPage() {
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:9001/api/sessions/')
      .then(res => res.json())
      .then(setSessions)
      .catch(console.error);
  }, []);

  return (
    <div className="px-4">
      <h2 className="text-2xl font-semibold text-gray-800 mb-6 text-center">
        Processing History
      </h2>

      {sessions.length === 0 ? (
        <p className="text-center text-gray-700">No processing history found</p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {sessions.map(session => (
            <div
              key={session.id}
              className="bg-white bg-opacity-90 backdrop-blur-md p-4 rounded-xl shadow-md"
            >
              <h3 className="font-semibold text-gray-800 mb-2">
                {session.customer_name}
              </h3>
              <p className="text-sm text-gray-600">
                Initial: ₹{parseFloat(session.balance).toFixed(2)}
              </p>
             <p className="text-sm text-gray-500 mb-4">
                {session.created_at ? new Date(session.created_at).toLocaleDateString() : 'No date'}
              </p>
              <a
                href={`http://127.0.0.1:9001/api/sessions/${session.id}/pdf/`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded transition"
              >
                Download Report
              </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}