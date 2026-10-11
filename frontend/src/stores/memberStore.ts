import { ref } from 'vue';
import { defineStore } from 'pinia';
import type { Payment, Receipt, MemberDocument } from '../types/membership';
import { getPayments, getReceipts, getDocuments } from '../services/api';
import { onPrivateReset, privateEpoch } from '../services/privateState';
export const useMemberStore = defineStore('member', () => {
  const payments = ref<Payment[]>([]);
  const receipts = ref<Receipt[]>([]);
  const documents = ref<MemberDocument[]>([]);
  onPrivateReset(() => { payments.value = []; receipts.value = []; documents.value = []; });
  async function loadPayments() {
    const epoch = privateEpoch;
    const [nextPayments, nextReceipts] = await Promise.all([getPayments(), getReceipts()]);
    if (epoch === privateEpoch) { payments.value = nextPayments; receipts.value = nextReceipts; }
  }
  async function loadDocuments() {
    const epoch = privateEpoch;
    const next = await getDocuments();
    if (epoch === privateEpoch) documents.value = next;
  }
  function putPayment(payment: Payment) {
    payments.value = [payment, ...payments.value.filter(item => item.id !== payment.id)];
  }
  return { payments, receipts, documents, loadPayments, loadDocuments, putPayment };
});
