<script setup>
import { ref, onMounted, computed } from 'vue';
import api from '../api';
import ConfirmModal from '../components/ConfirmModal.vue';
import ImagePreviewGallery from '../components/ImagePreviewGallery.vue';
import * as LucideIcons from 'lucide-vue-next';
import {
  Plus, Trash2, Edit, Calendar, Filter,
  TrendingUp, TrendingDown, DollarSign, HelpCircle, Delete,
  X, ChevronLeft, ChevronRight
} from 'lucide-vue-next';

const records = ref([]);
const categories = ref([]);
const loading = ref(true);

// Reusable Confirm Modal State
const confirmModal = ref({
  show: false,
  title: '提示',
  message: '',
  type: 'confirm', // 'confirm', 'alert', 'danger'
  onConfirm: null,
  onCancel: null
});

const triggerConfirm = (options) => {
  confirmModal.value = {
    show: true,
    title: options.title || '提示',
    message: options.message || '',
    type: options.type || 'confirm',
    onConfirm: () => {
      confirmModal.value.show = false;
      if (options.onConfirm) options.onConfirm();
    },
    onCancel: () => {
      confirmModal.value.show = false;
      if (options.onCancel) options.onCancel();
    }
  };
};

const triggerAlert = (message, title = '提示', callback = null) => {
  confirmModal.value = {
    show: true,
    title,
    message,
    type: 'alert',
    onConfirm: () => {
      confirmModal.value.show = false;
      if (callback) callback();
    },
    onCancel: () => {
      confirmModal.value.show = false;
      if (callback) callback();
    }
  };
};

// Calculations
const totalExpense = computed(() => {
  return records.value
    .filter(r => r.type === 'expense')
    .reduce((sum, r) => sum + r.amount, 0);
});

const totalIncome = computed(() => {
  return records.value
    .filter(r => r.type === 'income')
    .reduce((sum, r) => sum + r.amount, 0);
});

const balance = computed(() => totalIncome.value - totalExpense.value);

const formatToUTC8DateString = (dateInput) => {
  const d = new Date(dateInput);
  if (isNaN(d.getTime())) return '';
  const utc8Time = d.getTime() + 28800000;
  return new Date(utc8Time).toISOString().substring(0, 10);
};

// ShaYu Grouping: Group records by date with daily sub-totals
const groupedRecords = computed(() => {
  const groups = {};
  records.value.forEach(r => {
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

// Query Filters
const filterType = ref('');
const filterCategory = ref('');
const filterStartDate = ref('');
const filterEndDate = ref('');

// Modals
const showAddRecordModal = ref(false);
const showEditRecordModal = ref(false);

const recordForm = ref({
  id: '',
  amount: '',
  type: 'expense',
  category_id: '',
  record_date: formatToUTC8DateString(new Date()),
  note: '',
  images: []
});

const recordError = ref('');
const submittingRecord = ref(false);

const fetchRecords = async () => {
  try {
    let url = '/records';
    const params = [];
    if (filterType.value) params.push(`type=${filterType.value}`);
    if (filterCategory.value) params.push(`category_id=${filterCategory.value}`);
    if (filterStartDate.value) params.push(`start_date=${new Date(filterStartDate.value + 'T00:00:00+08:00').toISOString()}`);
    if (filterEndDate.value) params.push(`end_date=${new Date(filterEndDate.value + 'T23:59:59.999+08:00').toISOString()}`);

    if (params.length > 0) {
      url += '?' + params.join('&');
    }

    const response = await api.get(url);
    records.value = response.data;
  } catch (err) {
    console.error('Error fetching records:', err);
  }
};

const fetchCategories = async () => {
  try {
    const response = await api.get('/categories');
    categories.value = response.data;
  } catch (err) {
    console.error('Error fetching categories:', err);
  }
};

const initData = async () => {
  loading.value = true;
  await fetchCategories();
  await fetchRecords();

  if (categories.value.length > 0) {
    recordForm.value.category_id = expenseCategories.value[0]?.id || categories.value[0]?.id;
  }
  loading.value = false;
};

onMounted(() => {
  initData();
});

const expenseCategories = computed(() => categories.value.filter(c => c.type === 'expense'));
const incomeCategories = computed(() => categories.value.filter(c => c.type === 'income'));

const handleFilterChange = () => {
  fetchRecords();
};

const clearFilters = () => {
  filterType.value = '';
  filterCategory.value = '';
  filterStartDate.value = '';
  filterEndDate.value = '';
  fetchRecords();
};

// ShaYu custom keyboard layout input handler
const handleKeyboardPress = (key) => {
  let val = recordForm.value.amount.toString();
  if (key === 'C') {
    val = '';
  } else if (key === '⌫') {
    val = val.slice(0, -1);
  } else if (key === '.') {
    if (!val.includes('.')) {
      val = val === '' ? '0.' : val + '.';
    }
  } else {
    // Digits
    if (val === '0') {
      val = key;
    } else {
      // Limit decimals to 2 places
      const decIndex = val.indexOf('.');
      if (decIndex === -1 || val.length - decIndex <= 2) {
        val += key;
      }
    }
  }
  recordForm.value.amount = val;
};

// Image Uploading & Previewing logic
const uploadingImagesCount = ref(0);

const handleFileUpload = async (event) => {
  const files = event.target.files;
  if (!files || files.length === 0) return;

  const currentImages = recordForm.value.images || [];
  const maxSlots = 6 - currentImages.length;
  const filesToUpload = Array.from(files).slice(0, maxSlots);

  uploadingImagesCount.value = filesToUpload.length;

  for (const file of filesToUpload) {
    const formData = new FormData();
    formData.append('file', file);
    try {
      const res = await api.post('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      if (res.data && res.data.url) {
        if (!recordForm.value.images) {
          recordForm.value.images = [];
        }
        recordForm.value.images.push(res.data.url);
      }
    } catch (err) {
      console.error('Failed to upload file:', err);
    } finally {
      uploadingImagesCount.value = Math.max(0, uploadingImagesCount.value - 1);
    }
  }
  event.target.value = '';
};

const removeFormImage = (index) => {
  recordForm.value.images.splice(index, 1);
};

const getFullImageUrl = (url) => {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://')) return url;
  const baseUrl = api.defaults.baseURL;
  const rootUrl = baseUrl.endsWith('/api') ? baseUrl.slice(0, -4) : baseUrl;
  return `${rootUrl}${url}`;
};

const previewGallery = ref({
  show: false,
  images: [],
  currentIndex: 0
});

const handlePreviewImage = (imagesList, index) => {
  previewGallery.value = {
    show: true,
    images: imagesList.map(img => getFullImageUrl(img)),
    currentIndex: index
  };
};

// Add record
const openAddRecord = () => {
  recordForm.value = {
    id: '',
    amount: '',
    type: 'expense',
    category_id: expenseCategories.value[0]?.id || categories.value[0]?.id,
    record_date: formatToUTC8DateString(new Date()),
    note: '',
    images: []
  };
  recordError.value = '';
  showAddRecordModal.value = true;
};

const handleCreateRecord = async () => {
  const amt = parseFloat(recordForm.value.amount);
  if (isNaN(amt) || amt <= 0) {
    recordError.value = '请输入有效金额';
    return;
  }
  if (!recordForm.value.category_id) {
    recordError.value = '请选择分类';
    return;
  }

  submittingRecord.value = true;
  recordError.value = '';

  try {
    const recordDateISO = (() => {
      const todayStr = formatToUTC8DateString(new Date());
      if (recordForm.value.record_date === todayStr) {
        return new Date().toISOString();
      } else {
        return new Date(recordForm.value.record_date + 'T12:00:00+08:00').toISOString();
      }
    })();

    await api.post('/records', {
      amount: amt,
      type: recordForm.value.type,
      category_id: recordForm.value.category_id,
      record_date: recordDateISO,
      note: recordForm.value.note,
      images: recordForm.value.images || []
    });

    showAddRecordModal.value = false;
    await fetchRecords();
  } catch (err) {
    recordError.value = err.response?.data?.detail || '保存账单失败';
  } finally {
    submittingRecord.value = false;
  }
};

// Edit record
const openEditRecord = (rec) => {
  recordForm.value = {
    id: rec.id,
    amount: rec.amount.toString(),
    type: rec.type,
    category_id: rec.category_id,
    record_date: formatToUTC8DateString(rec.record_date),
    note: rec.note || '',
    images: rec.images ? [...rec.images] : []
  };
  recordError.value = '';
  showEditRecordModal.value = true;
};

const handleUpdateRecord = async () => {
  const amt = parseFloat(recordForm.value.amount);
  if (isNaN(amt) || amt <= 0) {
    recordError.value = '请输入有效金额';
    return;
  }

  submittingRecord.value = true;
  recordError.value = '';

  try {
    const recordDateISO = (() => {
      const originalRecord = records.value.find(r => r.id === recordForm.value.id);
      if (originalRecord && formatToUTC8DateString(originalRecord.record_date) === recordForm.value.record_date) {
        return new Date(originalRecord.record_date).toISOString();
      }
      return new Date(recordForm.value.record_date + 'T12:00:00+08:00').toISOString();
    })();

    await api.put(`/records/${recordForm.value.id}`, {
      amount: amt,
      type: recordForm.value.type,
      category_id: recordForm.value.category_id,
      record_date: recordDateISO,
      note: recordForm.value.note,
      images: recordForm.value.images || []
    });

    showEditRecordModal.value = false;
    await fetchRecords();
  } catch (err) {
    recordError.value = err.response?.data?.detail || '修改账单失败';
  } finally {
    submittingRecord.value = false;
  }
};

const handleDeleteRecord = (id) => {
  triggerConfirm({
    title: '确认删除',
    message: '确定要删除这笔个人账单吗？',
    type: 'danger',
    onConfirm: async () => {
      try {
        await api.delete(`/records/${id}`);
        await fetchRecords();
      } catch (err) {
        triggerAlert(err.response?.data?.detail || '删除账单失败', '错误');
      }
    }
  });
};

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

// Mobile Query Filters Drawer
const showMobileFilters = ref(false);
const tempFilterType = ref('');
const tempFilterCategory = ref('');
const tempFilterStartDate = ref('');
const tempFilterEndDate = ref('');

const openMobileFilters = () => {
  tempFilterType.value = filterType.value;
  tempFilterCategory.value = filterCategory.value;
  tempFilterStartDate.value = filterStartDate.value;
  tempFilterEndDate.value = filterEndDate.value;
  showMobileFilters.value = true;
};

const handleMobileConfirm = () => {
  filterType.value = tempFilterType.value;
  filterCategory.value = tempFilterCategory.value;
  filterStartDate.value = tempFilterStartDate.value;
  filterEndDate.value = tempFilterEndDate.value;
  showMobileFilters.value = false;
  fetchRecords();
};

const handleMobileClear = () => {
  tempFilterType.value = '';
  tempFilterCategory.value = '';
  tempFilterStartDate.value = '';
  tempFilterEndDate.value = '';

  filterType.value = '';
  filterCategory.value = '';
  filterStartDate.value = '';
  filterEndDate.value = '';
  showMobileFilters.value = false;
  fetchRecords();
};

const hasActiveFilters = computed(() => {
  return !!(filterType.value || filterCategory.value || filterStartDate.value || filterEndDate.value);
});
</script>

<template>
  <div class="ledger-view-container">
    <!-- Top Warm Summary Header -->
    <div class="shayu-header-banner">
      <div class="d-flex justify-between align-center mb-16">
        <div>
          <span style="color: rgba(34,34,34,0.6) !important; font-size: 13px; font-weight: 600;">账本结余</span>
          <h3 style="color: #222222; font-size: 26px; font-family: var(--font-heading);">
            <el-tooltip
              v-if="Math.abs(balance) >= 100000"
              :content="(balance < 0 ? '-' : '') + '¥' + Math.abs(balance).toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(balance) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(balance) }}</span>
          </h3>
        </div>
        <button class="btn btn-primary" style="background: #222; color: #fff; box-shadow: none;" @click="openAddRecord">
          <Plus :size="16" />
          <span>记一笔</span>
        </button>
      </div>

      <div class="stats-banner-grid">
        <div class="stat-column">
          <div class="stat-lbl">总支出 (元)</div>
          <div class="stat-val font-heading" style="font-size: 20px;">
            <el-tooltip
              v-if="totalExpense >= 100000"
              :content="'¥' + totalExpense.toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(totalExpense) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(totalExpense) }}</span>
          </div>
        </div>
        <div class="stat-column">
          <div class="stat-lbl">总收入 (元)</div>
          <div class="stat-val font-heading" style="font-size: 20px;">
            <el-tooltip
              v-if="totalIncome >= 100000"
              :content="'¥' + totalIncome.toFixed(2)"
              placement="top"
              effect="dark"
            >
              <span>{{ formatLargeAmount(totalIncome) }}</span>
            </el-tooltip>
            <span v-else>{{ formatLargeAmount(totalIncome) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在加载账单流水...</p>
    </div>

    <div v-else class="ledger-content">
      <!-- Filters Panel -->
      <div class="glass-card filter-card mb-24">
        <div class="filter-header d-flex justify-between align-center mb-16">
          <h3 class="filter-title d-flex align-center gap-8">
            <Filter :size="16" class="text-primary-hover" />
            <span>账单筛选</span>
          </h3>
          <button class="clear-filters-btn text-muted" @click="clearFilters">重置</button>
        </div>

        <div class="filters-grid">
          <div class="filter-group">
            <label>账单类型</label>
            <el-select v-model="filterType" placeholder="全部" @change="handleFilterChange" style="width: 100%;">
              <el-option label="全部" value="" />
              <el-option label="支出" value="expense" />
              <el-option label="收入" value="income" />
            </el-select>
          </div>

          <div class="filter-group">
            <label>账单类别</label>
            <el-select v-model="filterCategory" placeholder="全部" @change="handleFilterChange" style="width: 100%;">
              <el-option label="全部" value="" />
              <el-option v-for="cat in categories" :key="cat.id"
                :label="`${cat.name} (${cat.type === 'expense' ? '支' : '收'})`" :value="cat.id" />
            </el-select>
          </div>

          <div class="filter-group">
            <label>起始日期</label>
            <el-date-picker v-model="filterStartDate" type="date" value-format="YYYY-MM-DD" placeholder="选择起始日期"
              @change="handleFilterChange" style="width: 100%;" />
          </div>

          <div class="filter-group">
            <label>结束日期</label>
            <el-date-picker v-model="filterEndDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期"
              @change="handleFilterChange" style="width: 100%;" />
          </div>
        </div>
      </div>

      <!-- Records Log Card -->
      <div class="glass-card records-card">
        <div class="records-header d-flex justify-between align-center mb-24">
          <div class="d-flex align-center gap-8">
            <h3 style="margin: 0; font-size: 16px; font-weight: 700;">个人流水账单</h3>
            <!-- Mobile Filter Icon Button -->
            <button class="mobile-filter-trigger-btn" :class="{ active: hasActiveFilters }" @click="openMobileFilters"
              title="账单筛选">
              <Filter :size="18" />
            </button>
          </div>
        </div>
        <div v-if="groupedRecords.length === 0" class="empty-records text-center text-muted">
          暂无符合筛选条件的账单记录。
        </div>

        <div v-else class="shayu-daily-groups">
          <div v-for="group in groupedRecords" :key="group.date" class="shayu-date-group mb-24">
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
              <div v-for="rec in group.items" :key="rec.id" class="record-row d-flex flex-column gap-12">
                <!-- First Row: Category Icon & Name (Left), Actions (Right) -->
                <div class="rec-line-1 d-flex justify-between align-center">
                  <div class="d-flex align-center gap-8">
                    <div class="cat-icon-circle-mini"
                      :style="{ backgroundColor: `${rec.category?.color || '#ffd21e'}12`, color: rec.category?.color || '#ffd21e' }">
                      <component :is="getIconComponent(rec.category?.icon || 'HelpCircle')" :size="16" />
                    </div>
                    <span class="rec-cat font-semibold" style="font-size: 15px; color: var(--color-text-dark);">
                      {{ rec.category?.name || '未知' }}
                    </span>
                  </div>

                  <div class="rec-actions">
                    <button class="action-btn" @click="openEditRecord(rec)" title="编辑">
                      <Edit :size="14" />
                    </button>
                    <button class="action-btn text-danger-hover" @click="handleDeleteRecord(rec.id)" title="删除">
                      <Trash2 :size="14" />
                    </button>
                  </div>
                </div>

                <!-- Second Row: Amount (Right aligned) -->
                <div class="rec-line-2 d-flex justify-end align-center">
                  <span class="rec-amount font-semibold"
                    :class="rec.type === 'expense' ? 'text-danger' : 'text-success'">
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

                <!-- Record Images Row -->
                <div v-if="rec.images && rec.images.length > 0" class="record-images-preview-row d-flex gap-8 mb-8 mt-8">
                  <img v-for="(img, idx) in rec.images" :key="idx" :src="getFullImageUrl(img)"
                    class="record-inline-thumbnail" @click.stop="handlePreviewImage(rec.images, idx)" />
                </div>

                <!-- Third Row: Note/Remarks with Tooltip -->
                <div class="rec-line-3">
                  <div class="rec-note-tooltip-wrapper">
                    <span class="rec-note-text">
                      {{ rec.note || '无备注' }}
                    </span>
                    <span class="rec-tooltip">{{ rec.note || '无备注' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Record Modal (ShaYu Style Keyboard Layout) -->
    <div v-if="showAddRecordModal" class="modal-backdrop" @click.self="showAddRecordModal = false">
      <div class="modal-content">
        <h3 class="mb-16">记一笔</h3>

        <!-- Toggle Tabs -->
        <div class="radio-group-tabs mb-16">
          <button type="button" class="tab-btn" :class="{ active: recordForm.type === 'expense' }"
            @click="recordForm.type = 'expense'; recordForm.category_id = expenseCategories[0]?.id">
            日常支出
          </button>
          <button type="button" class="tab-btn" :class="{ active: recordForm.type === 'income' }"
            @click="recordForm.type = 'income'; recordForm.category_id = incomeCategories[0]?.id">
            日常收入
          </button>
        </div>

        <!-- Categories Picker Grid -->
        <div class="category-picker-grid mb-16">
          <button v-for="cat in (recordForm.type === 'expense' ? expenseCategories : incomeCategories)" :key="cat.id"
            type="button" class="category-picker-item" :class="{ active: recordForm.category_id === cat.id }"
            @click="recordForm.category_id = cat.id">
            <div class="category-picker-icon-circle">
              <component :is="getIconComponent(cat.icon)" :size="20" />
            </div>
            <span class="category-picker-name">{{ cat.name }}</span>
          </button>
        </div>

        <!-- Note & Date row -->
        <div class="d-flex gap-8 mb-16 align-center">
          <el-input v-model="recordForm.note" placeholder="写点备注..." maxlength="40" clearable
            style="flex: 2; --el-input-text-color: #222;" />
          <el-date-picker v-model="recordForm.record_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期"
            :editable="false" :clearable="false" style="flex: 1; min-width: 130px;" />
        </div>

        <!-- Attachment Images Upload Grid -->
        <div class="image-uploader-section mb-16">
          <div class="image-upload-grid">
            <div v-for="(img, idx) in recordForm.images" :key="idx" class="upload-thumbnail-wrapper">
              <img :src="getFullImageUrl(img)" class="upload-thumbnail"
                @click="handlePreviewImage(recordForm.images, idx)" />
              <button type="button" class="thumbnail-delete-btn" @click="removeFormImage(idx)">
                <X :size="10" />
              </button>
            </div>

            <div v-if="uploadingImagesCount > 0" class="upload-thumbnail-wrapper uploading">
              <div class="upload-spinner"></div>
            </div>

            <label v-if="(recordForm.images || []).length + uploadingImagesCount < 6" class="upload-trigger-btn">
              <input type="file" accept="image/*" multiple class="hidden-file-input" @change="handleFileUpload" />
              <Plus :size="16" />
              <span class="upload-btn-text">添加图片</span>
            </label>
          </div>
        </div>

        <!-- Realtime Amount Display -->
        <div class="d-flex justify-between align-center mb-8 px-8"
          style="border-bottom: 2px solid #eef1f6; padding-bottom: 8px;">
          <span class="text-muted" style="font-weight: 700;">金额</span>
          <span style="font-size: 28px; font-weight: 800; font-family: var(--font-heading); color: #222;">
            ¥{{ recordForm.amount || '0.00' }}
          </span>
        </div>

        <div v-if="recordError" class="error-msg-text mb-8">{{ recordError }}</div>

        <!-- Calculator Keypad Grid -->
        <div class="calculator-keypad">
          <button type="button" class="key-btn" @click="handleKeyboardPress('1')">1</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('2')">2</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('3')">3</button>
          <button type="button" class="key-btn action" @click="handleKeyboardPress('⌫')">⌫</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('4')">4</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('5')">5</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('6')">6</button>
          <button type="button" class="key-btn action" @click="handleKeyboardPress('C')">清空</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('7')">7</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('8')">8</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('9')">9</button>
          <button type="button" class="key-btn confirm" @click="handleCreateRecord"
            :disabled="submittingRecord">确定</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('.')">.</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('0')">0</button>
          <button type="button" class="key-btn action" @click="showAddRecordModal = false">取消</button>
        </div>
      </div>
    </div>

    <!-- Edit Record Modal (ShaYu Style Keyboard Layout) -->
    <div v-if="showEditRecordModal" class="modal-backdrop" @click.self="showEditRecordModal = false">
      <div class="modal-content">
        <h3 class="mb-16">修改账单</h3>

        <!-- Toggle Tabs -->
        <div class="radio-group-tabs mb-16">
          <button type="button" class="tab-btn" :class="{ active: recordForm.type === 'expense' }"
            @click="recordForm.type = 'expense'; recordForm.category_id = expenseCategories[0]?.id">
            日常支出
          </button>
          <button type="button" class="tab-btn" :class="{ active: recordForm.type === 'income' }"
            @click="recordForm.type = 'income'; recordForm.category_id = incomeCategories[0]?.id">
            日常收入
          </button>
        </div>

        <!-- Categories Picker Grid -->
        <div class="category-picker-grid mb-16">
          <button v-for="cat in (recordForm.type === 'expense' ? expenseCategories : incomeCategories)" :key="cat.id"
            type="button" class="category-picker-item" :class="{ active: recordForm.category_id === cat.id }"
            @click="recordForm.category_id = cat.id">
            <div class="category-picker-icon-circle">
              <component :is="getIconComponent(cat.icon)" :size="20" />
            </div>
            <span class="category-picker-name">{{ cat.name }}</span>
          </button>
        </div>

        <!-- Note & Date row -->
        <div class="d-flex gap-8 mb-16 align-center">
          <el-input v-model="recordForm.note" placeholder="写点备注..." maxlength="40" clearable
            style="flex: 2; --el-input-text-color: #222;" />
          <el-date-picker v-model="recordForm.record_date" type="date" value-format="YYYY-MM-DD" placeholder="选择日期"
            :editable="false" :clearable="false" style="flex: 1; min-width: 130px;" />
        </div>

        <!-- Attachment Images Upload Grid -->
        <div class="image-uploader-section mb-16">
          <div class="image-upload-grid">
            <div v-for="(img, idx) in recordForm.images" :key="idx" class="upload-thumbnail-wrapper">
              <img :src="getFullImageUrl(img)" class="upload-thumbnail"
                @click="handlePreviewImage(recordForm.images, idx)" />
              <button type="button" class="thumbnail-delete-btn" @click="removeFormImage(idx)">
                <X :size="10" />
              </button>
            </div>

            <div v-if="uploadingImagesCount > 0" class="upload-thumbnail-wrapper uploading">
              <div class="upload-spinner"></div>
            </div>

            <label v-if="(recordForm.images || []).length + uploadingImagesCount < 6" class="upload-trigger-btn">
              <input type="file" accept="image/*" multiple class="hidden-file-input" @change="handleFileUpload" />
              <Plus :size="16" />
              <span class="upload-btn-text">添加图片</span>
            </label>
          </div>
        </div>

        <!-- Realtime Amount Display -->
        <div class="d-flex justify-between align-center mb-8 px-8"
          style="border-bottom: 2px solid #eef1f6; padding-bottom: 8px;">
          <span class="text-muted" style="font-weight: 700;">金额</span>
          <span style="font-size: 28px; font-weight: 800; font-family: var(--font-heading); color: #222;">
            ¥{{ recordForm.amount || '0.00' }}
          </span>
        </div>

        <div v-if="recordError" class="error-msg-text mb-8">{{ recordError }}</div>

        <!-- Calculator Keypad Grid -->
        <div class="calculator-keypad">
          <button type="button" class="key-btn" @click="handleKeyboardPress('1')">1</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('2')">2</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('3')">3</button>
          <button type="button" class="key-btn action" @click="handleKeyboardPress('⌫')">⌫</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('4')">4</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('5')">5</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('6')">6</button>
          <button type="button" class="key-btn action" @click="handleKeyboardPress('C')">清空</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('7')">7</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('8')">8</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('9')">9</button>
          <button type="button" class="key-btn confirm" @click="handleUpdateRecord"
            :disabled="submittingRecord">确定</button>

          <button type="button" class="key-btn" @click="handleKeyboardPress('.')">.</button>
          <button type="button" class="key-btn" @click="handleKeyboardPress('0')">0</button>
          <button type="button" class="key-btn action" @click="showEditRecordModal = false">取消</button>
        </div>
      </div>
    </div>
    <!-- Image Preview Gallery Component -->
    <ImagePreviewGallery
      :show="previewGallery.show"
      :images="previewGallery.images"
      :initial-index="previewGallery.currentIndex"
      @close="previewGallery.show = false"
    />

    <!-- Reusable Confirm Modal -->
    <ConfirmModal :show="confirmModal.show" :title="confirmModal.title" :message="confirmModal.message"
      :type="confirmModal.type" @confirm="confirmModal.onConfirm" @cancel="confirmModal.onCancel" />

    <!-- Mobile Filter Drawer -->
    <el-drawer v-model="showMobileFilters" title="账单筛选" direction="btt" size="480px"
      custom-class="mobile-filter-drawer">
      <div class="mobile-filter-content">
        <div class="form-group mb-16">
          <label class="d-block mb-8 text-muted" style="font-size: 13px; font-weight: 600;">账单类型</label>
          <el-select v-model="tempFilterType" placeholder="全部" style="width: 100%;">
            <el-option label="全部" value="" />
            <el-option label="支出" value="expense" />
            <el-option label="收入" value="income" />
          </el-select>
        </div>

        <div class="form-group mb-16">
          <label class="d-block mb-8 text-muted" style="font-size: 13px; font-weight: 600;">账单类别</label>
          <el-select v-model="tempFilterCategory" placeholder="全部" style="width: 100%;">
            <el-option label="全部" value="" />
            <el-option v-for="cat in categories" :key="cat.id"
              :label="`${cat.name} (${cat.type === 'expense' ? '支' : '收'})`" :value="cat.id" />
          </el-select>
        </div>

        <div class="form-group mb-16">
          <label class="d-block mb-8 text-muted" style="font-size: 13px; font-weight: 600;">起始日期</label>
          <el-date-picker v-model="tempFilterStartDate" type="date" value-format="YYYY-MM-DD" placeholder="选择起始日期"
            style="width: 100%;" />
        </div>

        <div class="form-group mb-24">
          <label class="d-block mb-8 text-muted" style="font-size: 13px; font-weight: 600;">结束日期</label>
          <el-date-picker v-model="tempFilterEndDate" type="date" value-format="YYYY-MM-DD" placeholder="选择结束日期"
            style="width: 100%;" />
        </div>

        <div class="d-flex gap-16 mt-24">
          <el-button class="flex-1" @click="handleMobileClear">清空</el-button>
          <el-button type="primary" class="flex-1" @click="handleMobileConfirm">确定</el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.ledger-view-container {
  max-width: 1000px;
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
  to {
    transform: rotate(360deg);
  }
}

.stats-banner-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.stat-column .stat-lbl {
  font-size: 12px;
  color: rgba(34, 34, 34, 0.55);
  font-weight: 600;
  margin-bottom: 4px;
}

.stat-column .stat-val {
  font-size: 20px;
  font-weight: 800;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.filter-group label {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-bottom: 4px;
}

.clear-filters-btn {
  background: none;
  border: none;
  font-size: 12px;
  cursor: pointer;
  font-family: inherit;
}

.clear-filters-btn:hover {
  color: var(--primary-hover) !important;
}

/* Records List */
.empty-records {
  padding: 40px 0;
}

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

.record-row {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 8px;
  border-bottom: 1px solid var(--panel-border);
  transition: background-color var(--transition-fast);
}

.record-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.cat-icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cat-icon-circle-mini {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.rec-cat {
  font-size: 15px;
}

.rec-note-tooltip-wrapper {
  position: relative;
  display: inline-block;
  max-width: 100%;
}

.rec-note-text {
  max-width: 280px;
  display: block;
  text-overflow: ellipsis;
  overflow: hidden;
  white-space: nowrap;
  font-size: 13px;
  color: var(--color-text-muted);
}

.rec-tooltip {
  visibility: hidden;
  position: absolute;
  z-index: 100;
  bottom: 125%;
  left: 0;
  background-color: rgba(34, 34, 34, 0.95);
  color: #fff;
  text-align: left;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  line-height: 1.4;
  white-space: normal;
  max-width: 250px;
  min-width: 120px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.rec-note-tooltip-wrapper:hover .rec-tooltip,
.rec-note-tooltip-wrapper:active .rec-tooltip {
  visibility: visible;
  opacity: 1;
}

.rec-amount {
  font-family: var(--font-heading);
  font-size: 18px;
}

.rec-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.record-row:hover .rec-actions {
  opacity: 1;
}

.action-btn {
  background: none;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  transition: var(--transition-fast);
}

.action-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-dark);
}

.action-btn.text-danger-hover:hover {
  background: rgba(255, 71, 87, 0.1);
  color: var(--danger);
}

/* Modals Tabs */
.radio-group-tabs {
  display: flex;
  background: var(--gray-100);
  border-radius: var(--radius-md);
  padding: 4px;
}

.tab-btn {
  flex: 1;
  background: none;
  border: none;
  color: var(--color-text-muted);
  font-family: inherit;
  font-weight: 700;
  padding: 10px;
  border-radius: calc(var(--radius-md) - 4px);
  cursor: pointer;
  transition: var(--transition-fast);
}

.tab-btn.active {
  background: #ffffff;
  color: var(--primary-text);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
}

.error-msg-text {
  color: var(--danger);
  font-size: 13px;
  text-align: center;
}

.flex-1 {
  flex: 1;
}

.px-8 {
  padding-left: 8px;
  padding-right: 8px;
}

.mobile-filter-trigger-btn {
  display: none;
  background: none;
  border: none;
  padding: 8px;
  cursor: pointer;
  color: var(--color-text-muted);
  border-radius: 50%;
  transition: all 0.2s;
  align-items: center;
  justify-content: center;
}

.mobile-filter-trigger-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.mobile-filter-trigger-btn.active {
  color: var(--primary) !important;
}

.mobile-filter-content {
  padding: 0 16px 20px 16px;
}

@media (max-width: 768px) {
  .filter-card {
    display: none !important;
  }

  .mobile-filter-trigger-btn {
    display: inline-flex;
  }

  .stats-banner-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .filters-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .rec-actions {
    opacity: 1;
  }

  .category-picker-grid {
    grid-template-columns: repeat(4, 1fr);
  }

  .rec-note-text {
    max-width: 120px;
  }
}
</style>
