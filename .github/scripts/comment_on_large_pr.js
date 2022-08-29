const {
  PR_NUMBER,
  PR_ACTION,
  PR_AUTHOR,
  IGNORE_AUTHORS,
} = require("./constants")


/**
 * Notify PR author to split XXL PR in smaller chunks
 *
 * @param {object} core - core functions instance from @actions/core
 * @param {object} gh_client - Pre-authenticated REST client (Octokit)
 * @param {string} owner - GitHub Organization
 * @param {string} repository - GitHub repository
 */
const notifyAuthor = async ({
  core,
  gh_client,
  owner,
  repository,
}) => {
    core.info(`Commenting on PR ${PR_NUMBER}`)

    let msg = `### ⚠️Large PR detected⚠️

Please consider breaking into smaller PRs to avoid significant review delays. Ignore if this PR has naturally grown to this size after reviews.
    `;

    try {
      await gh_client.rest.issues.createComment({
        owner: owner,
        repo: repository,
        body: msg,
        issue_number: PR_NUMBER,
      });
    } catch (error) {
      core.setFailed("Failed to notify PR author to split large PR");
      console.error(err);
    }
}

module.exports = async ({github, context, core}) => {
    if (IGNORE_AUTHORS.includes(PR_AUTHOR)) {
      return core.notice("Author in IGNORE_AUTHORS list; skipping...")
    }

    if (PR_ACTION != "labeled") {
      return core.notice("Only run on PRs labeling actions; skipping")
    }


    /** @type {string[]} */
    const { data: labels } = await github.rest.issues.listLabelsOnIssue({
      owner: context.repo.owner,
      repo: context.repo.repo,
      issue_number: PR_NUMBER,
    })

    // Schema: https://docs.github.com/en/rest/issues/labels#list-labels-for-an-issue
    for (const label of labels) {
      core.info(`Label: ${label}`)
      if (label.name == "size/XXL") {
        await notifyAuthor({
          core: core,
          gh_client: github,
          owner: context.repo.owner,
          repository: context.repo.repo,
        })
        break;
      }
    }
}
