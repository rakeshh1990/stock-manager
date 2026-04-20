import { useState } from "react";
import axios from "axios";
import { Card, CardContent } from "@/components/ui/card";

function App() {
  const [symbol, setSymbol] = useState("");
  const [data, setData] = useState(null);

  const handleAnalyse = async () => {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_BASE_URL}/analyse`, {
        params: { symbol }
      });
      setData(res.data);
    } catch (e) {
      alert("Failed to fetch data");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center p-10 bg-gray-50">
      <h1 className="text-3xl font-bold mb-5">📈 Stock Analyzer</h1>

      <div className="flex gap-2">
        <input
          className="border p-2 rounded w-64"
          placeholder="Enter symbol (e.g. INFY.NS)"
          value={symbol}
          onChange={e => setSymbol(e.target.value)}
        />
        <button
          onClick={handleAnalyse}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Analyze
        </button>
      </div>

      {data && (
        <Card className="mt-10 w-full max-w-lg">
          <CardContent>
            <h2 className="text-xl font-semibold mb-2">{data.symbol}</h2>
            <p><b>Latest Close:</b> ₹{data.latest_close}</p>
            <p><b>RSI:</b> {data.rsi}</p>
            <p><b>Recommendation:</b> {data.recommendation}</p>
            <p><b>Note:</b> {data.note}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default App;
