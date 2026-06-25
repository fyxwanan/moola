<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import api from '../api';
import { useAuthStore } from '../stores/auth';
import * as LucideIcons from 'lucide-vue-next';
import { 
  TrendingUp, TrendingDown, Wallet, FolderKanban, Plus, HelpCircle, 
  ArrowRight, Calendar, PiggyBank, RefreshCw
} from 'lucide-vue-next';

const router = useRouter();
const authStore = useAuthStore();
const user = computed(() => authStore.user);

const records = ref([]);
const projects = ref([]);
const loading = ref(true);

const initDashboard = async () => {
  loading.value = true;
  try {
    const [recordsRes, projectsRes] = await Promise.all([
      api.get('/records'),
      api.get('/projects')
    ]);
    records.value = recordsRes.data;
    projects.value = projectsRes.data;
  } catch (err) {
    console.error('Error initializing dashboard data:', err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  initDashboard();
});

// Calculations for personal ledger
const personalExpense = computed(() => {
  return records.value
    .filter(r => r.type === 'expense')
    .reduce((sum, r) => sum + r.amount, 0);
});

const personalIncome = computed(() => {
  return records.value
    .filter(r => r.type === 'income')
    .reduce((sum, r) => sum + r.amount, 0);
});

const personalBalance = computed(() => personalIncome.value - personalExpense.value);

const formatToUTC8DateString = (dateInput) => {
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return '';
  const utc8Time = d.getTime() + 28800000;
  return new Date(utc8Time).toISOString().substring(0, 10);
};

// ShaYu Grouping: Group recent records by date with daily sub-totals
const groupedRecords = computed(() => {
  const groups = {};
  // Limit to latest 15 records for dashboard preview
  const sliceRecords = records.value.slice(0, 15);
  
  sliceRecords.forEach(r => {
    const dateStr = formatToUTC8DateString(r.record_date);
    if (!groups[dateStr]) {
      groups[dateStr] = {
        date: dateStr,
        expense: 0,
        income: 0,
        items: []
      };
    }
    if (r.type === 'expense') {
      groups[dateStr].expense += r.amount;
    } else {
      groups[dateStr].income += r.amount;
    }
    groups[dateStr].items.push(r);
  });
  
  return Object.values(groups).sort((a, b) => b.date.localeCompare(a.date));
});

// Chart statistics: Calculate expenses by category
const categoryStats = computed(() => {
  const expenseRecords = records.value.filter(r => r.type === 'expense');
  const totals = {};
  
  expenseRecords.forEach(r => {
    const catName = r.category?.name || '其他';
    const color = r.category?.color || '#6B7280';
    if (!totals[catName]) {
      totals[catName] = { name: catName, value: 0, color };
    }
    totals[catName].value += r.amount;
  });
  
  const statsArray = Object.values(totals).sort((a, b) => b.value - a.value);
  const totalVal = statsArray.reduce((sum, item) => sum + item.value, 0);
  
  return statsArray.map(item => ({
    ...item,
    percentage: totalVal > 0 ? Math.round((item.value / totalVal) * 100) : 0
  }));
});

// SVG Donut segments helper
const donutSegments = computed(() => {
  let accumulatedAngle = 0;
  const segments = [];
  const radius = 50;
  const cx = 60;
  const cy = 60;
  const circumference = 2 * Math.PI * radius;
  
  categoryStats.value.forEach(stat => {
    const angle = (stat.percentage / 100) * 360;
    const strokeDasharray = `${(stat.percentage / 100) * circumference} ${circumference}`;
    const strokeDashoffset = `${-accumulatedAngle / 360 * circumference}`;
    
    segments.push({
      ...stat,
      strokeDasharray,
      strokeDashoffset
    });
    accumulatedAngle += angle;
  });
  
  return segments;
});

const getIconComponent = (iconName) => {
  return LucideIcons[iconName] || HelpCircle;
};

const formatDayHeader = (dateStr) => {
  const todayStr = formatToUTC8DateString(new Date());
  const yesterday = new Date(new Date().getTime() - 86400000);
  const yesterdayStr = formatToUTC8DateString(yesterday);
  
  let label = '';
  if (dateStr === todayStr) {
    label = '今天';
  } else if (dateStr === yesterdayStr) {
    label = '昨天';
  } else {
    const parts = dateStr.split('-');
    const month = parseInt(parts[1], 10);
    const day = parseInt(parts[2], 10);
    label = `${month}月${day}日`;
  }
  
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
  const dateObj = new Date(`${dateStr}T12:00:00Z`);
  const dayName = weekdays[dateObj.getUTCDay()];
  
  return `${label} ${dayName}`;
};

const getYearMonthLabel = () => {
  const now = new Date();
  return `${now.getFullYear()}年 ${String(now.getMonth() + 1).padStart(2, '0')}月`;
};

const formatLargeAmount = (amount) => {
  const absVal = Math.abs(amount);
  const sign = amount < 0 ? '-' : '';
  if (absVal >= 100000000) { // 1亿
    return `${sign}¥${(absVal / 100000000).toFixed(2)}b`;
  } else if (absVal >= 100000) { // 10万
    return `${sign}¥${(absVal / 10000).toFixed(2)}w`;
  }
  return `${sign}¥${absVal.toFixed(2)}`;
};
</script>

<template>
  <div class="dashboard-container">
    <!-- ShaYu Top Banner Card -->
    <div class="shayu-header-banner">
      <div class="d-flex justify-between align-center mb-16">
        <div class="date-label">
          <span class="text-muted" style="color: rgba(34,34,34,0.6) !important; font-size: 13px; font-weight: 600;">当前账套</span>
          <h3 style="color: #222222; font-size: 20px;">{{ getYearMonthLabel() }}</h3>
        </div>
        
        <button class="refresh-badge-btn" @click="initDashboard" :disabled="loading">
          <RefreshCw :size="16" :class="{ 'anim-spin': loading }" />
        </button>
      </div>

      <div class="stats-banner-grid">
        <div class="stat-column">
          <div class="stat-lbl">本月总支出 (元)</div>
          <div class="stat-val font-heading">
            <el-tooltip
              v-if="personalExpense >= 100000"
              :content="'¥' + personalExpense.toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(personalExpense) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(personalExpense) }}</span>
          </div>
        </div>
        <div class="stat-column">
          <div class="stat-lbl">本月总收入 (元)</div>
          <div class="stat-val font-heading">
            <el-tooltip
              v-if="personalIncome >= 100000"
              :content="'¥' + personalIncome.toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(personalIncome) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(personalIncome) }}</span>
          </div>
        </div>
        <div class="stat-column">
          <div class="stat-lbl">结余</div>
          <div class="stat-val font-heading">
            <el-tooltip
              v-if="Math.abs(personalBalance) >= 100000"
              :content="(personalBalance < 0 ? '-' : '') + '¥' + Math.abs(personalBalance).toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(personalBalance) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(personalBalance) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading Screen -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在计算收支明细...</p>
    </div>

    <div v-else class="dashboard-grid">
      <!-- Main Content Left Column -->
      <div class="left-column">
        <!-- Charts Card -->
        <div class="glass-card mb-24">
          <h3 class="card-title mb-24">支出分类分析</h3>
          
          <div v-if="categoryStats.length === 0" class="empty-chart-text text-center text-muted">
            本月暂无支出记录，添加一笔支出后将在这里展示分析。
          </div>

          <div v-else class="chart-layout">
            <!-- Donut SVG -->
            <div class="donut-chart-box">
              <svg width="180" height="180" viewBox="0 0 120 120" class="donut-svg">
                <circle cx="60" cy="60" r="50" fill="transparent" stroke="var(--gray-200)" stroke-width="12" />
                <circle 
                  v-for="(seg, idx) in donutSegments" 
                  :key="idx"
                  cx="60" 
                  cy="60" 
                  r="50" 
                  fill="transparent" 
                  :stroke="seg.color" 
                  stroke-width="12" 
                  :stroke-dasharray="seg.strokeDasharray"
                  :stroke-dashoffset="seg.strokeDashoffset"
                  transform="rotate(-90 60 60)"
                  class="donut-segment"
                />
              </svg>
              <div class="donut-center-label">
                <div class="val">
                  <el-tooltip
                    v-if="personalExpense >= 100000"
                    :content="'¥' + personalExpense.toFixed(2)"
                    placement="top"
                    effect="dark"
                  >
                    <span>{{ formatLargeAmount(personalExpense) }}</span>
                  </el-tooltip>
                  <span v-else>{{ formatLargeAmount(personalExpense) }}</span>
                </div>
                <div class="lbl text-muted">本月支出</div>
              </div>
            </div>

            <!-- Categories Breakdown -->
            <div class="breakdown-list">
              <div v-for="stat in categoryStats.slice(0, 4)" :key="stat.name" class="breakdown-item mb-16">
                <div class="d-flex justify-between align-center mb-8">
                  <div class="d-flex align-center gap-8">
                    <span class="color-dot" :style="{ backgroundColor: stat.color }"></span>
                    <span class="name font-semibold">{{ stat.name }}</span>
                    <span class="percent text-muted">{{ stat.percentage }}%</span>
                  </div>
                  <div class="val font-semibold">
                    <el-tooltip
                      v-if="stat.value >= 100000"
                      :content="'¥' + stat.value.toFixed(2)"
                      placement="top"
                      effect="dark"
                    >
                      <span>{{ formatLargeAmount(stat.value) }}</span>
                    </el-tooltip>
                    <span v-else>{{ formatLargeAmount(stat.value) }}</span>
                  </div>
                </div>
                <div class="progress-track">
                  <div class="progress-bar" :style="{ width: `${stat.percentage}%`, backgroundColor: stat.color }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ShaYu Style Grouped Transactions List -->
        <div class="glass-card">
          <div class="d-flex justify-between align-center mb-24">
            <h3 class="card-title">最近收支明细</h3>
            <router-link to="/ledger" class="view-all-link d-flex align-center gap-8">
              <span>查看个人账本</span>
              <ArrowRight :size="16" />
            </router-link>
          </div>

          <div v-if="groupedRecords.length === 0" class="empty-list-text text-muted text-center">
            本月暂无记账记录。点击左侧“个人记账”来记录你的第一笔账单吧！
          </div>

          <div v-else class="shayu-daily-groups">
            <!-- Group loop -->
            <div v-for="group in groupedRecords" :key="group.date" class="shayu-date-group mb-16">
              <!-- Group Date Header -->
              <div class="shayu-group-header d-flex justify-between align-center">
                <span class="group-date">{{ formatDayHeader(group.date) }}</span>
                <div class="group-summary text-muted">
                  <span v-if="group.income > 0">收入: {{ group.income.toFixed(1) }}</span>
                  <span v-if="group.expense > 0" class="ml-8">支出: {{ group.expense.toFixed(1) }}</span>
                </div>
              </div>
              
              <!-- Items inside group -->
              <div class="group-items-box">
                <div 
                  v-for="rec in group.items" 
                  :key="rec.id" 
                  class="recent-row d-flex justify-between align-center"
                >
                  <div class="d-flex align-center gap-16">
                    <div 
                      class="cat-icon-box" 
                      :style="{ backgroundColor: `${rec.category?.color || '#6366F1'}12`, color: rec.category?.color || '#6366f1' }"
                    >
                      <component :is="getIconComponent(rec.category?.icon || 'HelpCircle')" :size="18" />
                    </div>
                    <div>
                      <div class="name font-semibold">{{ rec.category?.name || '未知' }}</div>
                      <div class="date-note text-muted">
                        <span class="note-truncate">{{ rec.note || '无备注' }}</span>
                      </div>
                    </div>
                  </div>
                  <span class="amount font-semibold" :class="rec.type === 'expense' ? 'text-danger' : 'text-success'">
                    <el-tooltip
                      v-if="rec.amount >= 100000"
                      :content="(rec.type === 'expense' ? '-' : '+') + '¥' + rec.amount.toFixed(2)"
                      placement="top"
                      effect="dark"
                    >
                      <span>{{ rec.type === 'expense' ? '-' : '+' }}{{ formatLargeAmount(rec.amount).slice(1) }}</span>
                    </el-tooltip>
                    <span v-else>{{ rec.type === 'expense' ? '-' : '+' }}{{ formatLargeAmount(rec.amount).slice(1) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Projects Quick View -->
      <div class="right-column">
        <div class="glass-card projects-list-card">
          <div class="d-flex justify-between align-center mb-24">
            <h3 class="card-title d-flex align-center gap-8">
              <FolderKanban :size="18" class="text-primary-hover" />
              <span>协同共享账本</span>
            </h3>
            <router-link to="/projects" class="create-proj-icon-btn" title="协同账目">
              <Plus :size="16" />
            </router-link>
          </div>

          <div v-if="projects.length === 0" class="empty-projects text-center text-muted">
            您还未创建或加入任何协同账目项目。
          </div>

          <div v-else class="project-mini-list">
            <div 
              v-for="project in projects.slice(0, 4)" 
              :key="project.id" 
              class="project-mini-row interactive d-flex justify-between align-center"
              @click="router.push(`/projects/${project.id}`)"
            >
              <div>
                <div class="proj-name font-semibold">{{ project.name }}</div>
                <div class="proj-members text-muted">{{ project.members?.length || 0 }} 名成员</div>
              </div>
              <ArrowRight :size="16" class="arrow" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container {
  max-width: 1100px;
  margin: 0 auto;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(0, 0, 0, 0.05);
  border-top-color: var(--primary-hover);
  border-radius: 50%;
  animation: spin 1s infinite linear;
  margin-bottom: 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.anim-spin {
  animation: spin 1s infinite linear;
}

.refresh-badge-btn {
  background: rgba(255, 255, 255, 0.25);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--primary-text);
  transition: var(--transition-fast);
}

.refresh-badge-btn:hover {
  background: rgba(255, 255, 255, 0.4);
}

/* Stats Row inside banner */
.stats-banner-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-column .stat-lbl {
  font-size: 12px;
  color: rgba(34, 34, 34, 0.55);
  font-weight: 600;
  margin-bottom: 6px;
}

.stat-column .stat-val {
  font-size: 24px;
  font-weight: 800;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2.5fr 1fr;
  gap: 24px;
}

/* Donut & Stats */
.chart-layout {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 24px;
  align-items: center;
}

.donut-chart-box {
  position: relative;
  width: 180px;
  height: 180px;
  margin: 0 auto;
}

.donut-svg {
  transform: rotate(0deg);
}

.donut-segment {
  transition: stroke-dashoffset 0.5s ease;
}

.donut-center-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}
.donut-center-label .val {
  font-size: 18px;
  font-weight: 800;
  font-family: var(--font-heading);
}
.donut-center-label .lbl {
  font-size: 10px;
  margin-top: 2px;
}

.breakdown-list {
  display: flex;
  flex-direction: column;
}

.color-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.breakdown-item .name {
  font-size: 14px;
}

.breakdown-item .percent {
  font-size: 11px;
}

.breakdown-item .val {
  font-size: 14px;
  font-family: var(--font-heading);
}

.progress-track {
  background: var(--gray-100);
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 3px;
}

/* ShaYu Style Lists grouping */
.shayu-group-header {
  background: var(--gray-100);
  padding: 8px 14px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-weight: 700;
  border-left: 3px solid var(--primary);
  margin-bottom: 8px;
}

.group-date {
  color: var(--color-text-dark);
}

.group-summary {
  font-family: var(--font-heading);
}

.ml-8 {
  margin-left: 8px;
}

.group-items-box {
  padding: 0 4px;
}

.recent-row {
  padding: 12px 8px;
  border-bottom: 1px solid var(--panel-border);
}

.recent-row:last-child {
  border-bottom: none;
}

.cat-icon-box {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.recent-row .name {
  font-size: 14px;
}

.date-note {
  font-size: 11px;
  margin-top: 2px;
}

.note-truncate {
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-row .amount {
  font-size: 16px;
  font-family: var(--font-heading);
}

.view-all-link {
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 13px;
  font-weight: 700;
}
.view-all-link:hover {
  color: var(--primary-hover);
}

/* Projects Sidebar */
.create-proj-icon-btn {
  background: rgba(255, 210, 30, 0.15);
  border: none;
  color: var(--primary-text);
  width: 28px;
  height: 28px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--transition-fast);
  text-decoration: none;
}
.create-proj-icon-btn:hover {
  background: var(--primary);
}

.project-mini-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-mini-row {
  padding: 14px;
  background: #ffffff;
  border: 1px solid var(--panel-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: var(--transition-fast);
}

.project-mini-row .proj-name {
  font-size: 14px;
}
.project-mini-row .proj-members {
  font-size: 11px;
  margin-top: 2px;
}

.project-mini-row .arrow {
  color: var(--color-text-muted);
  transition: transform var(--transition-fast);
}

.project-mini-row:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}

.project-mini-row:hover .arrow {
  transform: translateX(3px);
  color: var(--primary-hover);
}

.empty-chart-text, .empty-list-text, .empty-projects {
  padding: 30px 0;
  font-size: 13px;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .stats-banner-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  .chart-layout {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}
</style>
