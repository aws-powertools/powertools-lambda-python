function getVersionBasePath(version) {
    return `/v${version.replace(/\s+/g, '-')}`;
}

exports.getVersionBasePath = getVersionBasePath;
exports.HEADER_HEIGHT = 72;
