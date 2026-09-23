import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { DashboardPayload, ChatMessage } from '../types/dataset';
import { fetchCurrentAnalytics, uploadDataset, recalculateAnalytics, sendChatMessage } from '../services/api';


function createInitialDashboardPayload(): DashboardPayload {
  return {
    session_id: 'preview',
    is_valid_trade_data: false,
    exchange_rate: 4000,
    begin_date: undefined,
    end_date: undefined,
    summary_kpis: [
      {
        label: 'Total Value ($)',
        value: '$0.00',
        numeric_val: 0,
        unit: 'USD',
        description: 'Awaiting dataset ingestion'
      },
      {
        label: 'Total Value (KHR)',
        value: '៛0.00 KHR',
        numeric_val: 0,
        unit: 'KHR',
        description: 'Raw trade currency total'
      },
      {
        label: 'Total Volume',
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
  const dashboardData = ref<DashboardPayload>(createInitialDashboardPayload());
  const exchangeRate = ref<number>(4000);
  const isLoading = ref<boolean>(false);
  const validationError = ref<string | null>(null);
  const isChatOpen = ref<boolean>(false);
  const isChatProcessing = ref<boolean>(false);
  
  // 4-Pillar Interactive Slicer & Filter States
  const filterHsCode = ref<string>('ALL');
  const filterHsCodes = ref<string[]>([]); // Multi-select HS8 codes (empty array = All)
  const filterYear = ref<string>('ALL');
  const filterCountry = ref<string>('ALL');
  const filterMetric = ref<'USD' | 'TONNES'>('USD');
  const topNLimit = ref<number>(5);

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

  const chatMessages = ref<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'ai',
      text: 'Hello! 👋 I am your AI Trade Assistant. Ask me any question grounded strictly in your uploaded trade dataset!',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);

  async function fetchMasterData() {
    isLoading.value = true;
    validationError.value = null;
    try {
      const data = await fetchCurrentAnalytics();
      if (data && data.is_valid_trade_data) {
        dashboardData.value = data;
        if (data.exchange_rate) {
          exchangeRate.value = data.exchange_rate;
        }
      } else {
        dashboardData.value = createInitialDashboardPayload();
      }
    } catch (err: any) {
      console.warn('Could not auto-fetch current dataset (using preview mode):', err);
    } finally {
      isLoading.value = false;
    }
  }

  async function handleFileUpload(file: File) {
    isLoading.value = true;
    validationError.value = null;

    try {
      const data = await uploadDataset(file, exchangeRate.value);
      if (!data.is_valid_trade_data) {
        validationError.value = data.validation_message || 'Uploaded file format is invalid for trade analytics.';
        dashboardData.value = createInitialDashboardPayload();
      } else {
        dashboardData.value = data;
      }
    } catch (err: any) {
      validationError.value = err.response?.data?.detail || 'Failed to upload and process dataset. Please try again.';
    } finally {
      isLoading.value = false;
    }
  }

  async function setExchangeRate(newRate: number) {
    if (newRate <= 0) return;
    exchangeRate.value = newRate;
    
    if (dashboardData.value && dashboardData.value.session_id) {
      isLoading.value = true;
      try {
        const updated = await recalculateAnalytics(dashboardData.value.session_id, newRate);
        dashboardData.value = updated;
      } catch (err) {
        console.error('Failed to recalculate metrics:', err);
      } finally {
        isLoading.value = false;
      }
    }
  }

  function toggleChat() {
    isChatOpen.value = !isChatOpen.value;
  }

  async function postChatMessage(userQuestion: string) {
    if (!userQuestion.trim() || !dashboardData.value || isChatProcessing.value) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: userQuestion,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    chatMessages.value.push(userMsg);
    isChatProcessing.value = true;

    try {
      const res = await sendChatMessage(dashboardData.value.session_id, userQuestion, exchangeRate.value);
      const aiMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: res.answer,
        sql: res.sql_executed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      chatMessages.value.push(aiMsg);
    } catch (err) {
      chatMessages.value.push({
        id: (Date.now() + 1).toString(),
        sender: 'ai',
        text: 'Sorry, I encountered an error processing your query against the dataset.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      });
    } finally {
      isChatProcessing.value = false;
    }
  }

  function askAboutChart(chartTitle: string, chartMeaningText?: string) {
    isChatOpen.value = true;
    const contextInfo = chartMeaningText ? ` (Visual Context: ${chartMeaningText})` : '';
    const promptText = `As a Senior Data Analyst, please explain the key data insights and analytical breakdown for the chart "${chartTitle}"${contextInfo} based strictly on the trade dataset.`;
    postChatMessage(promptText);
  }

  return {
    dashboardData,
    exchangeRate,
    isLoading,
    validationError,
    isChatOpen,
    isChatProcessing,
    chatMessages,
    filterHsCode,
    filterHsCodes,
    isSingleCommoditySelected,
    selectedSingleHsCode,
    filterYear,
    filterCountry,
    filterMetric,
    topNLimit,
    isFiltered,
    resetAllFilters,
    fetchMasterData,
    handleFileUpload,
    setExchangeRate,
    toggleChat,
    postChatMessage,
    askAboutChart
  };
});

