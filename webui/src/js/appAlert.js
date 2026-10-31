import { reactive } from "vue"

const DEFAULT_TITLES = {
  error: "Something went wrong",
  warning: "Please check your input",
  success: "Done",
  info: "Notice"
}

let nextId = 0

export const alertState = reactive({ queue: [] })

// In-app replacement for window.alert(), which is unstyled and may render without buttons in Android WebViews.
// Alerts are queued and the returned promise resolves when the user dismisses the alert.
export function showAlert(message, options = {}) {
  const type = DEFAULT_TITLES[options.type] ? options.type : "info"
  return new Promise((resolve) => {
    alertState.queue.push({
      id: ++nextId,
      type,
      title: options.title || DEFAULT_TITLES[type],
      message: String(message),
      resolve
    })
  })
}

export function dismissAlert() {
  const current = alertState.queue.shift()
  current?.resolve()
}
