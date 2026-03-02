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

  const apiRequest = async (endpoint, options = {}) => {
    const response = await fetch(`${apiBaseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
      ...options,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      const message =
        data?.error?.message ||
        data?.message ||
        (typeof data?.error === 'string' ? data.error : null) ||
        `Request failed (${response.status})`;
      throw new Error(message);
    }

    return data;
  };

  const resolveDiseaseId = async (diseaseName) => {
    const result = await apiRequest('/api/diseases');
    const diseases = result?.data || [];
    const match = diseases.find(
      (item) =>
        String(item?.name || '').trim().toLowerCase() ===
        String(diseaseName).trim().toLowerCase()
    );

    if (!match?.disease_id) {
      throw new Error(
        `Disease "${diseaseName}" was not found in backend records. Please use a disease already in the database.`
      );
    }

    return Number(match.disease_id);
  };

  const resolveLocationId = async (city, state) => {
    const trimmedCity = String(city || '').trim();
    const trimmedState = String(state || '').trim();

    if (!trimmedCity) {
      throw new Error('City is required to map submission to a backend location record.');
    }

    const query = new URLSearchParams({ city: trimmedCity });
    if (trimmedState) {
      query.set('state_province', trimmedState);
    }

    const existing = await apiRequest(`/api/locations?${query.toString()}`);
    const existingLocations = existing?.data || [];
    if (existingLocations.length > 0 && existingLocations[0]?.location_id) {
      return Number(existingLocations[0].location_id);
    }

    const created = await apiRequest('/api/locations', {
      method: 'POST',
      body: JSON.stringify({
        city: trimmedCity,
        state_province: trimmedState || null,
        country: 'USA',
      }),
    });

    const createdLocation = created?.data?.[0];
    if (!createdLocation?.location_id) {
      throw new Error('Failed to create a new location record for this submission.');
    }

    return Number(createdLocation.location_id);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSuccess('');

    if (!form.disease || !form.caseCount || !form.dateFrom || !form.dateTo || !form.city) {
      setError('Please fill in all required fields.');
      return;
    }

    if (form.dateFrom > form.dateTo) {
      setError('Date From cannot be later than Date To.');
      return;
    }

    setError('');

    setIsSubmitting(true);

    try {
      const diseaseId = await resolveDiseaseId(form.disease);
      const locationId = await resolveLocationId(form.city, form.state);

      await apiRequest('/api/cases', {
        method: 'POST',
        body: JSON.stringify({
          disease_id: diseaseId,
          location_id: locationId,
          case_count: Number(form.caseCount),
          date_reported: form.dateTo,
          severity: 'medium',
          verified: false,
          data_source: 'case_submission_ui',
        }),
      });

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
            <label htmlFor="cs-city">City *</label>
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
            Note: Form submits through backend APIs and creates/uses matching
            location records before writing cases.
          </em>
        </p>
      </footer>
    </div>
  );
}

export default CaseSubmission;
