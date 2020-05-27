module.exports = {
    pathPrefix: '',
    siteMetadata: {
        title: 'AWS Lambda Powertools Python',
        description: 'A suite of utilities for AWS Lambda Functions that makes tracing with AWS X-Ray, structured logging and creating custom metrics asynchronously easier',
        author: `Amazon Web Services`,
        siteName: 'AWS Lambda Powertools Python',
        siteUrl: 'https://awslabs.github.io/aws-lambda-powertools-python'
    },
    plugins: [
        {
            resolve: 'gatsby-theme-apollo-docs',
            options: {
                root: __dirname,
                menuTitle: 'Helpful resources',
                githubRepo: 'awslabs/aws-lambda-powertools-python',
                baseUrl: 'https://awslabs.github.io/aws-lambda-powertools-python',
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
                    'Serverless Best Practices video': {
                        url: 'https://www.youtube.com/watch?v=9IYpGTS7Jy0',
                        description: 'AWS re:Invent ARC307: Serverless architectural patterns & best practices - Origins of Powertools',
                    },
                    'AWS Well-Architected Serverless Lens': {
                        url: 'https://d1.awsstatic.com/whitepapers/architecture/AWS-Serverless-Applications-Lens.pdf',
                        description: 'AWS Well-Architected Serverless Applications Lens whitepaper',
                    },
                    'Amazon Builders Library': {
                        url: 'https://aws.amazon.com/builders-library/',
                        description: 'Collection of living articles covering topics across architecture, software delivery, and operations'
                    },
                    'AWS CDK Patterns': {
                        url: 'https://cdkpatterns.com/patterns/',
                        description: "CDK Patterns maintained by Matt Coulter (@nideveloper)"
                    }
                },
                footerNavConfig: {
                    API: {
                        href: 'https://aws.amazon.com/serverless/'
                    },
                    Serverless: {
                        href: 'https://aws.amazon.com/serverless/'
                    },
                    'AWS SAM Docs': {
                        href: 'https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html',
                    },
                    'AWS Serverless Application Architecture Review': {
                        href: 'https://console.aws.amazon.com/wellarchitected/home'
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
