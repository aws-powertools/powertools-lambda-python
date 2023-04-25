const {
  PR_ACTION,
  PR_AUTHOR,
  PR_BODY,
  PR_NUMBER,
  IGNORE_AUTHORS,
  LABEL_BLOCK,
  LABEL_BLOCK_MISSING_LICENSE_AGREEMENT
} = require("./constants")

module.exports = async ({github, context, core}) => {
    if (IGNORE_AUTHORS.includes(PR_AUTHOR)) {
      return core.notice("Author in IGNORE_AUTHORS list; skipping...")
    }

    if (PR_ACTION != "opened") {
      return core.notice("Only newly open PRs are labelled to avoid spam; skipping")
    }

    const RELATED_ACK_SECTION_REGEX = /By submitting this pull request, I confirm that you can use, modify, copy, and redistribute this contribution, under the terms of your choice./;

    const isMatch = RELATED_ACK_SECTION_REGEX.exec(PR_BODY);
    if (isMatch == null) {
        core.info(`No acknowledgement section found, maybe the author didn't use the template but there is one.`)

        let msg = "No acknowledgement section found. Please make sure you used the template to open a PR and didn't remove the acknowledgment section. Check the template here: https://github.com/awslabs/aws-lambda-powertools-python/blob/develop/.github/PULL_REQUEST_TEMPLATE.md#acknowledgment";
        await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          body: msg,
          issue_number: PR_NUMBER,
        });

        return await github.rest.issues.addLabels({
          issue_number: PR_NUMBER,
          owner: context.repo.owner,
          repo: context.repo.repo,
          labels: [LABEL_BLOCK, LABEL_BLOCK_MISSING_LICENSE_AGREEMENT]
        })
    }
}
