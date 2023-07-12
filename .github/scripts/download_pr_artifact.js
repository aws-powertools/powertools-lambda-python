module.exports = async ({github, context, core}) => {
    const fs = require('fs');

    const workflowRunId = process.env.WORKFLOW_ID;
    core.info(`Listing artifacts for workflow run ${workflowRunId}`);

    const artifacts = await github.rest.actions.listWorkflowRunArtifacts({
      owner: context.repo.owner,
      repo: context.repo.repo,
      run_id: workflowRunId,
    });

    const matchArtifact = artifacts.data.artifacts.filter(artifact => artifact.name == "pr")[0];

    core.info(`Downloading artifacts for workflow run ${workflowRunId}`);
    const artifact = await github.rest.actions.downloadArtifact({
      owner: context.repo.owner,
      repo: context.repo.repo,
      artifact_id: matchArtifact.id,
      archive_format: 'zip',
    });

    core.info("Saving artifact found", artifact);

    fs.writeFileSync('pr.zip', Buffer.from(artifact.data));
}
