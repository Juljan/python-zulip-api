from zulip_bots.test_lib import BotTestCase

class TestHelpBot(BotTestCase):
    bot_name = "fedorest"  # type: str

    def test_bot(self) -> None:
        dialog = [
            ('', 'beep boop'),
            ('help', 'beep boop'),
            ('foo', 'beep boop'),
        ]

        bot_response = "Test"

        self.assert_bot_response(
            message = {'content': 'Hello'},
            response = {'content': bot_response},
            expected_method='send_reply'
        )
