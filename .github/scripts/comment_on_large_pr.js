const {
  PR_NUMBER,
  PR_AUTHOR,
  IGNORE_AUTHORS,
} = require("./constants")

module.exports = async ({github, context, core}) => {
    if (IGNORE_AUTHORS.includes(PR_AUTHOR)) {
      return core.notice("Author in IGNORE_AUTHORS list; skipping...")
    }

    core.info(`Commenting on PR ${PR_NUMBER}`)

    let msg = `
    ### ⚠️Large PR detected⚠️.

    Please consider breaking into smaller PRs to avoid significant review delays. Ignore if this PR has naturally grown to this size after reviews.
    `;

    await github.rest.issues.createComment({
      owner: context.repo.owner,
      repo: context.repo.repo,
      body: msg,
      issue_number: PR_NUMBER,
    });
}
