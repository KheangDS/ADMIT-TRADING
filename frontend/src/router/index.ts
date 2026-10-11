import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/authStore';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'Home', component: () => import('../pages/LandingPage.vue') },
    { path: '/login', component: () => import('../pages/LoginPage.vue') },
    { path: '/reset-password', component: () => import('../pages/ResetPasswordPage.vue') },
    // OAuth codes are handled only by the backend. This is an optional safe UI return route.
    { path: '/auth/callback', redirect: '/account' },
    { path: '/plans', component: () => import('../pages/PlansPage.vue') },
    { path: '/pricing', redirect: '/plans' },
    { path: '/account', component: () => import('../pages/AccountPage.vue'), meta: { authenticated: true } },
    { path: '/payments', component: () => import('../pages/PaymentsPage.vue'), meta: { authenticated: true } },
    { path: '/checkout/:planId', component: () => import('../pages/CheckoutPage.vue'), meta: { authenticated: true } },
    { path: '/documents', component: () => import('../pages/DocumentsPage.vue'), meta: { member: true } },
    { path: '/dashboard', name: 'Dashboard', component: () => import('../components/dashboard/MacroOverview.vue'), meta: { member: true, analytics: true } },
    { path: '/commodity/:hs8code', name: 'CommodityDetail', component: () => import('../pages/CommodityDetailPage.vue'), props: true, meta: { member: true, analytics: true } },
    { path: '/compare', name: 'CommodityCompare', component: () => import('../pages/CommodityComparePage.vue'), meta: { member: true, analytics: true } },
    { path: '/terms', name: 'Terms', component: () => import('../pages/TermsPage.vue') },
    { path: '/privacy', name: 'Privacy', component: () => import('../pages/PrivacyPage.vue') },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior(_to, _from, saved) { return saved || { top: 0 }; },
});
router.beforeEach(async to => {
  const auth = useAuthStore();
  await auth.bootstrap();
  if (to.path === '/reset-password') {
    const token = typeof to.query.token === 'string' ? to.query.token.trim() : '';
    if (!token || token.length < 10) {
      return { path: '/login' };
    }
  }
  if (to.path === '/login' && auth.user) {
    const returnTo =
      typeof to.query.return_to === 'string' &&
      to.query.return_to.startsWith('/') &&
      !to.query.return_to.startsWith('//') &&
      to.query.return_to !== '/login'
        ? to.query.return_to
        : (auth.canAccessMembers ? '/dashboard' : '/account');
    return { path: returnTo };
  }
  if ((to.meta.authenticated || to.meta.member) && !auth.user) {
    return { path: '/login', query: { return_to: to.fullPath || to.path } };
  }
  if (to.meta.member && !auth.canAccessMembers) return { path: '/account', query: { membership: 'required' } };
});
export default router;
