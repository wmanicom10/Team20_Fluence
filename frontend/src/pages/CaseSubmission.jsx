import { useState } from 'react';

/**
 * CaseSubmission Page Component
 * TM20-54: UI for submitting disease case reports
 *
 * Accepts: disease type, case count, date range, location
 *
 * TODO (remaining work):
 *  - Add severity dropdown
 *  - Add optional notes textarea
 *  - Improve validation (date range check, better error messages)
 *  - Add success/confirmation screen after submit
 *  - TM20-55: Wire form to POST /cases backend endpoint
 */

const DISEASE_OPTIONS = [
  'Influenza A',
  'Influenza B',
  'COVID-19',
  'RSV',
  'Norovirus',
  'Strep A',
  'Measles',
  'Pertussis',
  'Hepatitis A',
  'Tuberculosis',
];

function CaseSubmission() {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';
  const [form, setForm] = useState({
    disease: '',
    caseCount: '',
    dateFrom: '',
    dateTo: '',
    city: '',
    state: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const trySubmit = async (endpoint, payload) => {
    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message = data?.message || data?.error || `Request failed (${response.status})`;
      throw new Error(message);
    }

    return data;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess('');

    // Basic validation — just checks required fields are filled
    if (!form.disease || !form.caseCount || !form.dateFrom || !form.dateTo) {
      setError('Please fill in all required fields.');
      return;
    }

    if (form.dateFrom > form.dateTo) {
      setError('Date From cannot be later than Date To.');
      return;
    }

    setError('');

    const dbPayload = {
      case_count: Number(form.caseCount),
      date_reported: form.dateTo,
      severity: 'unknown',
      verified: false,
      data_source: 'case_submission_ui',
      disease_name: form.disease,
      city: form.city || null,
      state: form.state || null,
      date_from: form.dateFrom,
      date_to: form.dateTo,
    };

    const pocPayload = {
      patient_id: `hospital-report-${Date.now()}`,
      diagnosis: form.disease,
      reported_at: form.dateTo,
      notes: `Count: ${form.caseCount}. Location: ${form.city || 'N/A'}, ${form.state || 'N/A'}. Range: ${form.dateFrom} to ${form.dateTo}`,
    };

    setIsSubmitting(true);

    try {
      try {
        await trySubmit('/cases', dbPayload);
      } catch {
        await trySubmit('/api/cases', pocPayload);
      }

      setSuccess('Case submission sent successfully.');
      setForm({
        disease: '',
        caseCount: '',
        dateFrom: '',
        dateTo: '',
        city: '',
        state: '',
      });
    } catch (submitError) {
      setError(
        `Submission failed: ${submitError.message}. Backend endpoint may still be in progress.`
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="case-submission">
      <header className="page-header">
        <h1>Submit Disease Case Report</h1>
        <p>Report new disease cases for inclusion in the surveillance system</p>
      </header>

      <form className="case-form" onSubmit={handleSubmit}>
        {/* Disease & Count */}
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="cs-disease">Disease Type *</label>
            <select
              id="cs-disease"
              name="disease"
              value={form.disease}
              onChange={handleChange}
            >
              <option value="" disabled>
                Select a disease
              </option>
              {DISEASE_OPTIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          <div className="form-field">
            <label htmlFor="cs-count">Case Count *</label>
            <input
              id="cs-count"
              name="caseCount"
              type="number"
              min="1"
              value={form.caseCount}
              onChange={handleChange}
              placeholder="e.g. 25"
            />
          </div>
        </div>

        {/* Date Range */}
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="cs-date-from">Date From *</label>
            <input
              id="cs-date-from"
              name="dateFrom"
              type="date"
              value={form.dateFrom}
              onChange={handleChange}
            />
          </div>

          <div className="form-field">
            <label htmlFor="cs-date-to">Date To *</label>
            <input
              id="cs-date-to"
              name="dateTo"
              type="date"
              value={form.dateTo}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Location */}
        <div className="form-row">
          <div className="form-field">
            <label htmlFor="cs-city">City</label>
            <input
              id="cs-city"
              name="city"
              type="text"
              value={form.city}
              onChange={handleChange}
              placeholder="e.g. Syracuse"
            />
          </div>

          <div className="form-field">
            <label htmlFor="cs-state">State</label>
            <input
              id="cs-state"
              name="state"
              type="text"
              value={form.state}
              onChange={handleChange}
              placeholder="e.g. NY"
            />
          </div>
        </div>

        {/* TODO: Add severity dropdown and notes textarea here */}

        {error && <div className="form-error">{error}</div>}
        {success && <div className="form-success">{success}</div>}

        <div className="form-actions">
          <button type="submit" className="cta-button" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Report'}
          </button>
        </div>
      </form>

      <footer className="data-footer">
        <p>
          <em>
            Note: Form now attempts backend submission. If API endpoints are not
            fully available yet, you may see a temporary error.
          </em>
        </p>
      </footer>
    </div>
  );
}

export default CaseSubmission;
