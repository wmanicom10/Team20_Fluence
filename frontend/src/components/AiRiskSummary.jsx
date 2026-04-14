import { useEffect, useState } from 'react';

const getErrorMessage = (payload, fallbackMessage) => {
  if (payload?.error?.message) {
    return payload.error.message;
  }

  if (payload?.message) {
    return payload.message;
  }

  return fallbackMessage;
};

function AiRiskSummary({ apiBaseUrl, disease }) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null });

  useEffect(() => {
    let isActive = true;

    const load = async () => {
      setState({ status: 'loading', data: null, error: null });

      try {
        const params = new URLSearchParams();
        if (disease && disease !== 'All Diseases') {
          params.set('disease', disease);
        }

        const url = `${apiBaseUrl}/api/ui/ai-risk${params.toString() ? `?${params.toString()}` : ''}`;
        const response = await fetch(url).catch(() => null);
        if (!response) {
          throw new Error('Network request failed');
        }

        const payload = await response.json().catch(() => ({}));
        if (!response.ok || payload?.status === 'error') {
          throw new Error(getErrorMessage(payload, 'Failed to load AI risk summary.'));
        }

        const items = Array.isArray(payload?.data) ? payload.data : payload?.data ? [payload.data] : [];
        if (!isActive) {
          return;
        }

        if (items.length === 0) {
          setState({ status: 'empty', data: null, error: null });
          return;
        }

        const first = items[0];
        const summary = first.summary || first || {};

        setState({
          status: 'loaded',
          data: {
            riskLevel: summary.risk_level || summary.riskLevel || 'Unknown',
            totalCases: summary.total_cases ?? summary.totalCases ?? null,
            trend: summary.trend_percentage ?? summary.trendPercentage ?? null,
          },
          error: null,
        });
      } catch (error) {
        if (!isActive) {
          return;
        }

        setState({
          status: 'error',
          data: null,
          error: error.message || 'Failed to load AI risk summary.',
        });
      }
    };

    load();

    return () => {
      isActive = false;
    };
  }, [apiBaseUrl, disease]);

  if (state.status === 'loading') {
    return (
      <div className="stat-card ai-risk">
        <span className="stat-value">--</span>
        <span className="stat-label">AI Risk</span>
        <div className="stat-sub">Loading...</div>
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="stat-card ai-risk error">
        <span className="stat-value">--</span>
        <span className="stat-label">AI Risk</span>
        <div className="stat-sub">Error: {state.error}</div>
      </div>
    );
  }

  if (state.status === 'empty') {
    return (
      <div className="stat-card ai-risk empty">
        <span className="stat-value">Low</span>
        <span className="stat-label">AI Risk</span>
        <div className="stat-sub">No signals</div>
      </div>
    );
  }

  const { riskLevel, totalCases, trend } = state.data || {};

  return (
    <div className="stat-card ai-risk">
      <span className="stat-value">{riskLevel || 'Unknown'}</span>
      <span className="stat-label">AI Risk</span>
      <div className="stat-sub">
        {totalCases !== null ? `${totalCases.toLocaleString()} cases` : trend !== null ? `Trend ${trend}%` : 'No metric'}
      </div>
    </div>
  );
}

export default AiRiskSummary;
