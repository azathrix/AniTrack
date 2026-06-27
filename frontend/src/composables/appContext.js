import { inject } from 'vue'

export function appContextComponent(components = {}) {
  const optionKeys = ['components', 'computed', 'methods', 'watch', 'emits', 'props']
  const isOptionsObject = components && optionKeys.some(key => Object.prototype.hasOwnProperty.call(components, key))
  const options = isOptionsObject ? components : { components }
  return {
    ...options,
    setup() {
      return inject('appContext') || {}
    },
  }
}
