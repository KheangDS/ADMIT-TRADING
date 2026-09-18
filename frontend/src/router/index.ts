import { createRouter, createWebHistory } from 'vue-router';
import MacroOverview from '../components/dashboard/MacroOverview.vue';
import CommodityDetailPage from '../pages/CommodityDetailPage.vue';
import CommodityComparePage from '../pages/CommodityComparePage.vue';

const routes = [
  {
    path: '/',
    name: 'Home',
    component: MacroOverview,
  },
  {
    path: '/commodity/:hs8code',
    name: 'CommodityDetail',
    component: CommodityDetailPage,
    props: true,
  },
  {
    path: '/compare',
    name: 'CommodityCompare',
    component: CommodityComparePage,
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(_to, _from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    return { top: 0 };
  },
});

export default router;

