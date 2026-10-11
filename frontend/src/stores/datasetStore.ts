import { defineStore } from 'pinia';
import { ref, shallowRef, computed, onScopeDispose } from 'vue';
import type { DashboardPayload, ChatMessage } from '../types/dataset';
import { apiError, fetchCurrentAnalytics, isPublicationChanged, sendChatMessage } from '../services/api';
import { onPrivateReset, privateEpoch } from '../services/privateState';
import { useAuthStore } from './authStore';


function createInitialDashboardPayload(): DashboardPayload {
  return {
    session_id: 'preview',
    is_valid_trade_data: false,
    exchange_rate: 4000,
    begin_date: undefined,
    end_date: undefined,
    summary_kpis: [
      {
        label: 'Revenue (USD)',
        value: '$0.00',
        numeric_val: 0,
        unit: 'USD',
        description: 'Awaiting dataset ingestion'
      },
      {
        label: 'Total Transactions',
        value: '0 Records',
        numeric_val: 0,
        unit: 'Records',
        description: 'Total customs trade declarations recorded'
      },
      {
        label: 'Export Volume',
        value: '0.00 Tonnes',
        numeric_val: 0,
        unit: 'Tonnes',
        description: 'Total agricultural export weight'
      },
      {
        label: 'Destination Markets',
        value: '0 Countries',
        numeric_val: 0,
        unit: 'Markets',
        description: 'Active international trading partners'
      },
      {
        label: 'Total Commodities',
        value: '0 Commodities',
        numeric_val: 0,
        unit: 'Commodities',
        description: 'Active 8-digit tariff line products'
      }
    ],
    hs8_commodities: [],
    hs4_categories: [],
    market_share_table: [],
    level1_charts: [],
    hhi_risk_score: 0.0,
    is_high_risk: false,
    executive_strategy: [],
    commodity_details: {},
    commodity_list: []
  };
}

export const useDatasetStore = defineStore('dataset', () => {
  const auth = useAuthStore();
  const hasLoaded = ref(false);
  const dashboardData = shallowRef<DashboardPayload>(createInitialDashboardPayload());
  const exchangeRate = ref<number>(4000);

  const isLoading = ref<boolean>(false);
  const validationError = ref<string | null>(null);
  const publicationNotice = ref<string | null>(null);
  let analyticsRequest: Promise<void> | null = null;
  let scopeVersion = 0;
  const isChatOpen = ref<boolean>(false);
  const isChatProcessing = ref<boolean>(false);
  
  // 4-Pillar Interactive Slicer & Filter States
  const filterHsCode = ref<string>('ALL');
  const filterHsCodes = ref<string[]>([]); // Multi-select HS8 codes (empty array = All)
  const filterYear = ref<string>('ALL');
  const filterCountry = ref<string>('ALL');
  const filterMetric = ref<'USD' | 'TONNES'>('USD');
  const topNLimit = ref<number>(5);

  const selectedHsCodes = computed(() => filterHsCodes.value.length ? filterHsCodes.value : filterHsCode.value !== 'ALL' ? [filterHsCode.value] : []);
  const isSingleCommoditySelected = computed<boolean>(() => {
    if (filterHsCodes.value.length === 1) return true;
    if (filterHsCodes.value.length === 0 && filterHsCode.value !== 'ALL') return true;
    return false;
  });

  const selectedSingleHsCode = computed<string | null>(() => {
    if (filterHsCodes.value.length === 1) return filterHsCodes.value[0];
    if (filterHsCodes.value.length === 0 && filterHsCode.value !== 'ALL') return filterHsCode.value;
    return null;
  });

  const isFiltered = computed(() => {
    return (
      filterHsCodes.value.length > 0 ||
      filterHsCode.value !== 'ALL' ||
      filterYear.value !== 'ALL' ||
      filterCountry.value !== 'ALL' ||
      filterMetric.value !== 'USD'
    );
  });

  function resetAllFilters() {
    filterHsCode.value = 'ALL';
    filterHsCodes.value = [];
    filterYear.value = 'ALL';
    filterCountry.value = 'ALL';
    filterMetric.value = 'USD';
    topNLimit.value = 5;
  }

  const chatMessages = ref<ChatMessage[]>([]);
  function clearPrivateData() {
    scopeVersion++;
    analyticsRequest = null;
    publicationNotice.value = null;
    dashboardData.value = createInitialDashboardPayload();
    exchangeRate.value = 4000;
    chatMessages.value = [];
    isChatOpen.value = false;
    isChatProcessing.value = false;
    isLoading.value = false;
    hasLoaded.value = false;
    validationError.value = null;
    resetAllFilters();
  }
  onScopeDispose(onPrivateReset(clearPrivateData));

  function resetPublicationContext() {
    scopeVersion++;
    resetAllFilters();
    chatMessages.value = [];
    isChatProcessing.value = false;
  }

  // One request at a time; forced refreshes bypass only the loaded cache.
  function fetchMasterData(force = false): Promise<void> {
    if (!auth.canAccessMembers) return Promise.resolve();
    if (analyticsRequest) return analyticsRequest;
    if (hasLoaded.value && !force) return Promise.resolve();
    const epoch = privateEpoch;
    const previousId = dashboardData.value.publication?.id;
    const rate = hasLoaded.value ? exchangeRate.value : undefined;
    isLoading.value = true;
    validationError.value = null;
    const request = (async () => {
      try {
        const data = await fetchCurrentAnalytics(rate);
        if (epoch !== privateEpoch || !auth.canAccessMembers) return;
        if (previousId !== data.publication?.id) {
          resetPublicationContext();
          if (previousId) publicationNotice.value = 'Published analytics changed. Filters and chat were cleared. Please review the updated charts and ask your question again.';
        }
        if (data.is_valid_trade_data) {
          dashboardData.value = data;
          exchangeRate.value = data.exchange_rate;
        } else {
          dashboardData.value = createInitialDashboardPayload();
          resetPublicationContext();
          validationError.value = data.validation_message || 'No published trade data is available yet.';
        }
        hasLoaded.value = true;
      } catch (err) {
        if (epoch === privateEpoch) {
          validationError.value = apiError(err, 'Published analytics are unavailable. Please try again later.');
          // Failed repricing must not make chat/labels use a rate different from
          // the still-visible charts. Retain their successfully loaded rate.
          if (dashboardData.value.is_valid_trade_data) exchangeRate.value = dashboardData.value.exchange_rate;
        }
      } finally {
        if (epoch === privateEpoch) { isLoading.value = false; analyticsRequest = null; }
      }
    })();
    analyticsRequest = request;
    return request;
  }

  async function setExchangeRate(newRate: number) {
    if (!Number.isFinite(newRate) || newRate <= 0 || !auth.canAccessMembers || isLoading.value) return;
    exchangeRate.value = newRate;
    if (dashboardData.value.is_valid_trade_data) await fetchMasterData(true);
  }

  function toggleChat() {
    if (auth.canAccessMembers) isChatOpen.value = !isChatOpen.value;
  }

  async function postChatMessage(userQuestion: string) {
    if (!userQuestion.trim() || !auth.canAccessMembers || !dashboardData.value.is_valid_trade_data || isChatProcessing.value || isLoading.value) return;
    const epoch = privateEpoch;
    const version = scopeVersion;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: userQuestion,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    chatMessages.value.push(userMsg);
    isChatProcessing.value = true;

    try {
      const res = await sendChatMessage(dashboardData.value.session_id, userQuestion, exchangeRate.value, dashboardData.value.publication?.id);
      if (epoch !== privateEpoch || version !== scopeVersion || !auth.canAccessMembers) return;
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.answer,
        sql: res.sql_executed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      chatMessages.value.push(aiMsg);
    } catch (err) {
      if (epoch !== privateEpoch || version !== scopeVersion) return;
      if (isPublicationChanged(err)) {
        // A request started before the conflict may still contain the old publication.
        if (analyticsRequest) await analyticsRequest;
        if (epoch !== privateEpoch || !auth.canAccessMembers) return;
        resetPublicationContext();
        dashboardData.value = createInitialDashboardPayload();
        publicationNotice.value = 'Published analytics changed. Filters and chat were cleared. Please review the updated charts and ask your question again.';
        await fetchMasterData(true);
        return; // Never retry an old chart explanation against a new publication.
      }
      chatMessages.value.push({
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Sorry, I encountered an error processing your query against the dataset.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
    } finally {
      if (epoch === privateEpoch && version === scopeVersion) isChatProcessing.value = false;
    }
  }

  function askAboutChart(_chartTitle?: string, _chartMeaningText?: string) {
    if (auth.canAccessMembers) {
      isChatOpen.value = true;
    }
  }

  return {
    dashboardData,
    hasLoaded,
    clearPrivateData,
    exchangeRate,
    isLoading,
    validationError,
    publicationNotice,
    isChatOpen,
    isChatProcessing,
    chatMessages,
    filterHsCode,
    filterHsCodes,
    selectedHsCodes,
    isSingleCommoditySelected,
    selectedSingleHsCode,
    filterYear,
    filterCountry,
    filterMetric,
    topNLimit,
    isFiltered,
    resetAllFilters,
    fetchMasterData,
    setExchangeRate,
    toggleChat,
    postChatMessage,
    askAboutChart
  };
});

