const { PR_NUMBER, PR_TITLE } = require("./constants")

module.exports = async ({github, context, core}) => {
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

	  const areas = [
	  	"tracer",
	  	"metric",
	  	"utilities",
	  	"logger",
	  	"event_handlers",
	  	"middleware_factory",
	  	"idempotency",
	  	"event_sources",
	  	"feature_flags",
	  	"parameters",
	  	"batch",
	  	"parser",
	  	"validator",
	  	"jmespath_util",
	  	"lambda-layers",
	  ];

    // Maintenance: We should keep track of modified PRs in case their titles change
    let miss = 0;
    try {
        for (const label in labels) {
            const matcher = new RegExp(labels[label])
            const isMatch = matcher.exec(PR_TITLE)
            if (isMatch != null) {
                core.info(`Auto-labeling PR ${PR_NUMBER} with ${label}`)

                await github.rest.issues.addLabels({
                    issue_number: PR_NUMBER,
                    owner: context.repo.owner,
                    repo: context.repo.repo,
                    labels: [label]
                })

                const area = matches[2]; // second capture group contains the area
                if (areas.indexOf(area) > -1) {
                    core.info(`Auto-labeling PR ${PR_NUMBER} with area ${area}`);
                    await github.rest.issues.addLabels({
                        issue_number: PR_NUMBER,
                        owner: context.repo.owner,
                        repo: context.repo.repo,
                        labels: [`area/${area}`],
                    });
                } else {
                    core.debug(`'${PR_TITLE}' didn't match any known area.`);
                }

                return;
            } else {
                core.debug(`'${PR_TITLE}' didn't match '${label}' semantic.`)
                miss += 1
            }
        }
    } finally {
        if (miss == Object.keys(labels).length) {
            return core.notice(`PR ${PR_NUMBER} title '${PR_TITLE}' doesn't follow semantic titles; skipping...`)
        }
    }
}
