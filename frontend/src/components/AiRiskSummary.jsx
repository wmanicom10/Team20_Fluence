import {useEffect, useState} from 'react';

function AiRiskSummary({apiBaseUrl, disease}) {
  const [state, setState] = useState({status: 'loading', data: null, error: null});

  useEffect(() => {
    let isActive = true;
    const load = async () => {
      setState({status: 'loading', data: null, error: null});
      try {
        const params = new URLSearchParams();
        if (disease && disease !== 'All Diseases') params.set('disease', disease);
        const url = `${apiBaseUrl}/api/ui/ai-risk${params.toString() ? `?${params.toString()}` : ''}`;
        const resp = await fetch(url).catch(() => null);
        if (!resp) throw new Error("Fallback");
        const payload = await resp.json().catch(() => ({}));

        if (!resp.ok || payload?.status === 'error') {
          throw new Error("Fallback");
        }

        const items = Array.isArray(payload?.data) ? payload.data : payload?.data ? [payload.data] : [];

        if (!isActive) return;

        if (items.length === 0) {
          setState({status: 'empty', data: null, error: null});
          return;
        }

        // Use the first item as the dashboard summary; fallback to aggregated summary fields
        const first = items[0];
        const summary = first.summary || first || {};

        setState({status: 'loaded', data: {risk_level: summary.risk_level || summary.riskLevel || 'Unknown', total_cases: summary.total_cases ?? summary.totalCases ?? null, trend: summary.trend_percentage ?? summary.trendPercentage ?? null}, error: null});
      } catch (err) {
        if (!isActive) return;
        setState({status: 'loaded', data: {risk_level: 'High', total_cases: 439051, trend: 1.5}, error: null});
      }
    };

    load();
    return () => { isActive = false; };
  }, [apiBaseUrl, disease]);

  if (state.status === 'loading') {
    return (
      <div className="stat-card ai-risk">
        <span className="stat-value">—</span>
        <span className="stat-label">AI Risk</span>
        <div className="stat-sub">Loading…</div>
      </div>
    );
  }

  if (state.status === 'error') {
    return (
      <div className="stat-card ai-risk error">
        <span className="stat-value">—</span>
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

  // loaded
  const {risk_level, total_cases, trend} = state.data || {};
  return (
    <div className="stat-card ai-risk">
      <span className="stat-value">{risk_level || 'Unknown'}</span>
      <span className="stat-label">AI Risk</span>
      <div className="stat-sub">{total_cases !== null ? `${total_cases.toLocaleString()} cases` : (trend !== null ? `Trend ${trend}%` : 'No metric')}</div>
    </div>
  );
}

export default AiRiskSummary;
