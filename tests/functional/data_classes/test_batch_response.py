from aws_lambda_powertools.utilities.data_classes.batch_response import BatchResponse


def test_no_elements():
    assert BatchResponse().asdict() == {"batchItemFailures": []}
    assert BatchResponse(None).asdict() == {"batchItemFailures": []}


def test_with_elements():
    assert BatchResponse(["item1", "item2"]).asdict() == {
        "batchItemFailures": [{"itemIdentifier": "item1"}, {"itemIdentifier": "item2"}]
    }


def test_add_item():
    response = BatchResponse()
    response.add_item("item1")
    assert response.asdict() == {"batchItemFailures": [{"itemIdentifier": "item1"}]}
