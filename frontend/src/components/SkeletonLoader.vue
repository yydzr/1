<template>
  <div class="skeleton" :class="variant">
    <template v-if="variant === 'card'">
      <div class="sk-line sk-title"></div>
      <div class="sk-line sk-text"></div>
      <div class="sk-line sk-text short"></div>
      <div class="sk-line sk-text"></div>
      <div class="sk-line sk-text short"></div>
    </template>
    <template v-else-if="variant === 'list'">
      <div v-for="i in count" :key="i" class="sk-row">
        <div class="sk-circle"></div>
        <div class="sk-col">
          <div class="sk-line sk-title"></div>
          <div class="sk-line sk-text short"></div>
        </div>
      </div>
    </template>
    <template v-else-if="variant === 'stats'">
      <div v-for="i in count" :key="i" class="sk-stat">
        <div class="sk-line sk-value"></div>
        <div class="sk-line sk-label"></div>
      </div>
    </template>
    <template v-else-if="variant === 'chart'">
      <div class="sk-chart"></div>
      <div class="sk-line sk-label" style="margin-top:8px"></div>
    </template>
    <template v-else>
      <div v-for="i in count" :key="i" class="sk-row">
        <div class="sk-circle"></div>
        <div class="sk-col">
          <div class="sk-line sk-title"></div>
          <div class="sk-line sk-text"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  variant: { type: String, default: 'text' },
  count: { type: Number, default: 3 },
})
</script>

<style scoped>
.skeleton {
  padding: 16px 0;
}

/* Shimmer */
.sk-line, .sk-circle, .sk-chart, .sk-value, .sk-label, .sk-stat {
  background: linear-gradient(90deg, var(--color-border-light) 25%, var(--color-surface-hover, #e8eaed) 50%, var(--color-border-light) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.sk-line { height: 12px; margin-bottom: 10px; }
.sk-title { width: 60%; height: 16px; }
.sk-text { width: 90%; }
.sk-text.short { width: 40%; }
.sk-value { width: 50%; height: 28px; margin-bottom: 4px; }
.sk-label { width: 30%; height: 10px; margin: 0 auto; }

.sk-circle { width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0; }
.sk-chart { width: 100%; height: 220px; border-radius: var(--radius-md); margin-bottom: 10px; }

.sk-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.sk-col { flex: 1; }

.skeleton.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.sk-stat { text-align: center; padding: 16px 0; }
</style>
