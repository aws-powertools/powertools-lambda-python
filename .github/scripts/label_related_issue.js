module.exports = async ({github, context}) => {
    const prBody = context.payload.body;
    const prNumber = context.payload.number;
    const releaseLabel = process.env.RELEASE_LABEL;
    const maintainersTeam = process.env.MAINTAINERS_TEAM

    const RELATED_ISSUE_REGEX = /Issue number:.+(\d)/

    const matcher = new RegExp(RELATED_ISSUE_REGEX)
    const isMatch = matcher.exec(prBody)
    if (isMatch != null) {
        let relatedIssueNumber = isMatch[1]
        console.info(`Auto-labeling related issue ${relatedIssueNumber} for release`)

        return await github.rest.issues.addLabels({
          issue_number: relatedIssueNumber,
          owner: context.repo.owner,
          repo: context.repo.repo,
          labels: [releaseLabel]
        })
    } else {
      let msg = `${maintainersTeam} No related issues found. Please ensure '${releaseLabel}' label is applied before releasing.`;
      return await github.rest.issues.createComment({
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: msg,
        issue_number: prNumber,
      });
    }
}
