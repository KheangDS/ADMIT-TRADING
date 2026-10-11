<template>
  <div class="space-y-16 sm:space-y-24 py-6 sm:py-12">
    <!-- Hero Section -->
    <section class="relative">
      <!-- Decorative Background Ambient Glow -->
      <div class="absolute -top-12 -left-12 w-96 h-96 bg-sky-400/10 rounded-full blur-3xl pointer-events-none -z-10"></div>
      <div class="absolute top-1/2 -right-12 w-96 h-96 bg-indigo-400/10 rounded-full blur-3xl pointer-events-none -z-10"></div>

      <div class="grid lg:grid-cols-12 gap-10 lg:gap-12 items-center">
        <!-- Hero Copy -->
        <div class="lg:col-span-7 space-y-6 text-left">
          <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-200/80 text-xs font-bold tracking-wide">
            <SparklesIcon class="w-3.5 h-3.5 text-sky-600 animate-pulse" />
            <span>Cambodian Agricultural Trade Intelligence</span>
          </div>

          <h1 class="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-slate-900 leading-[1.12]">
            Turn trade data into <span class="text-transparent bg-clip-text bg-gradient-to-r from-sky-700 via-sky-600 to-indigo-700">clearer decisions</span>.
          </h1>

          <p class="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl text-justify">
            Explore official commodity export trends, compare international markets across HS4/HS8 codes, and access proprietary member intelligence reports in one unified, responsive workspace.
          </p>

          <!-- CTA Buttons -->
          <div class="flex flex-wrap items-center gap-3.5 pt-2">
            <router-link 
              to="/plans" 
              class="inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-gradient-to-r from-sky-700 to-sky-800 hover:from-sky-800 hover:to-sky-900 text-white font-bold text-sm shadow-md hover:shadow-lg transition-all cursor-pointer group"
            >
              <span>Explore Membership Plans</span>
              <ArrowRightIcon class="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </router-link>

            <router-link 
              :to="auth.canAccessMembers ? '/dashboard' : '/login'"
              class="inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-bold text-sm shadow-2xs hover:shadow-xs transition-all cursor-pointer"
            >
              <LayoutDashboardIcon v-if="auth.canAccessMembers" class="w-4 h-4 text-sky-600" />
              <UserIcon v-else class="w-4 h-4 text-slate-500" />
              <span>{{ auth.canAccessMembers ? 'Launch Member Dashboard' : 'Sign In / Register' }}</span>
            </router-link>
          </div>

          <!-- Feature Highlights Tags -->
          <div class="pt-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-500 font-medium">
            <span class="inline-flex items-center gap-1.5">
              <CheckCircle2Icon class="w-4 h-4 text-emerald-600" />
              Transparent USD Pricing
            </span>
            <span class="inline-flex items-center gap-1.5">
              <CheckCircle2Icon class="w-4 h-4 text-emerald-600" />
              Live MEF Exchange Rates
            </span>
            <span class="inline-flex items-center gap-1.5">
              <CheckCircle2Icon class="w-4 h-4 text-emerald-600" />
              Verified ABA QR Payments
            </span>
          </div>
        </div>

        <!-- Hero Preview Mockup Card (Real Live Dataset KPIs) -->
        <div class="lg:col-span-5 relative">
          <!-- Ambient Glow Orbs behind the Glass Card -->
          <div class="absolute -top-6 -right-6 w-56 h-56 bg-[#4499cf]/30 rounded-full blur-3xl pointer-events-none -z-10"></div>
          <div class="absolute -bottom-6 -left-6 w-48 h-48 bg-emerald-400/25 rounded-full blur-2xl pointer-events-none -z-10"></div>

          <!-- Glassmorphic Card Container -->
          <div class="bg-gradient-to-br from-[#06284e]/95 via-[#093563]/90 to-[#041d39]/95 backdrop-blur-2xl rounded-3xl p-6 sm:p-8 text-white shadow-2xl shadow-[#06284e]/50 border border-[#4499cf]/40 space-y-6 relative overflow-hidden transition-all duration-300 hover:border-[#4499cf]/60">
            <!-- Decorative Inner Ambient Blur Accent -->
            <div class="absolute -right-20 -top-20 w-52 h-52 bg-[#4499cf]/25 rounded-full blur-2xl pointer-events-none"></div>
            <div class="absolute -left-16 -bottom-16 w-44 h-44 bg-emerald-500/20 rounded-full blur-2xl pointer-events-none"></div>

            <!-- Top Status Row -->
            <div class="flex items-center justify-between border-b border-white/15 pb-4 relative z-10">
              <div class="flex items-center gap-2.5">
                <span class="w-3 h-3 rounded-full bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400"></span>
                <span class="text-sm font-extrabold text-white tracking-wide">Live Trade Stream</span>
              </div>
              <span class="text-xs font-mono font-bold text-sky-200 bg-[#06284e]/95 px-3 py-1 rounded-full border border-sky-400/50 shadow-xs backdrop-blur-md">
                MEF Sync Active
              </span>
            </div>

            <!-- Mini KPI Preview Grid with Real Data -->
            <div class="grid grid-cols-2 gap-3.5 relative z-10">
              <!-- KPI 1: Destination Markets -->
              <div class="bg-white/10 backdrop-blur-xl rounded-2xl p-4 sm:p-4.5 border border-white/20 space-y-2 transition-all duration-300 hover:bg-white/15 hover:border-sky-300/60 shadow-inner">
                <div class="flex items-center justify-between">
                  <p class="text-[11px] text-sky-200 font-extrabold uppercase tracking-wider">Destination Markets</p>
                  <GlobeIcon class="w-4 h-4 text-sky-300" />
                </div>
                <p class="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {{ tradeStats.destination_countries_count.toLocaleString() }} <span class="text-xs font-extrabold text-sky-200 bg-sky-500/20 px-2 py-0.5 rounded border border-sky-400/40">Countries</span>
                </p>
                <p class="text-xs text-slate-100 font-bold tracking-tight">Global Trading Partners</p>
              </div>

              <!-- KPI 2: Total Commodities -->
              <div class="bg-white/10 backdrop-blur-xl rounded-2xl p-4 sm:p-4.5 border border-white/20 space-y-2 transition-all duration-300 hover:bg-white/15 hover:border-emerald-300/60 shadow-inner">
                <div class="flex items-center justify-between">
                  <p class="text-[11px] text-emerald-200 font-extrabold uppercase tracking-wider">Total Commodities</p>
                  <LayersIcon class="w-4 h-4 text-emerald-300" />
                </div>
                <p class="text-2xl sm:text-3xl font-black text-white tracking-tight">
                  {{ tradeStats.total_commodities_count.toLocaleString() }} <span class="text-xs font-extrabold text-emerald-200 bg-emerald-500/20 px-2 py-0.5 rounded border border-emerald-400/40">Products</span>
                </p>
                <p class="text-xs text-slate-100 font-bold tracking-tight">HS4 / HS8 Tariff Lines</p>
              </div>
            </div>

            <!-- Live Features List -->
            <div class="space-y-3 pt-1 relative z-10">
              <div class="flex items-start gap-3 bg-white/10 backdrop-blur-md rounded-xl p-3.5 border border-white/15 transition-all duration-200 hover:bg-white/15 hover:border-white/25">
                <BarChart3Icon class="w-5 h-5 text-sky-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 class="text-xs sm:text-sm font-extrabold text-white tracking-tight">Harmonized System (HS4/HS8) Granularity</h4>
                  <p class="text-xs text-sky-100 font-semibold leading-relaxed mt-0.5">Drill down from high-level categories to specific tariff lines.</p>
                </div>
              </div>

              <div class="flex items-start gap-3 bg-white/10 backdrop-blur-md rounded-xl p-3.5 border border-white/15 transition-all duration-200 hover:bg-white/15 hover:border-white/25">
                <BotIcon class="w-5 h-5 text-indigo-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 class="text-xs sm:text-sm font-extrabold text-white tracking-tight">Dataset-Grounded AI Insights</h4>
                  <p class="text-xs text-indigo-100 font-semibold leading-relaxed mt-0.5">Instant analytical answers calibrated to published trade periods.</p>
                </div>
              </div>

              <div class="flex items-start gap-3 bg-white/10 backdrop-blur-md rounded-xl p-3.5 border border-white/15 transition-all duration-200 hover:bg-white/15 hover:border-white/25">
                <FileTextIcon class="w-5 h-5 text-amber-300 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 class="text-xs sm:text-sm font-extrabold text-white tracking-tight">Member Strategy & PDF Reports</h4>
                  <p class="text-xs text-amber-100 font-semibold leading-relaxed mt-0.5">Executive presentations and downloadable policy documentation.</p>
                </div>
              </div>
            </div>

            <!-- Bottom Data Sync Footer -->
            <div class="pt-2 border-t border-white/15 flex items-center justify-between text-xs text-slate-100 relative z-10 font-bold">
              <span class="inline-flex items-center gap-2 text-white">
                <CheckCircle2Icon class="w-4 h-4 text-emerald-400" />
                <span>{{ tradeStats.total_records > 0 ? `${tradeStats.total_records.toLocaleString()} Trade Records Analyzed` : 'No Published Records' }}</span>
              </span>
              <span class="font-mono text-sky-200 bg-white/15 px-2.5 py-1 rounded-md text-xs border border-white/20 shadow-xs font-bold">
                {{ tradeStats.reporting_period || 'Pending Publication' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Key Intelligence Capabilities Grid -->
    <section class="space-y-8">
      <div class="text-center max-w-2xl mx-auto">
        <h2 class="text-2xl sm:text-3xl font-black text-slate-900">
          Agricultural Exporters & Analysts
        </h2>
      </div>

      <div class="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="feature in features" 
          :key="feature.title"
          class="surface hover:border-sky-300 hover:shadow-md transition-all space-y-3 flex flex-col justify-start group p-6 rounded-2xl"
        >
          <div class="w-10 h-10 rounded-xl bg-sky-50 text-sky-700 flex items-center justify-center font-bold mb-1 group-hover:bg-sky-700 group-hover:text-white transition-colors">
            <component :is="feature.icon" class="w-5 h-5" />
          </div>
          <h3 class="text-base font-bold text-slate-900 group-hover:text-sky-800 transition-colors">
            {{ feature.title }}
          </h3>
          <p class="text-sm text-slate-600 leading-relaxed">
            {{ feature.text }}
          </p>
        </div>
      </div>
    </section>

    <!-- 3-Step Simple Membership Process -->
    <section class="bg-gradient-to-b from-slate-100/80 to-slate-50 rounded-3xl p-8 sm:p-12 border border-slate-200/80 space-y-8">
      <div class="text-center max-w-xl mx-auto space-y-2">
        <span class="text-xs font-bold text-sky-700 uppercase tracking-wider">Transparent & Streamlined</span>
        <h2 class="text-2xl sm:text-3xl font-black text-slate-900">How Membership Access Works</h2>
        <p class="text-slate-600 text-sm">Follow three easy steps to activate your platform access.</p>
      </div>

      <div class="grid sm:grid-cols-3 gap-6">
        <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-3 text-center">
          <div class="w-10 h-10 rounded-full bg-sky-100 text-sky-800 font-black text-sm flex items-center justify-center mx-auto">
            1
          </div>
          <h3 class="font-bold text-slate-900 text-sm">Select Your Plan</h3>
          <p class="text-xs text-slate-600 leading-relaxed">
            Choose from flexible USD subscription intervals tailored to your organization.
          </p>
        </div>

        <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-3 text-center">
          <div class="w-10 h-10 rounded-full bg-sky-100 text-sky-800 font-black text-sm flex items-center justify-center mx-auto">
            2
          </div>
          <h3 class="font-bold text-slate-900 text-sm">Scan ABA / KHQR</h3>
          <p class="text-xs text-slate-600 leading-relaxed">
            Scan the official QR code to transfer the exact amount with your payer account name.
          </p>
        </div>

        <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs space-y-3 text-center">
          <div class="w-10 h-10 rounded-full bg-sky-100 text-sky-800 font-black text-sm flex items-center justify-center mx-auto">
            3
          </div>
          <h3 class="font-bold text-slate-900 text-sm">Instant Review & Receipts</h3>
          <p class="text-xs text-slate-600 leading-relaxed">
            Admin validates payment and unlocks your analytics dashboard with downloadable official PDF receipts.
          </p>
        </div>
      </div>
    </section>

    <!-- Bottom CTA Banner -->
    <section class="bg-gradient-to-r from-sky-800 via-sky-900 to-indigo-950 rounded-3xl p-8 sm:p-12 text-white text-center shadow-xl space-y-6 relative overflow-hidden">
      <div class="max-w-2xl mx-auto space-y-4">
        <h2 class="text-2xl sm:text-4xl font-black tracking-tight">Ready to elevate your trade intelligence?</h2>
        <p class="text-sm sm:text-base text-slate-200 leading-relaxed">
          Gain immediate clarity on Cambodia's agricultural export landscape, price trends, and emerging market opportunities.
        </p>
        <div class="pt-2 flex flex-wrap items-center justify-center gap-4">
          <router-link 
            to="/plans" 
            class="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-100 text-sky-900 font-extrabold text-sm shadow-md transition-all cursor-pointer"
          >
            <span>View Pricing & Plans</span>
            <ArrowRightIcon class="w-4 h-4" />
          </router-link>
          <router-link 
            to="/login" 
            class="inline-flex items-center gap-2 px-5 py-3.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white font-bold text-sm transition-all cursor-pointer"
          >
            <span>Sign In to Account</span>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { 
  Sparkles as SparklesIcon,
  ArrowRight as ArrowRightIcon,
  LayoutDashboard as LayoutDashboardIcon,
  User as UserIcon,
  CheckCircle2 as CheckCircle2Icon,
  BarChart3 as BarChart3Icon,
  Bot as BotIcon,
  FileText as FileTextIcon,
  Layers as LayersIcon,
  Globe as GlobeIcon,
  TrendingUp as TrendingUpIcon
} from 'lucide-vue-next';
import { useAuthStore } from '../stores/authStore';
import { getTradeStatus, type PublicTradeStatus } from '../services/api';

const auth = useAuthStore();

const tradeStats = ref<PublicTradeStatus>({
  current_revision_id: null,
  destination_countries_count: 0,
  total_commodities_count: 0,
  total_records: 0,
  hs4_chapters_count: 0,
  reporting_period: ''
});

onMounted(async () => {
  try {
    const data = await getTradeStatus();
    if (data) {
      tradeStats.value = {
        current_revision_id: data.current_revision_id ?? null,
        destination_countries_count: typeof data.destination_countries_count === 'number' ? data.destination_countries_count : 0,
        total_commodities_count: typeof data.total_commodities_count === 'number' ? data.total_commodities_count : 0,
        total_records: typeof data.total_records === 'number' ? data.total_records : 0,
        hs4_chapters_count: typeof data.hs4_chapters_count === 'number' ? data.hs4_chapters_count : 0,
        reporting_period: data.reporting_period || ''
      };
    }
  } catch {
    // Retain default values
  }
});

const features = [
  { 
    title: 'Multi-Level Commodity Analytics', 
    text: 'Filter published reporting periods and compare agricultural products across HS4 and HS8 codes without losing macro trends.',
    icon: TrendingUpIcon
  },
  { 
    title: 'Global Export Destinations', 
    text: 'Analyze market shares across destination countries with interactive trade flow charts and volume comparisons.',
    icon: GlobeIcon
  },
  { 
    title: 'Dataset-Grounded AI Assistant', 
    text: 'Ask detailed questions about active published trade datasets and get instant, verifiable answers.',
    icon: BotIcon
  },
  { 
    title: 'Confidential Member Documents', 
    text: 'View in-browser PDF previews and download verified trade strategy presentations and research papers.',
    icon: FileTextIcon
  },
  { 
    title: 'Live MEF Currency Integration', 
    text: 'Real-time synchronization with Cambodia\'s Ministry of Economy and Finance official USD/KHR exchange rates.',
    icon: LayersIcon
  },
  { 
    title: 'Transparent Payment Audits', 
    text: 'Track payment verification status, active expiration dates, and generate official downloadable PDF receipts.',
    icon: CheckCircle2Icon
  }
];
</script>
