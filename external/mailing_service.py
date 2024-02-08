import requests

from api.logs import logger
from config.settings import MAILING_SERVICE_JWT_TOKEN, MAILING_SERVICE_URL


class MailingServiceClient:
    def __init__(self):
        self.base_url = MAILING_SERVICE_URL
        self.jwt_token = MAILING_SERVICE_JWT_TOKEN

    def send_message(self, text: str, phone_number: str, message_id: int) -> dict:
        """
        Sends a message using the Mailing Service API.

        Args:
            text (str): The text of the message.
            phone_number (str): The phone number to send the message to.
            message_id (int): The ID of the message.

        Returns:
            dict: The JSON response from the server.
        """

        url = f"{self.base_url}/send/{message_id}"
        headers = {"Authorization": f"Bearer {self.jwt_token}"}
        json = {
            "id": message_id,
            "phone": phone_number,
            "text": text,
        }

        logger.info(f"Message #{message_id}: Request url: {url}. Request json: {json}")

        response = requests.post(url, headers=headers, json=json)
        response.raise_for_status()
        response_json = response.json()

        logger.info(f"Message #{message_id}: Response: {response_json}")

        is_ok = response.ok and response_json.get("message") == "OK"
        if not is_ok:
            logger.error(f"Message #{message_id}: Failed to send.")
            raise Exception()

        return response
