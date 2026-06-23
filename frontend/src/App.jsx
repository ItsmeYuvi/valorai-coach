import { useState } from "react";
import axios from "axios";

function App() {
  const [image, setImage] = useState(null);
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleImageChange = (e) => {
    const file = e.target.files[0];

    if (file) {
      setImage(URL.createObjectURL(file));
    }
  };

  const handleAnalyze = async () => {
  try {
    setLoading(true);

    const res = await axios.get(
      "http://127.0.0.1:8000/analyze"
    );

    console.log("API Response:", res);
    console.log("Data:", res.data);

    setResponse(res.data.message);
  } catch (error) {
    console.error("ERROR:", error);

    if (error.response) {
      console.log(error.response);
    }

    setResponse("Failed to connect to backend");
  } finally {
    setLoading(false);
  }
};

  return (
    <div className="min-h-screen bg-zinc-950 text-white">

      {/* Navbar */}
      <nav className="border-b border-zinc-800 px-8 py-5 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-red-500">
          ValorAI Coach
        </h1>

        <span className="text-zinc-400 text-sm">
          AI-Powered Valorant Performance Analysis
        </span>
      </nav>

      {/* Hero */}
      <div className="flex flex-col items-center justify-center px-6 py-16">

        <h2 className="text-5xl font-bold text-center mb-4">
          Analyze Your Valorant Performance
        </h2>

        <p className="text-zinc-400 text-center max-w-xl mb-10">
          Upload a match screenshot and receive AI-powered coaching,
          performance insights, and personalized improvement plans.
        </p>

        {/* Upload Box */}
        <div className="w-full max-w-3xl border-2 border-dashed border-zinc-700 rounded-2xl p-8 text-center">

          <input
            type="file"
            accept="image/*"
            id="upload"
            className="hidden"
            onChange={handleImageChange}
          />

          <label
            htmlFor="upload"
            className="cursor-pointer inline-block bg-red-500 hover:bg-red-600 px-6 py-3 rounded-xl font-semibold transition"
          >
            Choose Image
          </label>

          {image && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold mb-4">
                Screenshot Preview
              </h3>

              <img
                src={image}
                alt="preview"
                className="rounded-xl mx-auto max-h-[400px] w-auto object-contain"
              />

              <button
                onClick={handleAnalyze}
                className="mt-6 bg-green-600 hover:bg-green-700 px-6 py-3 rounded-xl font-semibold transition"
              >
                {loading ? "Analyzing..." : "Analyze Match"}
              </button>

              {response && (
                <div className="mt-6 bg-zinc-900 border border-zinc-700 rounded-xl p-4">
                  <p>{response}</p>
                </div>
              )}
            </div>
          )}

        </div>

      </div>
    </div>
  );
}

export default App;