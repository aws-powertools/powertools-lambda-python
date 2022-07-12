module.exports = Object.freeze({
    /** @type {string} */
    "PR_ACTION": process.env.PR_ACTION || "",
    /** @type {string} */
    "PR_AUTHOR": process.env.PR_AUTHOR || "",
    /** @type {string} */
    "PR_BODY": process.env.PR_BODY || "",
    /** @type {string} */
    "PR_TITLE": process.env.PR_TITLE || "",
    /** @type {number} */
    "PR_NUMBER": process.env.PR_NUMBER || 0,
    /** @type {boolean} */
    "PR_IS_MERGED": process.env.PR_IS_MERGED || false,
    /** @type {string[]} */
    "IGNORE_AUTHORS": ["dependabot[bot]", "markdownify[bot]"],
    /** @type {string} */
    "BLOCK_LABEL": "do-not-merge",
    /** @type {string} */
    "BLOCK_REASON_LABEL": "need-issue",
});
