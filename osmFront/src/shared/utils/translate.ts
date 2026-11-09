
/**
 * Translates a message using a translation function.
 * @param {string} msg - The message to translate.
 * @param {function} t - The translation function.
 * @returns {string} The translated message.
 */
export function translate(msg: string, t?: (key: string) => string) {
  return t ? t(msg) || msg : msg;
}
