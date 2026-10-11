import { createRouter, createWebHistory } from 'vue-router';
import { bootstrap } from './api';
import { session } from './session';
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/imports' },
    { path: '/login', component: () => import('./pages/LoginPage.vue') },
    { path: '/imports', component: () => import('./pages/ImportsPage.vue'), meta: { admin: true } },
    {
      path: '/dictionary',
      component: () => import('./pages/DictionaryPage.vue'),
      meta: { admin: true },
    },
    {
      path: '/registry',
      redirect: '/dictionary',
    },
    {
      path: '/publication',
      redirect: '/imports',
    },
    {
      path: '/overview',
      redirect: '/imports',
    },
    {
      path: '/documents',
      component: () => import('./pages/DocumentsPage.vue'),
      meta: { admin: true },
    },
    { path: '/plans', component: () => import('./pages/PlansPage.vue'), meta: { admin: true } },
    {
      path: '/payments',
      component: () => import('./pages/PaymentsPage.vue'),
      meta: { admin: true },
    },
    { path: '/users', component: () => import('./pages/UsersPage.vue'), meta: { admin: true } },
    {
      path: '/operations',
      component: () => import('./pages/OperationsPage.vue'),
      meta: { admin: true, superadmin: true },
    },
    {
      path: '/audit',
      redirect: '/operations',
    },
    { path: '/:pathMatch(.*)*', component: () => import('./pages/NotFoundPage.vue') },
  ],
});
router.beforeEach(async (to) => {
  if (!session.ready) await bootstrap();
  const isAdmin = (session.user?.role === 'admin' || session.user?.role === 'superadmin') && !session.denied;
  if (to.path === '/login' && isAdmin) {
    const returnTo =
      typeof to.query.return_to === 'string' &&
      to.query.return_to.startsWith('/') &&
      !to.query.return_to.startsWith('//') &&
      to.query.return_to !== '/login'
        ? to.query.return_to
        : '/imports';
    return { path: returnTo };
  }
  if (to.meta.admin && !isAdmin) {
    return { path: '/login', query: { return_to: to.fullPath || to.path } };
  }
  if (to.meta.superadmin && session.user?.role !== 'superadmin') {
    return { path: '/imports' };
  }
});
