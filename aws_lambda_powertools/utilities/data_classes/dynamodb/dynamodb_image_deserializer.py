from typing import Dict, List, Optional, Union

from aws_lambda_powertools.utilities.data_classes.dynamo_db_stream_event import (
    AttributeValue,
)


class DynamoDBImageDeserializer:
    """
    Deserializes DynamoDB StreamRecord's old_image and new_image properties of type Dict[str, AttributeValue]
    to Dict with Python types.

    Example
    -------

    from aws_lambda_powertools.utilities.typing import LambdaContext
    from aws_lambda_powertools.utilities.data_classes import event_source, DynamoDBStreamEvent
    from aws_lambda_powertools.utilities.data_classes.dynamodb import DynamoDBImageDeserializer

    deserializer = DynamoDBImageDeserializer()

    @event_source(data_class=DynamoDBStreamEvent)
    def handler(event: DynamoDBStreamEvent, context: LambdaContext):
        for record in event.records:
            new_image = deserializer.deserialize(record.dynamodb.new_image)
            old_image = deserializer.deserialize(record.dynamodb.old_image)
    """

    def deserialize(self, image: Dict[str, AttributeValue]):
        """
        Deserializes image to Dict with Python types.
        AttributeValue fields are deserialized according to the following table:

            DynamoDB                                Python
            --------                                ------
            {'NULL': True}                          None
            {'BOOL': True/False}                    True/False
            {'N': string}                           string
            {'S': string}                           string
            {'B': bytes}                            bytes
            {'NS': [string]}                        set([string])
            {'SS': [string]}                        set([string])
            {'BS': [bytes]}                         set([bytes])
            {'L': list}                             list
            {'M': dict}                             dict

        Please bear in mind that numbers are represented as strings.

        Parameters
        ----------
        image: Dict[str, AttributeValue]
            Dictionary representing a StreamRecord's image property

        Returns
        -------
        Dict
            Dictionary with Python types

        Raises
        ------
        TypeError
            Raised if an unknown DynamoDB attribute type is encountered
        """
        return {k: self._deserialize_attr_value(v) for k, v in image.items()}

    def _deserialize_attr_value(
        self, attr_value: AttributeValue
    ) -> Union[Optional[bool], Optional[str], Optional[List], Optional[Dict]]:
        try:
            dynamodb_type = attr_value.dynamodb_type.lower()
            deserializer = getattr(self, "_deserialize_%s" % dynamodb_type)
        except AttributeError:
            raise TypeError("DynamoDB type %s is not supported" % dynamodb_type)
        return deserializer(attr_value)

    def _deserialize_null(self, attr_value: AttributeValue):
        return attr_value.null_value

    def _deserialize_bool(self, attr_value: AttributeValue):
        return attr_value.bool_value

    def _deserialize_n(self, attr_value: AttributeValue):
        return attr_value.n_value

    def _deserialize_s(self, attr_value: AttributeValue):
        return attr_value.s_value

    def _deserialize_b(self, attr_value: AttributeValue):
        return attr_value.b_value

    def _deserialize_ns(self, attr_value: AttributeValue):
        return set(attr_value.ns_value)

    def _deserialize_ss(self, attr_value: AttributeValue):
        print(attr_value)
        return set(attr_value.ss_value)

    def _deserialize_bs(self, attr_value: AttributeValue):
        return set(attr_value.bs_value)

    def _deserialize_l(self, attr_value: AttributeValue):
        return [self._deserialize_attr_value(v) for v in attr_value.list_value]

    def _deserialize_m(self, attr_value: AttributeValue):
        return {k: self._deserialize_attr_value(v) for k, v in attr_value.map_value.items()}
