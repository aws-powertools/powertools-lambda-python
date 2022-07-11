module.exports = async ({github, context, core}) => {
    core.info(process.env);
    const fs = require('fs');

    const pr = JSON.parse(fs.readFileSync('./pr.txt', 'utf-8').trim());
    const prBody = pr.body;
    const prNumber = pr.number;
    const releaseLabel = process.env.RELEASE_LABEL;
    const maintainersTeam = process.env.MAINTAINERS_TEAM

    return "Temporarily..."

    const RELATED_ISSUE_REGEX = /Issue number:[^\d\r\n]+(?<issue>\d+)/;

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
