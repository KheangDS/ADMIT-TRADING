<template>
  <footer class="bg-white border-t border-slate-200/80 mt-auto text-slate-600 transition-colors">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24 md:pb-6">
      
      <!-- Desktop: Sleek Minimalist Inline Bar (Option 2) -->
      <div class="hidden md:flex items-center justify-between gap-6">
        <!-- Brand & Tagline -->
        <div class="flex items-center gap-3">
          <router-link to="/" class="inline-flex items-center group">
            <img 
              src="/admit-trading.png" 
              alt="ADMIT TRADING" 
              class="h-8 w-auto object-contain transition-opacity group-hover:opacity-90" 
            />
          </router-link>
          <span class="h-4 w-px bg-slate-200"></span>
          <span class="text-xs font-semibold text-slate-500">
            Agricultural Trade Intelligence
          </span>
        </div>

        <!-- Inline Navigation Links -->
        <nav class="flex items-center gap-6 text-xs font-medium text-slate-600" aria-label="Footer Navigation">
          <router-link to="/dashboard" class="hover:text-sky-600 transition-colors">
            Trade Overview
          </router-link>
          <router-link to="/compare" class="hover:text-sky-600 transition-colors">
            Comparison
          </router-link>
          <router-link to="/plans" class="hover:text-sky-600 transition-colors">
            Membership
          </router-link>
          <router-link to="/terms" class="hover:text-sky-600 transition-colors">
            Terms of Service
          </router-link>
          <router-link to="/privacy" class="hover:text-sky-600 transition-colors">
            Privacy Policy
          </router-link>
          <button 
            type="button" 
            class="hover:text-sky-600 transition-colors bg-transparent border-0 p-0 cursor-pointer font-medium text-slate-600 text-xs"
            @click="reopenCookies"
          >
            Cookie Preferences
          </button>
        </nav>
      </div>

      <!-- Mobile: Compact 2-Column Layout -->
      <div class="flex flex-col gap-6 md:hidden">
        <!-- Brand -->
        <div class="flex items-center">
          <router-link to="/" class="inline-flex items-center">
            <img 
              src="/admit-trading.png" 
              alt="ADMIT TRADING" 
              class="h-7 w-auto object-contain" 
            />
          </router-link>
        </div>

        <!-- 2 Columns on Mobile -->
        <div class="grid grid-cols-2 gap-6 text-xs">
          <!-- Col: Platform -->
          <div class="space-y-2">
            <h5 class="text-[11px] font-bold uppercase tracking-wider text-slate-900 m-0">Platform</h5>
            <ul class="space-y-2 list-none p-0 m-0">
              <li>
                <router-link to="/dashboard" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Trade Overview
                </router-link>
              </li>
              <li>
                <router-link to="/compare" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Comparison
                </router-link>
              </li>
              <li>
                <router-link to="/plans" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Membership Plans
                </router-link>
              </li>
              <li>
                <router-link to="/account" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Account & Billing
                </router-link>
              </li>
            </ul>
          </div>

          <!-- Col: Legal & Trust -->
          <div class="space-y-2">
            <h5 class="text-[11px] font-bold uppercase tracking-wider text-slate-900 m-0">Legal & Trust</h5>
            <ul class="space-y-2 list-none p-0 m-0">
              <li>
                <router-link to="/terms" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Terms of Service
                </router-link>
              </li>
              <li>
                <router-link to="/privacy" class="text-slate-600 hover:text-sky-600 transition-colors">
                  Privacy Policy
                </router-link>
              </li>
              <li>
                <button 
                  type="button" 
                  class="text-slate-600 hover:text-sky-600 transition-colors text-xs p-0 m-0 bg-transparent border-0 cursor-pointer text-left"
                  @click="reopenCookies"
                >
                  Cookie Preferences
                </button>
              </li>
              <li>
                <span class="text-[11px] text-slate-400">
                  Google OAuth Compliant
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <!-- Bottom Bar (Both Desktop and Mobile) -->
      <div class="mt-5 pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-2.5 text-xs text-slate-400">
        <p class="m-0 text-center sm:text-left">
          © {{ currentYear }} ADMIT TRADING. All rights reserved.
        </p>
        <div class="flex items-center gap-3 text-[11px] text-slate-400">
          <span class="inline-flex items-center gap-1.5 text-slate-500 font-medium">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            Systems Operational
          </span>
          <span>•</span>
          <span>Phnom Penh, Cambodia</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const currentYear = computed(() => new Date().getFullYear());

function reopenCookies() {
  window.dispatchEvent(new CustomEvent('admit:open-cookie-banner'));
}
</script>
