module.exports = async ({github, context, core}) => {
    const prBody = process.env.PR_BODY;
    const prNumber = process.env.PR_NUMBER;
    const releaseLabel = process.env.RELEASE_LABEL;
    const maintainersTeam = process.env.MAINTAINERS_TEAM;
    const RELATED_ISSUE_REGEX = /Issue number:[^\d\r\n]+(?<issue>\d+)/;

    core.info(prBody);
    const isMatch = RELATED_ISSUE_REGEX.exec(prBody);
    if (!isMatch) {
      core.setFailed(`Unable to find related issue for PR number ${prNumber}.\n\n Body details: ${prBody}`);
      return await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `${maintainersTeam} No related issues found. Please ensure '${releaseLabel}' label is applied before releasing.`,
        issue_number: prNumber,
      });
    }

    const { groups: {relatedIssueNumber} } = isMatch

    core.info(`Auto-labeling related issue ${relatedIssueNumber} for release`)
    return await github.rest.issues.addLabels({
      issue_number: relatedIssueNumber,
      owner: context.repo.owner,
      repo: context.repo.repo,
      labels: [releaseLabel]
    })
}
