module.exports = async ({github, context, core}) => {
    const pr_number = process.env.PR_NUMBER
    const pr_title = process.env.PR_TITLE

    console.log(pr_title)

    const FEAT_REGEX = /feat(\((.+)\))?(\:.+)/
    const BUG_REGEX = /(fix|bug)(\((.+)\))?(\:.+)/
    const DOCS_REGEX = /(docs|doc)(\((.+)\))?(\:.+)/
    const CHORE_REGEX = /(chore)(\((.+)\))?(\:.+)/
    const DEPRECATED_REGEX = /(deprecated)(\((.+)\))?(\:.+)/
    const REFACTOR_REGEX = /(refactor)(\((.+)\))?(\:.+)/

    const labels = {
        "feature": FEAT_REGEX,
        "bug": BUG_REGEX,
        "documentation": DOCS_REGEX,
        "internal": CHORE_REGEX,
        "enhancement": REFACTOR_REGEX,
        "deprecated": DEPRECATED_REGEX,
    }

    for (const label in labels) {
        const matcher = new RegExp(labels[label])
        const isMatch = matcher.exec(pr_title)
        if (isMatch != null) {
            console.info(`Auto-labeling PR ${pr_number} with ${label}`)

            await github.rest.issues.addLabels({
            issue_number: pr_number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            labels: [label]
            })

            break
        }
    }
}