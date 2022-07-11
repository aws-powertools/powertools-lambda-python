module.exports = async ({github, context, core}) => {
    const fs = require('fs');
    core.debug(context.payload);

    core.info("Parsing previously saved PR");
    const pr = JSON.parse(fs.readFileSync('./pr.txt', 'utf-8').trim());
    core.info("Exporting outputs from PR");

    core.setOutput("prNumber", pr.number);
    core.setOutput("prTitle", pr.pull_request.title);
    core.setOutput("prBody", pr.pull_request.body);
    core.setOutput("prAuthor", pr.pull_request.user.login);
    core.setOutput("prAction", pr.action);
    core.setOutput("prIsMerged", pr.pull_request.merged);

    // set result as PR object so any workflow could use it
    return pr;
}