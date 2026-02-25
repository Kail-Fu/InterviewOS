import React from 'react';

const TermsAndConditions = ({ onClose }) => {
  const handleBackdrop = (e) => {
    if (e.target === e.currentTarget) onClose?.();
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      role="dialog"
      aria-modal="true"
      aria-labelledby="terms-title"
      onClick={handleBackdrop}
    >
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <h2 id="terms-title" className="text-3xl font-bold text-gray-900 mb-6 text-center">
          Terms and Conditions
        </h2>

        <div className="text-gray-700 space-y-4 prose lg:prose-xl">
          <p className="text-sm text-gray-500">Last Updated: October 12, 2025</p>

          <h3 className="text-xl font-semibold">1. Introduction</h3>
          <p>
            Welcome to <strong>Foretoken AI</strong> (“Foretoken,” “we,” “us”). These Terms govern your use of our
            assessment platform and related services (the “Services”). By accessing or using the Services, you agree to
            these Terms.
          </p>

          <h3 className="text-xl font-semibold">2. Eligibility &amp; Accounts</h3>
          <p>
            You must be 18+ (or 13+ with verifiable parental consent) to use the Services. Keep your account credentials
            confidential; you&apos;re responsible for activity under your account and for notifying us of unauthorized use.
          </p>

          <h3 className="text-xl font-semibold">3. Assessment Integrity (Prohibited Conduct)</h3>
          <ul className="list-disc list-inside space-y-2">
            <li>Submit only your own work; no collusion or real-time help from other people.</li>
            <li>Follow assessment-specific rules (time limits, allowed tools, language/runtime restrictions).</li>
            <li>Do not share, post, or redistribute assessment content or solutions.</li>
            <li>Do not interfere with or attempt to circumvent proctoring, monitoring, or security controls.</li>
            <li>
              Do not use bots, scraping, exploit/attack vectors, or reverse engineering beyond normal use of the
              Services.
            </li>
          </ul>
          <p>Violations may result in invalidation of results, disqualification, suspension, or account termination.</p>

          <h3 className="text-xl font-semibold">4. Identity Verification, Proctoring, and Recordings</h3>
          <p>
            Certain assessments may require identity verification and/or remote proctoring. By starting a proctored
            assessment, you consent (as disclosed in the assessment instructions) to:
          </p>
          <ul className="list-disc list-inside space-y-2">
            <li>
              <strong>Verification:</strong> capture and evaluation of your government ID and/or selfie for identity match.
            </li>
            <li>
              <strong>Monitoring &amp; Recording:</strong> capture of webcam, microphone, and/or screen; collection of
              browser/session telemetry (e.g., focus changes, copy/paste, tab switches), keystroke timings, and
              environmental snapshots.
            </li>
            <li>
              <strong>Human or automated review</strong> of these materials to validate integrity and investigate anomalies.
            </li>
            <li>
              <strong>Environmental checks</strong> (e.g., show surroundings, close disallowed materials), when required.
            </li>
          </ul>
          <p>
            We disclose when proctoring is required before you begin; declining required proctoring means you cannot take
            that assessment.
          </p>

          <h3 className="text-xl font-semibold">5. AI-Tool Usage &amp; Disclosure</h3>
          <p>
            Unless an assessment page states otherwise, you may use AI tools (e.g., ChatGPT, Copilot). We may capture
            AI-usage telemetry (e.g., clipboard events, timing patterns) and flag usage characteristics in your report.
            Hiring companies may receive an AI-usage disclosure indicating whether AI assistance was likely used and to
            what extent. If an assessment forbids AI tools, using them is a violation.
          </p>

          <h3 className="text-xl font-semibold">6. Submissions, Ownership, and License</h3>
          <ul className="list-disc list-inside space-y-2">
            <li>
              <strong>Your code/content:</strong> You retain ownership. You grant Foretoken a worldwide, non-exclusive,
              royalty-free license to use, reproduce, analyze, and display your submissions and related telemetry solely to
              (i) operate and improve the Services; (ii) evaluate, score, and report results; and (iii) ensure integrity
              and security.
            </li>
            <li>
              <strong>Employer access:</strong> If you were invited by a company or apply via our platform, you authorize
              us to share your submission, scores, recordings (if applicable), AI-usage disclosure, and integrity status
              with that employer.
            </li>
            <li>
              <strong>Third-party code/assets:</strong> You are responsible for rights to any code, data, or packages you
              include.
            </li>
          </ul>

          <h3 className="text-xl font-semibold">7. Scoring, Retakes, and Appeals</h3>
          <p>
            We may use automated tests, static analysis, and human review (e.g., code quality, performance, completeness),
            plus integrity signals (Section 4). Results are provided to you and/or the inviting employer.
          </p>
          <ul className="list-disc list-inside space-y-2">
            <li>
              <strong>Retakes:</strong> Eligibility, cool-down windows, and proctoring needs may be set by the employer or
              Foretoken.
            </li>
            <li>
              <strong>Appeals:</strong> If you believe there was an error (e.g., false proctoring flag or grader issue),
              contact support within 7 days with details; we may re-review at our discretion.
            </li>
          </ul>

          <h3 className="text-xl font-semibold">8. Privacy, Data Use, and Retention</h3>
          <p>
            Our Privacy Policy explains what we collect (account data, submissions, telemetry, recordings where applicable),
            why we collect it, and how we share it (including with inviting employers and vetted sub-processors). We retain
            data for as long as needed for assessments, integrity, dispute resolution, and legal obligations, then delete
            or de-identify it per policy. We host on reputable cloud providers and may store data in a region aligned with
            customer needs.
          </p>

          <h3 className="text-xl font-semibold">9. Security</h3>
          <p>
            We maintain administrative, technical, and physical safeguards appropriate to the risk (e.g., access controls,
            encryption in transit). No system is perfectly secure; report issues to us promptly.
          </p>

          <h3 className="text-xl font-semibold">10. Third-Party Services &amp; Open-Source</h3>
          <p>
            The Services may rely on third-party libraries, APIs, or cloud services. Your use of those components may be
            subject to their terms.
          </p>

          <h3 className="text-xl font-semibold">11. Fees and Refunds (for Employer/Paying Customers)</h3>
          <p>
            If you purchase paid features, you agree to the pricing and billing terms presented at checkout or in your
            order form. Except as required by law or contract, fees are non-refundable. We may suspend Services for
            non-payment.
          </p>

          <h3 className="text-xl font-semibold">12. Disclaimer</h3>
          <p>
            The Services are provided <strong>“as is”</strong> without warranties of any kind (including accuracy,
            availability, or fitness for a particular purpose). You are responsible for backing up your code and verifying
            outputs.
          </p>

          <h3 className="text-xl font-semibold">13. Limitation of Liability</h3>
          <p>
            To the maximum extent permitted by law, Foretoken and its affiliates will not be liable for indirect,
            incidental, special, consequential, or punitive damages. Our total liability for claims arising out of or
            relating to the Services will not exceed the greater of <strong>US $100</strong> or the amounts you paid to us
            for the Services in the 3 months preceding the claim.
          </p>

          <h3 className="text-xl font-semibold">14. Indemnification</h3>
          <p>
            You agree to indemnify and hold Foretoken harmless from claims arising out of your misuse of the Services, your
            submissions, or your violation of these Terms or applicable law.
          </p>

          <h3 className="text-xl font-semibold">15. Export, Sanctions &amp; Compliance</h3>
          <p>
            You will not use the Services in violation of export controls or sanctions laws. You are responsible for
            compliance in your jurisdiction.
          </p>

          <h3 className="text-xl font-semibold">16. Changes to the Services &amp; Terms</h3>
          <p>
            We may update features or these Terms. Material changes will be notified via the Services or email and become
            effective upon posting unless otherwise stated. Continued use after changes means acceptance.
          </p>

          <h3 className="text-xl font-semibold">17. Governing Law; Dispute Resolution</h3>
          <p>
            Except where prohibited, disputes will be resolved by <strong>binding arbitration</strong> on an individual
            basis; <strong>no class actions</strong>. Governing law and venue: Delaware, USA, unless otherwise specified
            in your order form. You may opt out of arbitration within 30 days of account creation by notifying us in
            writing.
          </p>

          <h3 className="text-xl font-semibold">18. Contact</h3>
          <p>
            Questions about these Terms or our Privacy Policy: <a href="mailto:legal@foretokenai.com">legal@foretokenai.com</a>.
          </p>
        </div>

        <div className="text-center mt-8">
          <button
            onClick={onClose}
            className="group relative inline-flex items-center justify-center overflow-hidden rounded-xl border border-black/80 bg-black px-8 py-3 text-white text-lg shadow-[inset_0_0_0_1px_rgba(255,255,255,.08),0_10px_30px_rgba(0,0,0,.20)] transition-transform active:scale-[.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-black/40"
          >
            <span className="relative z-10">Close</span>
            <span
              aria-hidden
              className="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/25 to-transparent transition-transform duration-700 ease-out group-hover:translate-x-full"
            />
          </button>
        </div>
      </div>
    </div>
  );
};

export default TermsAndConditions;