/**
 * Storage utility that uses localStorage instead of cookies
 * Provides a similar API to vue-cookies but without size limitations
 */

const StorageManager = {
  /**
   * Set a value in localStorage
   * @param {string} key - The key to store
   * @param {any} value - The value to store (will be JSON stringified if object)
   * @param {string|number} expires - Expiration (optional, for compatibility with cookies API)
   * @returns {this}
   */
  set(key, value, expires = null) {
    try {
      const item = {
        value: value,
        timestamp: Date.now(),
        expires: expires
      }
      localStorage.setItem(key, JSON.stringify(item))
    } catch (e) {
      console.error(`Error setting localStorage item ${key}:`, e)
    }
    return this
  },

  /**
   * Get a value from localStorage
   * @param {string} key - The key to retrieve
   * @returns {any} The stored value or null if not found/expired
   */
  get(key) {
    try {
      const itemStr = localStorage.getItem(key)
      if (!itemStr) {
        return null
      }

      const item = JSON.parse(itemStr)

      // Check if item has expired (if expiration was set)
      if (item.expires) {
        const expirationMs = this._parseExpiration(item.expires)
        if (expirationMs && Date.now() - item.timestamp > expirationMs) {
          this.remove(key)
          return null
        }
      }

      return item.value
    } catch (e) {
      console.error(`Error getting localStorage item ${key}:`, e)
      return null
    }
  },

  /**
   * Remove a value from localStorage
   * @param {string} key - The key to remove
   * @returns {this}
   */
  remove(key) {
    try {
      localStorage.removeItem(key)
    } catch (e) {
      console.error(`Error removing localStorage item ${key}:`, e)
    }
    return this
  },

  /**
   * Check if a key exists in localStorage
   * @param {string} key - The key to check
   * @returns {boolean}
   */
  isKey(key) {
    return this.get(key) !== null
  },

  /**
   * Get all keys in localStorage
   * @returns {Array<string>}
   */
  keys() {
    try {
      return Object.keys(localStorage)
    } catch (e) {
      console.error("Error getting localStorage keys:", e)
      return []
    }
  },

  /**
   * Clear all items from localStorage
   */
  clear() {
    try {
      localStorage.clear()
    } catch (e) {
      console.error("Error clearing localStorage:", e)
    }
  },

  /**
   * Parse expiration string to milliseconds
   * @private
   * @param {string|number} expires - Expiration time (e.g., "35min", "1d", "2h")
   * @returns {number|null} Milliseconds or null
   */
  _parseExpiration(expires) {
    if (!expires) return null
    if (typeof expires === "number") return expires

    const match = expires.match(/^(\d+)(min|h|d|y|s)$/)
    if (!match) return null

    const value = parseInt(match[1])
    const unit = match[2]

    const multipliers = {
      s: 1000,
      min: 60 * 1000,
      h: 60 * 60 * 1000,
      d: 24 * 60 * 60 * 1000,
      y: 365 * 24 * 60 * 60 * 1000
    }

    return value * (multipliers[unit] || 0)
  }
}

/**
 * Vue plugin to install the storage manager
 */
export default {
  install(app, options = {}) {
    const storageInstance = Object.create(StorageManager)

    // Set default expiration if provided in options
    if (options.expires) {
      const originalSet = storageInstance.set
      storageInstance.set = function (key, value, expires = options.expires) {
        return originalSet.call(this, key, value, expires)
      }
    }

    app.config.globalProperties.$storage = storageInstance
    app.provide("storage", storageInstance)
  }
}

// Also export the storage manager for direct use
export { StorageManager }
