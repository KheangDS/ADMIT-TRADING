<template>
  <div class="max-w-4xl mx-auto py-6 sm:py-10 space-y-8 text-slate-800">
    <!-- Header -->
    <div class="border-b border-slate-200 pb-6 space-y-2">
      <div class="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80 text-xs font-bold">
        <ShieldCheckIcon class="w-3.5 h-3.5 text-emerald-600" />
        <span>Privacy & Data Protection</span>
      </div>
      <h1 class="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight m-0">
        Privacy Policy
      </h1>
      <p class="text-xs sm:text-sm text-slate-500 m-0">
        Last Updated: October 2026 · Effective Date: October 2026 · Kingdom of Cambodia
      </p>
    </div>

    <!-- Main Content -->
    <div class="bg-white rounded-2xl border border-slate-200/90 shadow-xs p-6 sm:p-10 space-y-8 text-sm leading-relaxed text-slate-700">
      
      <!-- Section 1: Overview -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">1</span>
          <span>Overview & Scope</span>
        </h2>
        <p class="m-0 text-justify">
          ADMIT Trading ("we", "us", or "our") is dedicated to protecting the privacy of our visitors, members, and researchers. This Privacy Policy describes how we collect, process, store, and safeguard your personal data when you use our website, access our trade intelligence dashboards, or authenticate with your account.
        </p>
      </section>

      <!-- Section 2: Information We Collect -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">2</span>
          <span>Information We Collect</span>
        </h2>
        <p class="m-0 text-justify">
          We collect only the minimum personal information required to deliver a secure, high-integrity service:
        </p>
        <div class="grid sm:grid-cols-2 gap-3 pt-1">
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
            <h4 class="font-bold text-slate-900 text-xs m-0 flex items-center gap-1.5">
              <UserIcon class="w-3.5 h-3.5 text-sky-600" />
              <span>Direct Account Information</span>
            </h4>
            <p class="text-xs text-slate-600 m-0">
              Your name, email address, and a cryptographically hashed password (never stored in plaintext).
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
            <h4 class="font-bold text-slate-900 text-xs m-0 flex items-center gap-1.5">
              <GlobeIcon class="w-3.5 h-3.5 text-emerald-600" />
              <span>Google OAuth Profile Data</span>
            </h4>
            <p class="text-xs text-slate-600 m-0">
              When signing in with Google: your verified email, display name, and avatar picture provided by Google Identity.
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
            <h4 class="font-bold text-slate-900 text-xs m-0 flex items-center gap-1.5">
              <CreditCardIcon class="w-3.5 h-3.5 text-indigo-600" />
              <span>Payment Records</span>
            </h4>
            <p class="text-xs text-slate-600 m-0">
              Bakong KHQR payment timestamp, transaction reference code, and currency (USD/KHR). We do not collect credit cards.
            </p>
          </div>
          <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 space-y-1.5">
            <h4 class="font-bold text-slate-900 text-xs m-0 flex items-center gap-1.5">
              <LockIcon class="w-3.5 h-3.5 text-amber-600" />
              <span>Security & Session Data</span>
            </h4>
            <p class="text-xs text-slate-600 m-0">
              IP addresses in server audit logs, session rotation tokens, and CSRF anti-tamper security signatures.
            </p>
          </div>
        </div>
      </section>

      <!-- Section 3: Google User Data Compliance -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">3</span>
          <span>Google API Services User Data Policy Compliance</span>
        </h2>
        <div class="bg-sky-50/70 border border-sky-200/80 rounded-xl p-4 text-xs text-sky-950 space-y-2">
          <p class="m-0 text-justify">
            ADMIT Trading's use and transfer of information received from Google APIs adheres to the <strong>Google API Services User Data Policy</strong>, including the Limited Use requirements:
          </p>
          <ul class="list-disc pl-5 space-y-1 text-slate-800 m-0">
            <li><strong>Strict Authentication Use:</strong> We request only the <code>openid</code>, <code>email</code>, and <code>profile</code> scopes to authenticate your identity.</li>
            <li><strong>No Data Brokering:</strong> We never sell, transfer, or license Google user data to data brokers, advertisers, or unauthorized third parties.</li>
            <li><strong>No Generalized AI Training:</strong> Personal data and Google user data are never used to train generalized artificial intelligence or machine learning models.</li>
          </ul>
        </div>
      </section>

      <!-- Section 4: Cookie Policy -->
      <section id="cookies" class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">4</span>
          <span>Cookie & Local Storage Policy</span>
        </h2>
        <p class="m-0 text-justify">
          We believe in transparent, privacy-first engineering. Our platform sets <strong>zero third-party tracking or advertising cookies</strong>. We utilize only strictly necessary cookies and local storage items:
        </p>
        <div class="border border-slate-200 rounded-xl overflow-hidden">
          <table class="w-full text-left text-xs border-collapse">
            <thead class="bg-slate-50 text-slate-700 border-b border-slate-200">
              <tr>
                <th class="p-3 font-bold">Cookie / Storage Key</th>
                <th class="p-3 font-bold">Category</th>
                <th class="p-3 font-bold">Purpose</th>
                <th class="p-3 font-bold">Duration</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 font-mono text-[11px] text-slate-600">
              <tr>
                <td class="p-3 font-bold text-slate-900">agritrade_session</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">Strictly Necessary</span></td>
                <td class="p-3 font-sans">Encrypted HTTP-only token keeping you signed in securely.</td>
                <td class="p-3">Session / 3 Days</td>
              </tr>
              <tr>
                <td class="p-3 font-bold text-slate-900">X-CSRF-Token</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">Security</span></td>
                <td class="p-3 font-sans">Prevents cross-site request forgery attacks on state changes.</td>
                <td class="p-3">Session</td>
              </tr>
              <tr>
                <td class="p-3 font-bold text-slate-900">admit_cookie_consent</td>
                <td class="p-3"><span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-bold">Preference</span></td>
                <td class="p-3 font-sans">Remembers that you acknowledged the cookie consent banner.</td>
                <td class="p-3">Persistent (Local)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Section 5: Third-Party Infrastructure -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">5</span>
          <span>Third-Party Subprocessors & Infrastructure</span>
        </h2>
        <p class="m-0 text-justify">
          To provide a reliable, high-availability platform, we partner with industry-standard subprocessors under strict data protection terms:
        </p>
        <ul class="list-disc pl-5 space-y-1.5 m-0 text-justify">
          <li><strong>Google Identity Services:</strong> Provides federated OAuth authentication.</li>
          <li><strong>Bakong / National Bank of Cambodia:</strong> Facilitates secure interbank QR transactions.</li>
          <li><strong>Resend Email Infrastructure:</strong> Delivers transactional emails, receipts, and password resets via authenticated SMTP/API.</li>
          <li><strong>Cloud Container Infrastructure:</strong> Hosts our containerized Nginx, PostgreSQL, and Redis clusters with encrypted volumes.</li>
        </ul>
      </section>

      <!-- Section 6: Data Retention & Security -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">6</span>
          <span>Data Security & Encryption</span>
        </h2>
        <p class="m-0 text-justify">
          We enforce enterprise-grade security measures across all layers of our stack:
        </p>
        <ul class="list-disc pl-5 space-y-1 m-0 text-justify">
          <li>All network traffic is encrypted via <strong>HTTPS (TLS 1.3)</strong> with strict transport security.</li>
          <li>Session cookies are configured with <code>HttpOnly</code>, <code>Secure</code>, and <code>SameSite=Lax</code> flags to prevent cross-site scripting (XSS) and cross-origin leakage.</li>
          <li>Administrative portals are isolated under distinct cryptographic session spaces.</li>
        </ul>
      </section>

      <!-- Section 7: User Rights -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">7</span>
          <span>Your Data Rights & Deletion Requests</span>
        </h2>
        <p class="m-0 text-justify">
          You retain complete ownership of your personal data. At any time, you have the right to:
        </p>
        <ul class="list-disc pl-5 space-y-1 m-0 text-justify">
          <li><strong>Access:</strong> Request a full copy of the personal information associated with your account.</li>
          <li><strong>Rectification:</strong> Correct any outdated profile details directly in your Account settings.</li>
          <li><strong>Account Deletion:</strong> Request the permanent, irreversible deletion of your user account, active membership, and associated transaction history.</li>
        </ul>
      </section>

      <!-- Section 8: Contact -->
      <section class="space-y-3">
        <h2 class="text-base sm:text-lg font-bold text-slate-900 m-0 flex items-center gap-2">
          <span class="w-6 h-6 rounded-lg bg-slate-100 text-slate-700 text-xs font-bold inline-flex items-center justify-center">8</span>
          <span>Privacy Inquiries & Data Protection Contact</span>
        </h2>
        <p class="m-0 text-justify">
          If you have questions regarding this Privacy Policy, cookie settings, or would like to submit a data deletion request, please reach out to our privacy team:
        </p>
        <div class="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-xs font-mono text-slate-700 space-y-1">
          <p class="m-0 font-bold text-slate-900 font-sans">ADMIT Trading Data Protection Office</p>
          <p class="m-0">Email: privacy@admittrading.com</p>
          <p class="m-0">Location: Phnom Penh, Kingdom of Cambodia</p>
        </div>
      </section>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ShieldCheckIcon, UserIcon, GlobeIcon, CreditCardIcon, LockIcon } from 'lucide-vue-next';
</script>

