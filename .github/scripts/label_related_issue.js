const {
  PR_AUTHOR,
  PR_BODY,
  PR_NUMBER,
  IGNORE_AUTHORS,
  LABEL_PENDING_RELEASE,
  HANDLE_MAINTAINERS_TEAM,
  PR_IS_MERGED,
} = require("./constants")

module.exports = async ({github, context, core}) => {
    if (IGNORE_AUTHORS.includes(PR_AUTHOR)) {
      return core.notice("Author in IGNORE_AUTHORS list; skipping...")
    }

    if (PR_IS_MERGED == "false") {
      return core.notice("Only merged PRs to avoid spam; skipping")
    }

    const RELATED_ISSUE_REGEX = /Issue number:[^\d\r\n]+(?<issue>\d+)/;

    const isMatch = RELATED_ISSUE_REGEX.exec(PR_BODY);

    try {
      if (!isMatch) {
        core.setFailed(`Unable to find related issue for PR number ${PR_NUMBER}.\n\n Body details: ${PR_BODY}`);
        return await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          body: `${HANDLE_MAINTAINERS_TEAM} No related issues found. Please ensure '${LABEL_PENDING_RELEASE}' label is applied before releasing.`,
          issue_number: PR_NUMBER,
        });
      }
    } catch (error) {
      core.setFailed(`Unable to create comment on PR number ${PR_NUMBER}.\n\n Error details: ${error}`);
      throw new Error(error);
    }

    const { groups: {issue} } = isMatch

    try {
      core.info(`Auto-labeling related issue ${issue} for release`)
      return await github.rest.issues.addLabels({
        issue_number: issue,
        owner: context.repo.owner,
        repo: context.repo.repo,
        labels: [LABEL_PENDING_RELEASE]
      })
    } catch (error) {
      core.setFailed(`Is this issue number (${issue}) valid? Perhaps a discussion?`);
      throw new Error(error);
    }
}
