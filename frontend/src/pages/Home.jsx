import { Link } from 'react-router-dom';

/**
 * Home Page Component
 * Landing page for the Fluence disease surveillance application
 */
function Home() {
  return (
    <div className="home-page">
      <section className="hero">
        <h1>Welcome to Fluence</h1>
        <p className="subtitle">
          Public Health Disease Surveillance Platform
        </p>
        <p className="description">
          Monitor disease outbreaks, view real-time data, and access analytics 
          to support public health decisions.
        </p>
        <Link to="/data" className="cta-button">
          View Disease Data
        </Link>
      </section>

      <section className="features">
        <h2>Key Features</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <h3>Interactive Heat Maps</h3>
            <p>Visualize disease spread across regions with dynamic heat maps.</p>
          </div>
          <div className="feature-card">
            <h3>Real-Time Data</h3>
            <p>Access up-to-date disease case information from verified sources.</p>
          </div>
          <div className="feature-card">
            <h3>Analytics & Forecasting</h3>
            <p>Generate reports and view predictive models for outbreak trends.</p>
          </div>
          <div className="feature-card">
            <h3>Alert Subscriptions</h3>
            <p>Subscribe to alerts for specific diseases and regions.</p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Home;
