import { useState } from "react";
import axios from "axios";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function App() {
  const [history, setHistory] = useState([]);
  const [image, setImage] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [ocrText, setOcrText] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (file) {
      setSelectedFile(file);
      setImage(URL.createObjectURL(file));
      setOcrText("");
      setAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    try {
      setLoading(true);

      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await axios.post(
        "https://valo-ai-coach.onrender.com/analyze",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      setOcrText(res.data.ocr_text);
      setAnalysis(res.data.analysis);
    } catch (error) {
      console.error(error);
      setAnalysis({
        error: "Analysis failed",
      });
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const res = await axios.get(
        "https://valo-ai-coach.onrender.com/history"
      );

      setHistory(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const downloadReport = () => {
    window.open(
      "https://valo-ai-coach.onrender.com/download-report",
      "_blank"
    );
  };

  const chartData = history
    .filter(
      (item) =>
        item.analysis &&
        typeof item.analysis === "object" &&
        item.analysis.score
    )
    .map((item, index) => ({
      match: index + 1,
      score: item.analysis.score,
    }));

  return (
    <div className="min-h-screen bg-zinc-950 text-white">

      <nav className="border-b border-zinc-800 px-8 py-5 flex justify-between items-center">
        <h1 className="text-3xl font-bold text-red-500">
          ValorAI Coach
        </h1>

        <span className="text-zinc-400 text-sm">
          AI Powered Match Analysis
        </span>
      </nav>

      <div className="max-w-6xl mx-auto px-6 py-14">

        <h2 className="text-5xl font-bold text-center mb-4">
          Analyze Your Valorant Performance
        </h2>

        <p className="text-zinc-400 text-center max-w-2xl mx-auto mb-12">
          Upload a screenshot and get AI-powered insights.
        </p>

        <div className="border-2 border-dashed border-zinc-700 rounded-3xl p-10 text-center">

          <input
            type="file"
            accept="image/*"
            id="upload"
            className="hidden"
            onChange={handleImageChange}
          />

          <label
            htmlFor="upload"
            className="cursor-pointer inline-block bg-red-500 hover:bg-red-600 px-8 py-4 rounded-2xl font-semibold"
          >
            Upload Screenshot
          </label>

          {image && (
            <>
              <div className="mt-10">
                <img
                  src={image}
                  alt="preview"
                  className="mx-auto rounded-2xl border border-zinc-700 max-h-[500px]"
                />
              </div>

              <div className="flex justify-center gap-4 mt-8 flex-wrap">

                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="bg-green-600 hover:bg-green-700 px-8 py-4 rounded-2xl font-semibold"
                >
                  {loading
                    ? "Analyzing..."
                    : "Analyze Match"}
                </button>

                <button
                  onClick={loadHistory}
                  className="bg-blue-600 hover:bg-blue-700 px-8 py-4 rounded-2xl font-semibold"
                >
                  View History
                </button>

                {analysis && (
                  <button
                    onClick={downloadReport}
                    className="bg-purple-600 hover:bg-purple-700 px-8 py-4 rounded-2xl font-semibold"
                  >
                    Download PDF
                  </button>
                )}

              </div>
            </>
          )}
        </div>

        {(analysis || ocrText) && (
          <div className="grid md:grid-cols-2 gap-6 mt-10">

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
              <h3 className="text-xl font-bold text-blue-400 mb-4">
                📄 OCR Results
              </h3>

              <div className="text-zinc-300 whitespace-pre-wrap">
                {ocrText}
              </div>
            </div>

            <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">

              <h3 className="text-xl font-bold text-green-400 mb-6">
                🎯 AI Analysis
              </h3>

              {analysis &&
              typeof analysis === "object" ? (

                <div className="space-y-5">

                  <div className="bg-zinc-800 rounded-2xl p-6 text-center">
                    <p className="text-zinc-400 mb-2">
                      Performance Score
                    </p>

                    <h1 className="text-6xl font-bold text-green-400">
                      {analysis.score}/10
                    </h1>
                  </div>

                  <div className="grid md:grid-cols-3 gap-4">

                    <div className="bg-zinc-800 p-4 rounded-xl">
                      <p className="text-zinc-400 text-sm">
                        Match Type
                      </p>
                      <p className="font-bold">
                        {analysis.match_type}
                      </p>
                    </div>

                    <div className="bg-zinc-800 p-4 rounded-xl">
                      <p className="text-zinc-400 text-sm">
                        Focus Area
                      </p>
                      <p className="font-bold">
                        {analysis.focus_area}
                      </p>
                    </div>

                    <div className="bg-zinc-800 p-4 rounded-xl">
                      <p className="text-zinc-400 text-sm">
                        Confidence
                      </p>
                      <p className="font-bold">
                        {analysis.confidence}
                      </p>
                    </div>

                  </div>

                  <div className="bg-zinc-800 p-4 rounded-xl">
                    <h4 className="font-bold text-cyan-400 mb-2">
                      📋 Summary
                    </h4>
                    <p>{analysis.summary}</p>
                  </div>

                  <div className="bg-zinc-800 p-4 rounded-xl">
                    <h4 className="font-bold text-green-400 mb-2">
                      💪 Strengths
                    </h4>

                    <ul className="list-disc pl-5">
                      {analysis.strengths?.map(
                        (item, index) => (
                          <li key={index}>
                            {item}
                          </li>
                        )
                      )}
                    </ul>
                  </div>

                  <div className="bg-zinc-800 p-4 rounded-xl">
                    <h4 className="font-bold text-red-400 mb-2">
                      ⚠ Weaknesses
                    </h4>

                    <ul className="list-disc pl-5">
                      {analysis.weaknesses?.map(
                        (item, index) => (
                          <li key={index}>
                            {item}
                          </li>
                        )
                      )}
                    </ul>
                  </div>

                  <div className="bg-zinc-800 p-4 rounded-xl">
                    <h4 className="font-bold text-orange-400 mb-2">
                      🚀 Improvement Plan
                    </h4>

                    <ol className="list-decimal pl-5">
                      {analysis.improvement_plan?.map(
                        (item, index) => (
                          <li key={index}>
                            {item}
                          </li>
                        )
                      )}
                    </ol>
                  </div>

                  <div className="bg-zinc-800 p-4 rounded-xl">
                    <h4 className="font-bold text-pink-400 mb-2">
                      🎮 Agent Advice
                    </h4>

                    <p>
                      {analysis.agent_advice}
                    </p>
                  </div>

                </div>

              ) : (
                <pre>
                  {JSON.stringify(
                    analysis,
                    null,
                    2
                  )}
                </pre>
              )}
            </div>

          </div>
        )}

        {history.length > 0 && (
          <div className="mt-16">

            <h2 className="text-3xl font-bold mb-6">
              📚 Analysis History
            </h2>

            <div className="space-y-4">

              {history.map((item, index) => (
                <div
                  key={index}
                  className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6"
                >
                  <p className="text-zinc-400 text-sm mb-2">
                    {new Date(
                      item.date
                    ).toLocaleString()}
                  </p>

                  <p className="text-blue-400 font-semibold mb-3">
                    {item.filename}
                  </p>

                  <pre className="text-zinc-300 overflow-auto">
                    {JSON.stringify(
                      item.analysis,
                      null,
                      2
                    )}
                  </pre>
                </div>
              ))}

            </div>

            {chartData.length > 0 && (
              <div className="mt-10 bg-zinc-900 border border-zinc-800 rounded-2xl p-6">

                <h2 className="text-3xl font-bold mb-6 text-cyan-400">
                  📈 Performance Trend
                </h2>

                <ResponsiveContainer
                  width="100%"
                  height={300}
                >
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="match" />
                    <YAxis domain={[0, 10]} />
                    <Tooltip />

                    <Line
                      type="monotone"
                      dataKey="score"
                      stroke="#22c55e"
                      strokeWidth={3}
                    />
                  </LineChart>
                </ResponsiveContainer>

              </div>
            )}

          </div>
        )}

      </div>
    </div>
  );
}

export default App;