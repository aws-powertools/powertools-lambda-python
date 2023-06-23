module.exports = Object.freeze({
    /** @type {string} */
    // Values: https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#pull_request
    "PR_ACTION": process.env.PR_ACTION?.replace(/"/g, '') || "",

    /** @type {string} */
    "PR_AUTHOR": process.env.PR_AUTHOR?.replace(/"/g, '') || "",

    /** @type {string} */
    "PR_BODY": process.env.PR_BODY || "",

    /** @type {string} */
    "PR_TITLE": process.env.PR_TITLE || "",

    /** @type {number} */
    "PR_NUMBER": process.env.PR_NUMBER || 0,

    /** @type {string} */
    "PR_IS_MERGED": process.env.PR_IS_MERGED || "false",

    /** @type {string} */
    "LABEL_BLOCK": "do-not-merge",

    /** @type {string} */
    "LABEL_BLOCK_REASON": "need-issue",

    /** @type {string} */
    "LABEL_BLOCK_MISSING_LICENSE_AGREEMENT": "need-license-agreement-acknowledge",

    /** @type {string} */
    "LABEL_PENDING_RELEASE": "pending-release",

    /** @type {string} */
    "HANDLE_MAINTAINERS_TEAM": "@aws-powertools/powertools-lambda-python",

    /** @type {string[]} */
    "IGNORE_AUTHORS": ["dependabot[bot]", "markdownify[bot]"],

});
