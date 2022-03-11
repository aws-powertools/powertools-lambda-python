from aws_lambda_powertools import Logger

logger = Logger(service="payment")


def handler(event, context):
    logger.append_keys(payment_id="123456789")

    try:
        booking_id = book_flight()
        logger.info("Flight booked successfully", extra={"booking_id": booking_id})
    except BookingReservationError:
        ...

    logger.info("goodbye")
