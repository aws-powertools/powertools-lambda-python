module.exports = async ({github, context, core}) => {
    const prBody = process.env.PR_BODY;
    const prNumber = process.env.PR_NUMBER;
    const blockLabel = process.env.BLOCK_LABEL;
    const blockReasonLabel = process.env.BLOCK_REASON_LABEL;

    const RELATED_ISSUE_REGEX = /Issue number:[^\d\r\n]+(?<issue>\d+)/;

    const isMatch = RELATED_ISSUE_REGEX.exec(prBody);
    if (isMatch == null) {
        core.info(`No related issue found, maybe the author didn't use the template but there is one.`)

        let msg = "No related issues found. Please ensure there is an open issue related to this change to avoid significant delays or closure.";
        await github.rest.issues.createComment({
          owner: context.repo.owner,
          repo: context.repo.repo,
          body: msg,
          issue_number: prNumber,
        });

        return await github.rest.issues.addLabels({
          issue_number: prNumber,
          owner: context.repo.owner,
          repo: context.repo.repo,
          labels: [blockLabel, blockReasonLabel]
        })
    }
}
