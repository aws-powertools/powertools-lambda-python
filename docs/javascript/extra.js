const Amplify = window.aws_amplify.Amplify
const Analytics = Amplify.Analytics
const KinesisFirehoseProvider = window.aws_amplify.AWSKinesisFirehoseProvider

const awsconfig = {
	"aws_project_region": "eu-west-1",
	"aws_cognito_identity_pool_id": "eu-west-1:3df3caec-4bb6-4891-b154-ee940c8264b8",
	"aws_cognito_region": "eu-west-1",
	"aws_kinesis_firehose_stream_name": "ClickStreamKinesisFirehose-OGX7PQdrynUo",
};

const RUNTIME = "python"

const attachListeners = () => {
	/* Register handler to log search on blur */
	document.addEventListener("DOMContentLoaded", function () {
		recordPageView({
			prevLocation: document.referrer
		})
		if (document.forms.search) {
			let query = document.forms.search.query
			query.addEventListener("blur", function () {
				// If Search result is ever actionable
				// we should populate `value`
				if (this.value) {
					let path = document.location.pathname;
					console.info(`Search value: ${this.value}`)
					recordPageView({
						searchPattern: this.value
					})
				}
			})
		}
	})

	// Register handler for page sections when browser history is changed
	window.onpopstate = function (event) {
		recordPageView({
			prevLocation: document.referrer
		})
	};
}

const init = () => {
	Analytics.addPluggable(new KinesisFirehoseProvider())
	Amplify.configure(awsconfig);

	Analytics.configure({
		AWSKinesisFirehose: {
			region: awsconfig.aws_project_region
		}
	})

	attachListeners()
}

const recordPageView = ({prevLocation, searchPattern}) => {
	Analytics.record({
		data: {
			// Do not count page view for search
			url: searchPattern ? null : window.location.href,
			section: searchPattern ? null : location.pathname,
			previous: prevLocation || null,
			search: searchPattern || null,
			language: RUNTIME
		},
		streamName: awsconfig.aws_kinesis_firehose_stream_name
	}, 'AWSKinesisFirehose')
}

init()
