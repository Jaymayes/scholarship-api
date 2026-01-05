<template>
  <div class="demo-mode-wrapper">
    <!-- Mode Toggle Button -->
    <button 
      @click="toggleMode" 
      :class="['mode-toggle', currentMode]"
      :title="modeTitle"
    >
      <span class="mode-icon">{{ modeIcon }}</span>
      <span class="mode-label">{{ modeLabel }}</span>
    </button>
    
    <!-- Warning Banner (shown in demo/all modes) -->
    <div v-if="showWarning" class="demo-warning-banner">
      <span class="warning-icon">⚠️</span>
      <span class="warning-text">{{ warningText }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DemoModeBadge',
  
  data() {
    return {
      currentMode: 'live', // 'live', 'demo', 'all'
    }
  },
  
  computed: {
    modeIcon() {
      return {
        live: '📊',
        demo: '🧪',
        all: '🔧'
      }[this.currentMode]
    },
    
    modeLabel() {
      return {
        live: 'LIVE',
        demo: 'DEMO',
        all: 'ALL'
      }[this.currentMode]
    },
    
    modeTitle() {
      return {
        live: 'Showing live production data only',
        demo: 'Showing simulated/test data for demonstration',
        all: 'Showing all data (admin mode)'
      }[this.currentMode]
    },
    
    showWarning() {
      return this.currentMode !== 'live'
    },
    
    warningText() {
      return {
        demo: 'Demo Mode - Data is simulated',
        all: 'Admin Mode - Includes test data'
      }[this.currentMode]
    }
  },
  
  methods: {
    toggleMode() {
      const modes = ['live', 'demo']
      const currentIndex = modes.indexOf(this.currentMode)
      this.currentMode = modes[(currentIndex + 1) % modes.length]
      this.$emit('mode-change', this.currentMode)
    }
  }
}
</script>

<style scoped>
.demo-mode-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mode-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  border: 2px solid;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s ease;
}

.mode-toggle.live {
  background: #dcfce7;
  border-color: #22c55e;
  color: #166534;
}

.mode-toggle.demo {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
}

.mode-toggle.all {
  background: #fecaca;
  border-color: #ef4444;
  color: #991b1b;
}

.demo-warning-banner {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  background: #fef3c7;
  border-radius: 4px;
  font-size: 11px;
  color: #92400e;
}

.warning-icon {
  font-size: 14px;
}
</style>
