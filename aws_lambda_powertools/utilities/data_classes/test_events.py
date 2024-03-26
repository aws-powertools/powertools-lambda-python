# kinesis stream -> firehose -> s3 -> lambda: not working ie the event generated is just s3, nothing is nested...

# s3 -> sns -> firehose -> lambda: sns not sending messages to firehose for some reason :(
# working -> ?? -> working? i see test data in CW


# ses -> sns -> lambda = sns(ses)
sns_ses_event = {
  "Records": [
    {
      "EventSource": "aws:sns",
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:us-east-1:683517028648:ses-sns:a2059001-6ef2-4d4d-a6b8-5c3717210c15",
      "Sns": {
        "Type": "Notification",
        "MessageId": "14cc1773-477c-51e2-8b02-490f43dd19a3",
        "TopicArn": "arn:aws:sns:us-east-1:683517028648:ses-sns",
        "Subject": "Amazon SES Email Event Notification",
        "Message": "{\"eventType\":\"Send\",\"mail\":{\"timestamp\":\"2024-03-25T23:01:53.733Z\",\"source\":\"seshub@amazon.com\",\"sourceArn\":\"arn:aws:ses:us-east-1:683517028648:identity/seshub@amazon.com\",\"sendingAccountId\":\"683517028648\",\"messageId\":\"0100018e77d94dc5-c421e265-f034-4575-9ecc-3ca34038e91f-000000\",\"destination\":[\"success@simulator.amazonses.com\"],\"headersTruncated\":false,\"headers\":[{\"name\":\"From\",\"value\":\"seshub@amazon.com\"},{\"name\":\"To\",\"value\":\"success@simulator.amazonses.com\"},{\"name\":\"Subject\",\"value\":\"subject test from ses!!!!\"},{\"name\":\"MIME-Version\",\"value\":\"1.0\"},{\"name\":\"Content-Type\",\"value\":\"multipart/alternative;  boundary=\\\"----=_Part_467214_1288460597.1711407713733\\\"\"}],\"commonHeaders\":{\"from\":[\"seshub@amazon.com\"],\"to\":[\"success@simulator.amazonses.com\"],\"messageId\":\"0100018e77d94dc5-c421e265-f034-4575-9ecc-3ca34038e91f-000000\",\"subject\":\"subject test from ses!!!!\"},\"tags\":{\"ses:source-tls-version\":[\"TLSv1.3\"],\"ses:operation\":[\"SendEmail\"],\"ses:configuration-set\":[\"my-first-configuration-set\"],\"ses:source-ip\":[\"15.248.7.48\"],\"ses:from-domain\":[\"amazon.com\"],\"ses:caller-identity\":[\"Admin\"]}},\"send\":{}}\n",
        "Timestamp": "2024-03-25T23:01:53.935Z",
        "SignatureVersion": "1",
        "Signature": "DRfrfPLo2KTGw/GweWUe2uGgK8jhwac1OQQq1HJ3Bo7HFEBDp4c6AjUyoYAGQYzKskxXSJBYJyrj9B3WOU7OPisM/b7+eLWjtRNohIM5B/yzrveQRV8W4GwjX0JpdC247VZB9Z01D+M01kVYVwiOO50lS/kpLrAnGksrdmGnF2Z2FQuh6mh8bCpQgoz1xTXUF94hqR6Tuj2R+bYNWxkCEZ18rg8FgrQfaonxiM/R5J1CjMW8P8KAP4nSdeBUAgFBXG8W72V1gSbjIH7a4uOyGZfFPooQZ4EUd9/eC6VlcxvjwwVmy0/x5oE2mHDU/s7NulOafTKTTA/V4/xFp6yqbQ==",
        "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
        "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:683517028648:ses-sns:a2059001-6ef2-4d4d-a6b8-5c3717210c15",
        "MessageAttributes": {}
      }
    }
  ]
}


# s3 -> eventbridge -> sqs -> lambda = sqs(eventbridge(s3))
sqs_eb_s3_event = {
  "Records": [
    {
      "messageId": "ee95829a-ba32-471d-9684-34368ab9995e",
      "receiptHandle": "AQEBZoMhwYaEfxvSOWGnwMurMIe2sEkwsV9l5e+pDpa2zCtdWLBfbUNxIX5R8O9hx+jAXhpj01bHElvli+LtPNBJarb4V+JEg2Hql3lSdkISTEECrWc8Dm8eX+p+LeyoN9cSnfDUoqQ2rd/BSFt9/vk6ro+w/kM8G1q7Lt1PB6G51LbfzXYA+KYUPLWIeYK2NMDf8TyvC0PbERE6im9H+eqJznyPWNznfziwq7d6ZIpY3GSfRrED/0tfr3FvzIVCVsOBuPHyd5stqcrgkCs2Dt/f7DWYWr1KMSqFDM1u4S7wMIroCVSfe9wsqimLBwaHZcG1zukaW16c51TiRI3zNzOl3cuDZgqPAK1rQKsj3x+VLqxnbyIgx24oIKhh5XqcZfzRbBwX4HDF/Opv8cN16+0yTw==",
      "body": "{\"version\":\"0\",\"id\":\"75012ec5-af4a-7e39-2dd4-a28b7bb8cde4\",\"detail-type\":\"Object Created\",\"source\":\"aws.s3\",\"account\":\"683517028648\",\"time\":\"2024-03-26T18:05:54Z\",\"region\":\"us-east-1\",\"resources\":[\"arn:aws:s3:::s3-eb-unwrap-sourcebucket-7mop1gqlyrzu\"],\"detail\":{\"version\":\"0\",\"bucket\":{\"name\":\"s3-eb-unwrap-sourcebucket-7mop1gqlyrzu\"},\"object\":{\"key\":\"__init__.py\",\"size\":0,\"etag\":\"d41d8cd98f00b204e9800998ecf8427e\",\"sequencer\":\"0066030E82E2A48DFE\"},\"request-id\":\"HWEZ4KKQMXVWATHJ\",\"requester\":\"683517028648\",\"source-ip-address\":\"15.248.7.0\",\"reason\":\"PutObject\"}}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1711476356070",
        "SenderId": "AIDAJXNJGGKNS7OSV23OI",
        "ApproximateFirstReceiveTimestamp": "1711476356085"
      },
      "messageAttributes": {},
      "md5OfBody": "3fc2529293127eb705317a37dca18ef4",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:683517028648:s3-eb-sqs-unwrap",
      "awsRegion": "us-east-1"
    }
  ]
}



# s3 -> eventbridge -> lambda = eventbridge(s3)
eb_s3_event = {
  "version": "0",
  "id": "78eac3e6-798f-c27e-49ec-bbe3be7bab7d",
  "detail-type": "Object Created",
  "source": "aws.s3",
  "account": "683517028648",
  "time": "2024-03-20T23:56:16Z",
  "region": "us-east-1",
  "resources": [
    "arn:aws:s3:::s3-eb-unwrap-sourcebucket-7mop1gqlyrzu"
  ],
  "detail": {
    "version": "0",
    "bucket": {
      "name": "s3-eb-unwrap-sourcebucket-7mop1gqlyrzu"
    },
    "object": {
      "key": "s3-eb-template.yaml",
      "size": 1565,
      "etag": "e56e21b1610dd94e9907f82b8d05b934",
      "sequencer": "0065FB77A03AD4478F"
    },
    "request-id": "SW5MRVMJG8NG1GMZ",
    "requester": "683517028648",
    "source-ip-address": "72.21.198.69",
    "reason": "PutObject"
  }
}


# in unwrap CF stack: s3 -> sns -> sqs -> lambda = sqs(sns(s3))
sqs_sns_s3_event = {
  "Records": [
    {
      "messageId": "45405be4-2278-4eef-a29c-993898bb8917",
      "receiptHandle": "AQEBy2gRrluag0E0vWiKlHZhcf6Ymtgkf92PlWtTQ4PKOPdF3NcUqKEzKtKbiTN7d+qy64nN3F97DOQr9b4xegJidHlXlyIwsYxQIpmGfDETCKPS5nchXOWRLIu/a/bpCmaZK/Mv1r6lAaF2gnoX7JaVpdTbExLRBQqOIcb2NRXmfeE0yKZtIT0TV9pstzsAi328KGbr1QMKOV0RKrE1NtQDpa/ixeEUWrZeGqwA7Cwy0BMevfoQKVkO78JrDsn4W/lUt2R+oRF7sB62+onfbIlBPmi+LXV4WeSrB7w1yvnMbVuvfgHDS9F1LEs62wJTNVQz6224s3OBfJZsAaSpW1IzD+UttqFJ3KTadu6HZMbCq+I2An+cQjqZ3zDsEV7Vwm6LH+04RGA3b9edBLgIoMbfcg==",
      "body": "{\n  \"Type\" : \"Notification\",\n  \"MessageId\" : \"53c941f5-1d7a-5f8e-8ffe-1f8110f6e667\",\n  \"TopicArn\" : \"arn:aws:sns:us-west-2:683517028648:unwraptestevents-Topic-qit16u4t71Op\",\n  \"Subject\" : \"Amazon S3 Notification\",\n  \"Message\" : \"{\\\"Records\\\":[{\\\"eventVersion\\\":\\\"2.1\\\",\\\"eventSource\\\":\\\"aws:s3\\\",\\\"awsRegion\\\":\\\"us-west-2\\\",\\\"eventTime\\\":\\\"2024-03-19T22:01:47.135Z\\\",\\\"eventName\\\":\\\"ObjectCreated:Put\\\",\\\"userIdentity\\\":{\\\"principalId\\\":\\\"AWS:AROAZ6JGKFEUJYDMQOGIU:seshub-Isengard\\\"},\\\"requestParameters\\\":{\\\"sourceIPAddress\\\":\\\"205.251.233.178\\\"},\\\"responseElements\\\":{\\\"x-amz-request-id\\\":\\\"02TFARRDG75KXGG6\\\",\\\"x-amz-id-2\\\":\\\"ZUztk9/z3GbDxV5zE9Q8sN0Hg4LG7axcMUgZ2DWj/bXr2NY5zwFTB6kx2GDHiFtkcejqGJPlbOyWTrwZ0V5P8oHD6b3oS6eF\\\"},\\\"s3\\\":{\\\"s3SchemaVersion\\\":\\\"1.0\\\",\\\"configurationId\\\":\\\"NDE4Zjk0NmMtMTVlMi00ZWNhLWI1NDktYjg0YzBmMzVkYjQx\\\",\\\"bucket\\\":{\\\"name\\\":\\\"unwraptestevents-bucket-683517028648\\\",\\\"ownerIdentity\\\":{\\\"principalId\\\":\\\"A2RRIR5BTZTTF6\\\"},\\\"arn\\\":\\\"arn:aws:s3:::unwraptestevents-bucket-683517028648\\\"},\\\"object\\\":{\\\"key\\\":\\\"firehose-s3-template.json\\\",\\\"size\\\":4314,\\\"eTag\\\":\\\"e77dffcd1756d6e8e5123ef1e0ce7c54\\\",\\\"sequencer\\\":\\\"0065FA0B4B104A6DAB\\\"}}}]}\",\n  \"Timestamp\" : \"2024-03-19T22:01:48.137Z\",\n  \"SignatureVersion\" : \"1\",\n  \"Signature\" : \"cVaCtWT+JsLsnXrSRHlBPXKPqPIlEWQaCeecWXme5XoDbHYtDV58i8DHLHAcVjp+G5hmg7FxSjr9notzP4WLtgfMuqbsY0JjaSLl5Yo3dWZIOYgUgTqNj5RupPowbyjoywCUBluKYMduEIJ8ozFU0GdBWfCfcGrj89nUUjmrCn3zt8rTghRL4bT8fQWRhU9q9hKmMjPcSpe57T1Sf2k/LUu52L1bK89pVARA/nfV5nykbF4a4opjIYtSzSP2/COvXgb/8I2bbzlyOmAi8O5tEL4TkDx717o67565/7bbVA8UyuAcXL6VCdQfiI5U+dHdJdkWAWW4g/rEhvCBNW9PzA==\",\n  \"SigningCertURL\" : \"https://sns.us-west-2.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem\",\n  \"UnsubscribeURL\" : \"https://sns.us-west-2.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-west-2:683517028648:unwraptestevents-Topic-qit16u4t71Op:90710d0d-3c29-4b4b-aebc-e0622e295dea\"\n}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1710885708191",
        "SenderId": "AIDAIYLAVTDLUXBIEIX46",
        "ApproximateFirstReceiveTimestamp": "1710885708202"
      },
      "messageAttributes": {},
      "md5OfBody": "2dfc1cc4f8f1240a50d7cdc65c7dd2b3",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-west-2:683517028648:SQSQueue1",
      "awsRegion": "us-west-2"
    }
  ]
}

# s3 -> raw_sns -> sqs -> lambda = sqs(raw_sns(s3))
sqs_rawsns_s3_event = {
  "Records": [
    {
      "messageId": "519619da-e529-46d7-b58c-bc054405af0f",
      "receiptHandle": "AQEB//A8ci4+iToNBE66jNulMi/7cpVqiC7YkdTnQA0qhTOnWv55SDgxh+CV7WckD1xT3V9zBh2APTr1qtB7i29GepU/lzqFvS2wozjDljP7YHbWHn77hOeCwtfVFbJoqUyEL/+QcFIMZ06AUP0h+SAjJDype/x0WnCGqKd3juaRmECEk4LFc+g1evZ9DIP+Lkw3JM44JHAcgq4+Sm+Pv/dEZXHIoOL8S5mV4f0l+fJk9TDOLGbTCCEuMfWmrQBAVgJt052y0y6my2rAGO2iQdwkONXdPUrbxBSmeb/sDEp4qy4CViKgDzTo+Ii2sLDggKxeRrWaLzdFvv50ebTnLx8RHUsVnAiNv8DsJJOJx3ryw8gKO0o4TaMB8KQ4Zh2hAglgakSwjeMzCrTI7tyF1ML65A==",
      "body": "{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-west-2\",\"eventTime\":\"2024-03-19T22:57:48.823Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:AROAZ6JGKFEUJYDMQOGIU:seshub-Isengard\"},\"requestParameters\":{\"sourceIPAddress\":\"205.251.233.182\"},\"responseElements\":{\"x-amz-request-id\":\"HQDSXXWNQWRCN3PQ\",\"x-amz-id-2\":\"EVDoeOaTHawmKSqzPnBHMZNHvWnnHKfAl9Muyg21meD3KvREXeNTC9qdV6ZyJQs1hfKJ+sfUp5koqc3GeAziHnl0UQGDa3CF\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"NDE4Zjk0NmMtMTVlMi00ZWNhLWI1NDktYjg0YzBmMzVkYjQx\",\"bucket\":{\"name\":\"unwraptestevents-bucket-683517028648\",\"ownerIdentity\":{\"principalId\":\"A2RRIR5BTZTTF6\"},\"arn\":\"arn:aws:s3:::unwraptestevents-bucket-683517028648\"},\"object\":{\"key\":\"samconfig.toml\",\"size\":221,\"eTag\":\"9cc7da5febb07868706f59ab70d89981\",\"sequencer\":\"0065FA186CC08E810D\"}}}]}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1710889069948",
        "SenderId": "AIDAIYLAVTDLUXBIEIX46",
        "ApproximateFirstReceiveTimestamp": "1710889069955"
      },
      "messageAttributes": {},
      "md5OfBody": "94ff55fa8f439b3d2e43366d582de0b7",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-west-2:683517028648:SQSQueue1",
      "awsRegion": "us-west-2"
    }
  ]
}


# added more events in Records list: sqs(s3, s3)
sqs_s3_multi_event = {
  "Records": [
    {
      "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
      "receiptHandle": "MessageReceiptHandle",
      "body": "{\"Records\":[" +
        "{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2023-01-03T00:00:00.000Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:123456789012:example-user\"},\"requestParameters\":{\"sourceIPAddress\":\"127.0.0.1\"},\"responseElements\":{\"x-amz-request-id\":\"example-request-id-3\",\"x-amz-id-2\":\"example-id-3\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"testConfigRule\",\"bucket\":{\"name\":\"example-bucket11\",\"ownerIdentity\":{\"principalId\":\"EXAMPLE\"},\"arn\":\"arn:aws:s3:::example-bucket\"},\"object\":{\"key\":\"example-object-3.txt\",\"size\":3072,\"eTag\":\"example-tag-3\",\"versionId\":\"3\",\"sequencer\":\"example-sequencer-3\"}}}" +
      "]}"
    },
    {
      "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
      "receiptHandle": "MessageReceiptHandle",
      "body": "{\"Records\":[" +
        "{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2023-01-03T00:00:00.000Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:123456789012:example-user\"},\"requestParameters\":{\"sourceIPAddress\":\"127.0.0.1\"},\"responseElements\":{\"x-amz-request-id\":\"example-request-id-3\",\"x-amz-id-2\":\"example-id-3\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"testConfigRule\",\"bucket\":{\"name\":\"example-bucket22\",\"ownerIdentity\":{\"principalId\":\"EXAMPLE\"},\"arn\":\"arn:aws:s3:::example-bucket\"},\"object\":{\"key\":\"example-object-3.txt\",\"size\":3072,\"eTag\":\"example-tag-3\",\"versionId\":\"3\",\"sequencer\":\"example-sequencer-3\"}}}" +
      "]}"
    }
  ],
  "attributes": {
    "ApproximateReceiveCount": "1",
    "SentTimestamp": "1523232000000",
    "SenderId": "123456789012",
    "ApproximateFirstReceiveTimestamp": "1523232000001"
  },
  "messageAttributes": {},
  "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
  "eventSource": "aws:sqs",
  "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
  "awsRegion": "us-east-1"
}


#generated from lambda invoke s3 -> sqs -> lambda == sqs(s3)
sqs_s3_event = {
  "Records": [
    {
      "messageId": "44103047-3123-4583-aed3-7224000351a8",
      "receiptHandle": "AQEBWOm6hlP5TEZ64yvPugVI7LyhkEAvaEfvqfyqheIBcqhKPg5wfb95MC9IYm60od3hlTdgT3lJ7l/8upj8eYsCVglkTYqUKXKqUOgotxiqhyLlJ2AOy0gPc1EL5Uek3e267IB/5XPz9msqZmxuI6/pcT+Ihj/26EXYVxOYEK4YwbhbBNhl5Wp4dn8anV3/LD/vvgRyHtOAK4MlwWgIBFT9wWyJInMcYRVtmAx1ODUMG1CpsB6IB5m11pazNnlV0kOSzjjBDB4QK/euMqpfnCbUB4dLb5WAwZ37pys9xKjypEFS1eHXjSwEG+rG4J8u2UlFDO13FQ8lsOJB96Sx/T7KIqTvhc8VayDPXFArTtT6dlXZlc99gYf8uDDcYRfUPnBK8KZ/pEI6UjQiOVjvgWhIDiu0SxrQ82ytPMxjvizWkv0=",
      "body": "{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2024-03-14T19:02:45.087Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:AROAZ6JGKFEUJYDMQOGIU:seshub-Isengard\"},\"requestParameters\":{\"sourceIPAddress\":\"15.248.6.8\"},\"responseElements\":{\"x-amz-request-id\":\"ST581J3PW8R8QKVP\",\"x-amz-id-2\":\"bvl3TX3qzBFUe+/0IZNjrCdVI2GfhEAjJDg4G8JxVnT1MNNPlf/BckKG9cAGzenBbZLh72nKxg9KMqYg3+/tg4kpKFhWWi2h\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"NmIyMjczNmQtOTg4Ni00ZmMyLWIwNDctYzRmNWQ1NTk2NTlh\",\"bucket\":{\"name\":\"sqs-s3-unwrap-bucket-683517028648\",\"ownerIdentity\":{\"principalId\":\"A2RRIR5BTZTTF6\"},\"arn\":\"arn:aws:s3:::sqs-s3-unwrap-bucket-683517028648\"},\"object\":{\"key\":\"samconfig.toml\",\"size\":221,\"eTag\":\"8f6c039f567cc53694be2a275e452743\",\"sequencer\":\"0065F349D4F05B5827\"}}}]}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1710442966490",
        "SenderId": "AROA4R74ZO52XAB5OD7T4:S3-PROD-END",
        "ApproximateFirstReceiveTimestamp": "1710442966494"
      },
      "messageAttributes": {},
      "md5OfBody": "1b9d61fd8139b215ec65bd8916ac6872",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:683517028648:sqs-s3-unwrap-Queue-9H8CEZEhJfP7",
      "awsRegion": "us-east-1"
    }
  ]
}

# generated from invoking lambda with sns -> sqs -> lambda == sqs(sns)
# this does not have a Records key inside the SNS event, or the Sns key. But if SNS sends an event directly to Lambda
# (without having SQS in the middle), it would have a Records and Sns key. That's why it's failing
# even after being casted into a SNS event: it doesn't have a Records or Sns key
sqs_sns_event = {
  "Records": [
    {
      "messageId": "10ad507c-8389-4585-ae55-11d32ea71997",
      "receiptHandle": "AQEB1nupmCFCI3lhVKz3fPFqO5kZKDNpzuflQ96kZwseTe5HRCb3eeY8XoWoyfcSDqNwjXdC/CQBjunectuzr+0mYhwVvo0GxRWF0U1J8/djdoxCACEELa+IxnWYA+2ernXEVPrisgWSf8D+woy02h58ybMzbP8pCxeld/1cqbBOt7vd0QC7pRcXDdFl0KWl0yYi1PTWyy6L5uTz4RIDsL867eh6xtKxKinp/N2Fym5/0/3TkfDLk+RNTVTTMmiRebP7hKSfsmYeAc7tcx8GHRvJdcN11XDPfW76+uQbIb9DtAIQobpQ4sJ2FOAapJ9U5IJ4leTfWjJ+L/L1fKo+vlkWiv9k+ktP9ABP214ylpS8BVzn1dHjBGQ98pryKhE4jPm9J3SDYh/J3LSPxsjtUvF/p15pgvantoOYyobS7OMr9qM=",
      "body": "{\n  \"Type\" : \"Notification\",\n  \"MessageId\" : \"bf5ff648-5111-5dbe-ad4b-a82514ed6a35\",\n  \"TopicArn\" : \"arn:aws:sns:us-east-1:683517028648:sqs-sns-unwrap-Topic-0Wj2eIrU5hrM\",\n  \"Message\" : \"from sns\",\n  \"Timestamp\" : \"2024-03-14T18:36:44.233Z\",\n  \"SignatureVersion\" : \"1\",\n  \"Signature\" : \"Ne7jvjmincHd06Y19dZss3Xk003RlAm/srm2dt5nLDgwrY0dI56RkH/Dbva9w8xy63EUHyUVfHCYvrXLh/HpsW5nXU9YetK7G5QpfxBeTPnNioPdJi2U3PDA+jJXs0DK4ffonwEMLjbmIETAiWdrN5ollBpL5zh2ZjurMh7TnUGH6/KxsFcWNHTPrGN/v9HSRoFtQdtl9i/zFmBVaXC4dvaZU0cy/gYK5uIIf+YJ+OJoXd7fCxZLVPIwnK148Ws3b/i85UyP0tVguscoknf37bTPwdQuloPOKQHtPZDxUdLjS+uj27LRwiT+1CvGqdgpJ8XV/8tWqujR3FDI3ZL6EQ==\",\n  \"SigningCertURL\" : \"https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem\",\n  \"UnsubscribeURL\" : \"https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:683517028648:sqs-sns-unwrap-Topic-0Wj2eIrU5hrM:42e6130c-54b0-4cec-a8c0-7d0cc356ea4e\"\n}",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1710441404272",
        "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
        "ApproximateFirstReceiveTimestamp": "1710441404278"
      },
      "messageAttributes": {},
      "md5OfBody": "fb98571efddcc86ff1767f300518f455",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:683517028648:sqs-sns-unwrap-Queue-F562gfvOiNHt",
      "awsRegion": "us-east-1"
    }
  ]
}


# raw_sns -> sqs -> lambda == sqs(raw_sns)
sqs_rawsns_event = {
  "Records": [
    {
      "messageId": "c2f72267-c1b4-432b-b35e-c27a337798d1",
      "receiptHandle": "AQEB2+Do4Yh7HS58NLu1KQZMi69dTVWByZC140b3YS5Dl5hMjU5RlIkmHaxoyDArEzo1ZtJfOljU2aEZAf0nVkp6zosnWP3gqpueoM5RYeXTaYzQSAidCjMySSNWKnA4xzoI3uDhwcmguXAKxyTcgXd9pdiCQ8bXACZmqdzgL0RoKmgA9bIf0X3YYGlQ3X/ApEgxAyiD+ok1quVOj8jdqXfcJ1fbabwihtLTn6fxkVW6Z25gfrYTj8Ix90LdtWcmXjt/q9aJ30e3RdeVBhtB40C1glVm9R9cBvQQaog6z8yC+6H/eKKym25BRr8MJt9kx/e+8aMNKQowcnI/KYXwqSGRbTeml+5XXT5ANDr9qy1c4XEnl8k9vvozzlyYCjlLKOt+shhRfHULo4fzVunsO7GXpa7BW9ZtFJU31nlNCfLNYfk=",
      "body": "this is a raw message",
      "attributes": {
        "ApproximateReceiveCount": "1",
        "SentTimestamp": "1710887794983",
        "SenderId": "AIDAIT2UOQQY3AUEKVGXU",
        "ApproximateFirstReceiveTimestamp": "1710887794991"
      },
      "messageAttributes": {},
      "md5OfBody": "dbfce666a3bf5ced0e8687d4c0039a74",
      "eventSource": "aws:sqs",
      "eventSourceARN": "arn:aws:sqs:us-east-1:683517028648:sqs-sns-unwrap-Queue-F562gfvOiNHt",
      "awsRegion": "us-east-1"
    }
  ]
}


# generated from invoking lambda with s3 -> sns -> lambda == sns(s3).
sns_s3_event = {
  "Records": [
    {
      "EventSource": "aws:sns",
      "EventVersion": "1.0",
      "EventSubscriptionArn": "arn:aws:sns:us-east-1:683517028648:s3-sns-unwrap-Topic-7Xaj1echf9dg:6b8dee7d-026a-4c2e-b3f2-a2f189e4a402",
      "Sns": {
        "Type": "Notification",
        "MessageId": "2d44624b-23f8-5e80-99d9-3c265035c5ae",
        "TopicArn": "arn:aws:sns:us-east-1:683517028648:s3-sns-unwrap-Topic-7Xaj1echf9dg",
        "Subject": "Amazon S3 Notification",
        "Message": "{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"us-east-1\",\"eventTime\":\"2024-03-14T21:52:13.311Z\",\"eventName\":\"ObjectCreated:Put\",\"userIdentity\":{\"principalId\":\"AWS:AROAZ6JGKFEUJYDMQOGIU:seshub-Isengard\"},\"requestParameters\":{\"sourceIPAddress\":\"15.248.6.24\"},\"responseElements\":{\"x-amz-request-id\":\"53YYXE4TACR6K89G\",\"x-amz-id-2\":\"9jBkdIPJOx97diPIdSkVi3kpoo9d6qk1W11iL4ZIQMJgQm9rbdsywKE3NgkKpDm43RU7sASksILzYlM8rhX/bGncoqXwUQ5L\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"MWQyMzI0ZDgtNzE5Yi00NmNiLTlmNDYtNDI3MmM4Mjk0MTc2\",\"bucket\":{\"name\":\"s3-sns-unwrap-bucket-683517028648\",\"ownerIdentity\":{\"principalId\":\"A2RRIR5BTZTTF6\"},\"arn\":\"arn:aws:s3:::s3-sns-unwrap-bucket-683517028648\"},\"object\":{\"key\":\"samconfig.toml\",\"size\":221,\"eTag\":\"551277913a5ad93e0db069e673f23376\",\"sequencer\":\"0065F3718D39E6D6DC\"}}}]}",
        "Timestamp": "2024-03-14T21:52:13.905Z",
        "SignatureVersion": "1",
        "Signature": "IJqlNH8ddOX4V10m6IY+3gOK6/+PxxiGLs4PxHiGDcQ58mcCr4+vXCHuJ7jxOvCBHCYev1wF0PCwBhDpwBfstV8vAGEsX7GhJuAZ5jf0uOUMukZvIquy1LQBTdHg0TNq9N83sG0wz2QMp8QLLlkDJMF8nS00EjeDuFwpJxZnRadWcjz4AWXO6JITohyYnFVkDqsK5pOFd3Y1KADjfpRFH2lrljJm3CnA/x6PYVduP5PK83JnDs7LmEnK3cqE7IJhdwW9e824KXmjFBujoiNU9bUnoLiqFMg+UfZfMMJGjtCHIV0ZmnMix7nKZUGDNQe7TKOoDcXLxuAxa6TQNWfKSw==",
        "SigningCertUrl": "https://sns.us-east-1.amazonaws.com/SimpleNotificationService-60eadc530605d63b8e62a523676ef735.pem",
        "UnsubscribeUrl": "https://sns.us-east-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:us-east-1:683517028648:s3-sns-unwrap-Topic-7Xaj1echf9dg:6b8dee7d-026a-4c2e-b3f2-a2f189e4a402",
        "MessageAttributes": {}
      }
    }
  ]
}

