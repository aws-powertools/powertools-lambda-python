module.exports = async ({github, context, core}) => {
    const fs = require('fs');
    const filename = "pr.txt";

    try {
        core.debug("Payload as it comes..");
        core.debug(context.payload);
        fs.writeFileSync(`./${filename}`, JSON.stringify(context.payload));

        return `PR successfully saved ${filename}`
    } catch (err) {
        core.setFailed("Failed to save PR details");
        console.error(err);
    }
}