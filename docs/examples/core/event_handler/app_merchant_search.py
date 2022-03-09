from aws_lambda_powertools.event_handler import AppSyncResolver
from aws_lambda_powertools.utilities.data_classes.appsync import scalar_types_utils

app = AppSyncResolver()


@app.resolver(type_name="Query", field_name="findMerchant")
def find_merchant(search: str):
    return [
        {
            "id": scalar_types_utils.make_id(),
            "name": "Brewer Brewing",
            "description": "Mike Brewer's IPA brewing place",
        },
        {"id": scalar_types_utils.make_id(), "name": "Serverlessa's Bakery", "description": "Lessa's sourdough place"},
    ]
