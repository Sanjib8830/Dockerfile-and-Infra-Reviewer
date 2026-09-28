import ReviewPage from "./pages/ReviewPage";

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <h1>Dockerfile &amp; Infra Reviewer</h1>
        <p className="app-tagline">AI-assisted DevSecOps review</p>
      </header>
      <main>
        <ReviewPage />
      </main>
    </div>
  );
}

export default App;
