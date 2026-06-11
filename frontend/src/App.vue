<template>
  <router-view />
  <AuthDialog />
</template>

<script setup>
import AuthDialog from '@/components/AuthDialog.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  font-family: var(--font-sans);
  background-color: var(--color-bg);
  color: var(--color-text-primary);
  line-height: var(--leading-normal);
}

a {
  color: var(--color-primary);
  text-decoration: none;
  transition: color var(--transition-fast);
}

a:hover {
  color: var(--color-primary-hover);
}

/* Scrollbar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-tertiary);
}

::-webkit-scrollbar-track {
  background: transparent;
}

/* === Page Transition === */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity var(--transition-normal), transform var(--transition-normal);
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* === Element Plus Global Overrides === */

/* Card */
.el-card {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--color-border-light) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast), border-color var(--transition-fast) !important;
}

.el-card:hover {
  box-shadow: var(--shadow-md) !important;
  border-color: var(--color-border) !important;
}

.el-card__header {
  border-bottom: 1px solid var(--color-border-light);
  color: var(--color-text-primary);
  font-weight: var(--font-semibold);
  padding: 16px 20px;
}

.el-card__body {
  padding: 20px;
}

/* Input */
.el-input__wrapper {
  border-radius: var(--radius-md) !important;
  box-shadow: none !important;
  border: 1px solid var(--color-border);
  transition: all var(--transition-fast) !important;
}

.el-input__wrapper:hover {
  border-color: var(--color-text-tertiary);
}

.el-input__wrapper.is-focus {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px var(--color-primary-light) !important;
}

.el-textarea__inner {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--color-border);
}

.el-textarea__inner:focus {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px var(--color-primary-light) !important;
}

/* Select */
.el-select .el-input__wrapper {
  border-radius: var(--radius-md) !important;
}

.el-select-dropdown {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--color-border-light) !important;
  box-shadow: var(--shadow-xl) !important;
  margin-top: 4px !important;
}

.el-select-dropdown__item {
  border-radius: var(--radius-sm);
  margin: 2px 6px;
  padding: 8px 12px;
}

.el-select-dropdown__item.is-selected {
  color: var(--color-primary);
  font-weight: var(--font-semibold);
}

/* Button */
.el-button {
  border-radius: var(--radius-md) !important;
  font-weight: var(--font-medium) !important;
  transition: all var(--transition-fast) !important;
}

.el-button:active {
  transform: scale(0.97);
}

.el-button--primary {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-text-color: #fff;
  --el-button-hover-bg-color: var(--color-primary-hover);
  --el-button-hover-border-color: var(--color-primary-hover);
  --el-button-hover-text-color: #fff;
  --el-button-active-bg-color: var(--color-primary-active);
  --el-button-active-border-color: var(--color-primary-active);
}

.el-button--primary:hover {
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.35);
}

.el-button--default {
  --el-button-bg-color: var(--color-surface);
  --el-button-border-color: var(--color-border);
  --el-button-text-color: var(--color-text-secondary);
  --el-button-hover-bg-color: var(--color-surface-hover);
  --el-button-hover-border-color: var(--color-text-tertiary);
  --el-button-hover-text-color: var(--color-text-primary);
}

/* Dialog */
.el-dialog {
  border-radius: var(--radius-xl) !important;
  box-shadow: var(--shadow-dialog) !important;
  animation: dialogIn var(--transition-spring) forwards;
}

@keyframes dialogIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(16px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.el-dialog__header {
  border-bottom: 1px solid var(--color-border-light);
  padding: 20px 24px 16px;
  margin: 0;
}

.el-dialog__title {
  font-weight: var(--font-semibold);
  font-size: var(--text-lg);
  color: var(--color-text-primary);
}

.el-dialog__body {
  padding: 24px;
}

.el-dialog__footer {
  padding: 12px 24px 20px;
}

/* Table */
.el-table {
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
}

.el-table th.el-table__cell {
  background: var(--color-surface-secondary);
  color: var(--color-text-secondary);
  font-weight: var(--font-semibold);
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.el-table td.el-table__cell {
  border-bottom: 1px solid var(--color-border-light);
}

.el-table__body tr:hover > td {
  background: var(--color-surface-hover);
}

/* Tag */
.el-tag {
  border-radius: var(--radius-full) !important;
  border: none !important;
  font-weight: var(--font-medium);
  font-size: var(--text-xs);
  padding: 2px 10px;
}

.el-tag--primary {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.el-tag--success {
  background: var(--color-success-light);
  color: #16a34a;
}

.el-tag--warning {
  background: var(--color-warning-light);
  color: #d97706;
}

.el-tag--danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.el-tag--info {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

/* Progress */
.el-progress-bar__outer {
  background: var(--color-border-light) !important;
  border-radius: var(--radius-full) !important;
}

.el-progress-bar__inner {
  border-radius: var(--radius-full) !important;
  transition: width var(--transition-slow) !important;
}

/* Calendar */
.el-calendar {
  border-radius: var(--radius-md);
}

.el-calendar-table .el-calendar-day {
  border-radius: 50%;
  transition: background var(--transition-fast);
}

.el-calendar-table td.is-selected {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

/* Message / Toast */
.el-message {
  border-radius: var(--radius-md) !important;
  box-shadow: var(--shadow-lg) !important;
  animation: toastIn var(--transition-spring) forwards !important;
  border: 1px solid var(--color-border-light);
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateX(24px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.el-message-box {
  border-radius: var(--radius-xl) !important;
  box-shadow: var(--shadow-dialog) !important;
}

/* Dropdown */
.el-dropdown-menu {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--color-border-light) !important;
  box-shadow: var(--shadow-xl) !important;
  padding: 6px !important;
  margin-top: 4px !important;
}

.el-dropdown-menu__item {
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  font-size: var(--text-sm);
  transition: all var(--transition-fast);
}

/* Checkbox */
.el-checkbox__inner {
  border-radius: var(--radius-xs);
  border-color: var(--color-border);
  transition: all var(--transition-fast);
}

.el-checkbox__input.is-checked .el-checkbox__inner {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

/* Slider */
.el-slider__bar {
  background: var(--color-primary) !important;
}

.el-slider__button {
  border-color: var(--color-primary) !important;
  box-shadow: var(--shadow-sm);
}

/* Radio button */
.el-radio-button.is-active .el-radio-button__inner {
  background: var(--color-primary-light) !important;
  border-color: var(--color-primary) !important;
  color: var(--color-primary) !important;
  box-shadow: none !important;
}

/* Switch */
.el-switch.is-checked .el-switch__core {
  background: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

/* Page header */
.el-page-header__content {
  font-weight: var(--font-medium);
}

/* Empty state */
.el-empty__description p {
  color: var(--color-text-tertiary) !important;
}

.el-empty__image {
  opacity: 0.5;
}

/* Descriptions */
.el-descriptions__label {
  background: var(--color-surface-secondary);
  font-weight: var(--font-medium);
}

/* Pagination */
.el-pagination .el-pager li.is-active {
  background: var(--color-primary) !important;
  border-radius: var(--radius-sm);
}

/* Date picker */
.el-picker-panel {
  border-radius: var(--radius-lg) !important;
  border: 1px solid var(--color-border-light) !important;
  box-shadow: var(--shadow-xl) !important;
}

/* Form */
.el-form-item__label {
  color: var(--color-text-primary);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
}

/* Alert */
.el-alert {
  border-radius: var(--radius-md) !important;
  border: none !important;
}

/* Avatar */
.el-avatar {
  font-weight: var(--font-semibold);
}

/* Popover */
.el-popover {
  border-radius: var(--radius-md) !important;
  border: 1px solid var(--color-border-light) !important;
  box-shadow: var(--shadow-xl) !important;
}

/* Divider */
.el-divider--horizontal {
  border-top-color: var(--color-border-light);
  margin: 16px 0;
}
</style>
