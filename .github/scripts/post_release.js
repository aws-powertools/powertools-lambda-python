const STAGED_LABEL = "pending-release";

/**
 * Fetch issues using GitHub REST API
 *
 * @param {object} gh_client - Pre-authenticated REST client (Octokit)
 * @param {string} org - GitHub Organization
 * @param {string} repository - GitHub repository
 * @param {string} state - GitHub issue state (open, closed)
 * @param {string} label - Comma-separated issue labels to fetch
 * @return {Object[]} issues - Array of issues matching params
 * @see {@link https://octokit.github.io/rest.js/v18#usage|Octokit client}
 */
const fetchIssues = async ({
	gh_client,
	org,
	repository,
	state = "all",
	label = STAGED_LABEL,
}) => {

	try {
		const { data: issues } = await gh_client.rest.issues.listForRepo({
			owner: org,
			repo: repository,
			state: state,
			labels: label,
		});

		return issues;

	} catch (error) {
		console.error(error);
		throw new Error("Failed to fetch issues")
	}

};

/**
 * Notify new release and close staged GitHub issue
 *
 * @param {object} gh_client - Pre-authenticated REST client (Octokit)
 * @param {string} owner - GitHub Organization
 * @param {string} repository - GitHub repository
 * @param {string} release_version - GitHub Release version
 * @see {@link https://octokit.github.io/rest.js/v18#usage|Octokit client}
 */
const notifyRelease = async ({
	gh_client,
	owner,
	repository,
	release_version,
}) => {
	const release_url = `https://github.com/${owner}/${repository}/releases/tag/v${release_version}`;

	const issues = await fetchIssues({
		gh_client: gh_client,
		org: owner,
		repository: repository,
	});

	issues.forEach(async (issue) => {
		console.info(`Updating issue number ${issue.number}`);

		const comment = `This is now released under [${release_version}](${release_url}) version!`;
		try {
			await gh_client.rest.issues.createComment({
				owner: owner,
				repo: repository,
				body: comment,
				issue_number: issue.number,
			});
		} catch (error) {
			console.error(error);
			throw new Error(`Failed to update issue ${issue.number} about ${release_version} release`)
		}


		// Close issue and remove staged label; keep existing ones
		const labels = issue.labels
			.filter((label) => label.name != STAGED_LABEL)
			.map((label) => label.name);

		try {
			await gh_client.rest.issues.update({
				repo: repository,
				owner: owner,
				issue_number: issue.number,
				state: "closed",
				labels: labels,
			});
		} catch (error) {
			console.error(error);
			throw new Error("Failed to close issue")
		}

		console.info(`Issue number ${issue.number} closed and updated`);
	});
};

// context: https://github.com/actions/toolkit/blob/main/packages/github/src/context.ts
module.exports = async ({ github, context }) => {
	const { RELEASE_VERSION } = process.env;
	console.log(`Running post-release script for ${RELEASE_VERSION} version`);

	await notifyRelease({
		gh_client: github,
		owner: context.repo.owner,
		repository: context.repo.repo,
		release_version: RELEASE_VERSION,
	});
};
