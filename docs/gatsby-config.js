module.exports = {
    pathPrefix: '/docs',
    siteMetadata: {
        title: 'AWS Lambda Powertools Python',
        description: 'A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier',
        author: `Amazon Web Services`,
        siteName: 'AWS Lambda Powertools Python'
    },
    plugins: [
        {
            resolve: 'gatsby-theme-apollo-docs',
            options: {
                root: __dirname,
                menuTitle: 'AWS Lambda Powertools',
                githubRepo: 'awslabs/aws-lambda-powertools-python',
                sidebarCategories: {
                    null: [
                        'index'
                    ],
                    'Core utilities': [
                        'core/tracer',
                        'core/logger',
                        'core/metrics'
                    ],
                    'Utilities': [
                        'utilities/middleware_factory',
                    ],
                },
                navConfig: {
                    'AWS Serverless': {
                        url: 'https://aws.amazon.com/serverless/',
                        description: 'AWS Serverless homepage',
                    },
                    'AWS Well-Architected Serverless Lens': {
                        url: 'https://d1.awsstatic.com/whitepapers/architecture/AWS-Serverless-Applications-Lens.pdf',
                        description: 'AWS Well-Architected Serverless Applications Lens whitepaper',
                    },
                    'AWS Serverless Application Model (SAM)': {
                        url: 'https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html',
                        description: "AWS SAM docs"
                    }
                },
                footerNavConfig: {
                    Website: {
                        href: 'https://aws.amazon.com/architecture/well-architected/'
                    },
                    'Intro to Well-Architected': {
                        href: 'https://www.youtube.com/watch?v=gjNPpjYNiow'
                    }
                }                
            }
        },
        {
            resolve: `gatsby-plugin-catch-links`,
            options: {
                excludePattern: /(excluded-link|external)/,
            },
        },
        'gatsby-plugin-antd',
        'gatsby-remark-autolink-headers',
        'gatsby-plugin-offline',
        'gatsby-plugin-sitemap'
    ]
};
