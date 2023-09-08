module.exports = async ({github, context, core}) => {
    const fs = require('fs');
    const filename = "pr.txt";

    const labelsData = await github.rest.issues.listLabelsOnIssue({
        owner: context.repo.owner,
        repo: context.repo.repo,
        issue_number: (context.payload.issue || context.payload.pull_request || context.payload).number,
    });

    const labels = labelsData.data.map((label) => {
    	return label['name'];
    });

    try {
        fs.writeFileSync(`./${filename}`, JSON.stringify({...context.payload, ...{labels:labels.join(",")}}));

        return `PR successfully saved ${filename}`
    } catch (err) {
        core.setFailed("Failed to save PR details");
        console.error(err);
    }
}
