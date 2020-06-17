import "./src/styles/global.css"
import Amplify from 'aws-amplify';
import { Analytics, AWSKinesisFirehoseProvider } from '@aws-amplify/analytics';
import awsconfig from './src/config';

export const onRouteUpdate = ({ location, prevLocation }) => {
    Analytics.record({
        data: {
            url: window.location.href,
            section: location.pathname,
            previous: prevLocation ? prevLocation.pathname : null
        },
        streamName: awsconfig.aws_kinesis_firehose_stream_name
    }, 'AWSKinesisFirehose')
}

export const onClientEntry = () => {
    Analytics.addPluggable(new AWSKinesisFirehoseProvider());
    Amplify.configure(awsconfig);

    Analytics.configure({
        AWSKinesisFirehose: {
            region: awsconfig.aws_project_region
        }
    });
}
