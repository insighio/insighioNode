<template>
  <div
    v-if="current"
    class="modal active app-alert"
    :class="typeClass"
    role="alertdialog"
    aria-modal="true"
    aria-labelledby="app-alert-title"
    aria-describedby="app-alert-message"
  >
    <div class="modal-overlay"></div>
    <div class="modal-container">
      <div class="modal-header">
        <div id="app-alert-title" class="modal-title h5">
          <span class="app-alert-icon" aria-hidden="true">{{ icon }}</span>
          {{ current.title }}
        </div>
      </div>
      <div class="modal-body">
        <p id="app-alert-message" class="app-alert-message">{{ current.message }}</p>
      </div>
      <div class="modal-footer">
        <button ref="okButton" type="button" class="btn btn-primary app-alert-ok" @click="close">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import { alertState, dismissAlert } from "@/js/appAlert.js"

const ICONS = { error: "!", warning: "!", success: "ok", info: "i" }
const TYPE_CLASSES = {
  error: "app-alert-error",
  warning: "app-alert-warning",
  success: "app-alert-success",
  info: "app-alert-info"
}

export default {
  name: "AppAlertDialog",
  data() {
    return {
      returnFocusTo: null
    }
  },
  computed: {
    current() {
      return alertState.queue[0] || null
    },
    icon() {
      return ICONS[this.current?.type] || ICONS.info
    },
    typeClass() {
      return TYPE_CLASSES[this.current?.type] || TYPE_CLASSES.info
    }
  },
  watch: {
    "current.id"(id, previousId) {
      if (id && !previousId && !this.$el?.contains?.(document.activeElement)) {
        this.returnFocusTo = document.activeElement
      }
      this.$nextTick(() => {
        if (id) {
          this.$refs.okButton?.focus()
        } else if (this.returnFocusTo?.isConnected) {
          this.returnFocusTo.focus()
          this.returnFocusTo = null
        }
      })
    }
  },
  mounted() {
    // Capture phase on window runs before other dialogs' document listeners, so they don't also react.
    window.addEventListener("keydown", this.handleKeydown, true)
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleKeydown, true)
  },
  methods: {
    close() {
      dismissAlert()
    },
    handleKeydown(event) {
      if (!this.current) return
      if (event.key === "Escape") {
        event.preventDefault()
        event.stopPropagation()
        this.close()
      } else if (event.key === "Tab") {
        event.preventDefault()
        event.stopPropagation()
        this.$refs.okButton?.focus()
      }
    }
  }
}
</script>

<style scoped>
.app-alert {
  z-index: 2000;
}

.app-alert .modal-overlay {
  background: rgba(35, 53, 66, 0.55);
}

.app-alert .modal-container {
  max-width: min(92vw, 30rem);
  border-top: 5px solid var(--ui-accent);
}

.app-alert-error .modal-container {
  border-top-color: #b42318;
}

.app-alert-warning .modal-container {
  border-top-color: #b54708;
}

.app-alert .modal-title {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  color: #233542;
}

.app-alert-icon {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 50%;
  background: var(--ui-accent);
  color: white;
  font-size: 0.9rem;
  font-weight: 700;
}

.app-alert-error .app-alert-icon {
  background: #b42318;
}

.app-alert-warning .app-alert-icon {
  background: #b54708;
}

.app-alert-message {
  margin: 0;
  color: #233542;
  white-space: pre-line;
  overflow-wrap: anywhere;
}

.app-alert-ok {
  min-width: 6rem;
}

@media (max-width: 600px) {
  .app-alert-ok {
    width: 100%;
  }
}
</style>
