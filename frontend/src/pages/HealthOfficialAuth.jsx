import { useState } from 'react';
import { Link } from 'react-router-dom';

/**
 * HealthOfficialAuth Page Component
 * TM20-67: UI for authorizing health officials
 *
 * Health officials submit their credentials (license number, issuing state, etc.)
 * to be verified before gaining elevated access (e.g., submitting case reports).
 *
 * TM20-69 will wire this form to the backend for actual verification.
 */

const US_STATES = [
  'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
  'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
  'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
  'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
  'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
  'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
  'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
  'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
  'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
  'West Virginia', 'Wisconsin', 'Wyoming',
];

function HealthOfficialAuth() {
  const [form, setForm] = useState({
    fullName: '',
    email: '',
    licenseNumber: '',
    issuingState: '',
    organization: '',
    title: '',
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const validate = () => {
    if (!form.fullName.trim()) return 'Full name is required.';
    if (!form.email.trim()) return 'Email is required.';
    if (!form.licenseNumber.trim()) return 'License / credential number is required.';
    if (!form.issuingState) return 'Please select the issuing state.';
    if (!form.organization.trim()) return 'Organization is required.';
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);

    // Placeholder — TM20-69 will replace this with a real backend call
    // to POST /api/auth/verify-official (or similar endpoint)
    try {
      // Simulate network delay for now
      await new Promise((resolve) => setTimeout(resolve, 800));

      // TODO (TM20-69): Replace with actual API call, e.g.:
      // const res = await fetch(`${apiBaseUrl}/api/auth/verify-official`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({
      //     full_name: form.fullName,
      //     email: form.email,
      //     license_number: form.licenseNumber,
      //     issuing_state: form.issuingState,
      //     organization: form.organization,
      //     title: form.title,
      //   }),
      // });

      console.log('Health official verification submitted:', form);
      setSuccess(
        'Your credentials have been submitted for verification. ' +
        'You will be notified once your status is confirmed.'
      );
      setForm({
        fullName: '',
        email: '',
        licenseNumber: '',
        issuingState: '',
        organization: '',
        title: '',
      });
    } catch (err) {
      setError(err.message || 'Verification request failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">🏥</span>
          <h2>Health Official Verification</h2>
          <p className="muted">
            Submit your credentials to verify your identity as a health official.
            Verified officials gain access to submit case reports and view restricted data.
          </p>
        </div>

        {error && <div className="form-error">{error}</div>}
        {success && <div className="form-success">{success}</div>}

        {!success && (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-row">
              <label>
                Full Name <span className="required">*</span>
                <input
                  type="text"
                  name="fullName"
                  value={form.fullName}
                  onChange={handleChange}
                  placeholder="Dr. Jane Smith"
                  required
                />
              </label>

              <label>
                Email <span className="required">*</span>
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={handleChange}
                  placeholder="jane.smith@health.gov"
                  required
                />
              </label>
            </div>

            <div className="form-row">
              <label>
                License / Credential Number <span className="required">*</span>
                <input
                  type="text"
                  name="licenseNumber"
                  value={form.licenseNumber}
                  onChange={handleChange}
                  placeholder="e.g. MD-123456"
                  required
                />
              </label>

              <label>
                Issuing State <span className="required">*</span>
                <select
                  name="issuingState"
                  value={form.issuingState}
                  onChange={handleChange}
                  required
                >
                  <option value="">Select state...</option>
                  {US_STATES.map((state) => (
                    <option key={state} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label>
              Organization / Institution <span className="required">*</span>
              <input
                type="text"
                name="organization"
                value={form.organization}
                onChange={handleChange}
                placeholder="e.g. Syracuse Department of Health"
                required
              />
            </label>

            <label>
              Title / Role <span className="optional">(optional)</span>
              <input
                type="text"
                name="title"
                value={form.title}
                onChange={handleChange}
                placeholder="e.g. Epidemiologist, Public Health Officer"
              />
            </label>

            <div className="auth-notice">
              <p>
                <strong>Note:</strong> Your credentials will be validated against
                an external verification source. You will receive a confirmation
                once your status is approved. Until verified, case submission and
                other health official features remain restricted.
              </p>
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="cta-button"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Submitting...' : 'Submit for Verification'}
              </button>
            </div>
          </form>
        )}

        {success && (
          <div className="auth-next-steps">
            <p>While you wait for verification, you can:</p>
            <ul>
              <li><Link to="/data">Browse disease data</Link></li>
              <li><Link to="/map">View the outbreak map</Link></li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default HealthOfficialAuth;
